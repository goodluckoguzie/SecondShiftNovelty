from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from .briefs import generate_brief, generate_handover
from .config import DATA_DIR, DISCLAIMER, WHISPER_MODEL
from .db import engine, get_session, init_db, resolve_person
from .extractor import heuristic_extract, ollama_extract, parse_event_time
from .models import CareEvent, MedicationSchedule, PatternFlag, PersonProfile, Shift, User
from .ollama_client import ollama_available
from .patterns import chart_payload, recompute_flags, similar_events
from .safety import is_emergency, strip_advice
from .seed import seed_if_empty

app = FastAPI(title="Second Shift")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class LogRequest(BaseModel):
    transcript: str
    urgent: bool = False
    use_heuristic: bool = False
    person_id: Optional[int] = None
    shift_id: Optional[int] = None
    logger_id: Optional[int] = None


class HandoverRequest(BaseModel):
    name: str = "next worker"
    window: str = "72h"
    person_id: Optional[int] = None
    shift_id: Optional[int] = None


class ShiftStartRequest(BaseModel):
    user_id: Optional[int] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None


def _role(x_demo_role: Optional[str] = Header(default=None)) -> str:
    return (x_demo_role or "support_worker").strip().lower()


def _require_writer(role: str) -> None:
    if role in {"clinician", "nurse", "doctor"}:
        raise HTTPException(403, "View only. This role cannot log.")


def _pdf_path(kind: str, person_id: int):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / f"{kind}_{person_id}.pdf"


def _event_out(row: CareEvent) -> dict:
    return {
        "id": row.id,
        "person_id": row.person_id,
        "logged_at": row.logged_at.isoformat(),
        "event_time": row.event_time.isoformat(),
        "type": row.type,
        "subtype": row.subtype,
        "detail": row.detail,
        "raw_transcript": row.raw_transcript,
        "confidence": row.confidence,
        "urgent": row.urgent,
    }


def _flag_out(session: Session, row: PatternFlag) -> dict:
    ids = [int(x) for x in (row.evidence_event_ids or "").split(",") if x.strip().isdigit()]
    evidence = []
    for event_id in ids:
        event = session.get(CareEvent, event_id)
        if event:
            evidence.append(_event_out(event))
    return {
        "id": row.id,
        "person_id": row.person_id,
        "kind": row.kind,
        "subtype": row.subtype,
        "message": row.message,
        "related_date": row.related_date.isoformat() if row.related_date else None,
        "evidence_event_ids": ids,
        "evidence": evidence,
    }


@app.on_event("startup")
def startup() -> None:
    init_db()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with Session(engine) as session:
        seed_if_empty(session)
        recompute_flags(session)


@app.get("/health")
def health():
    return {
        "ok": True,
        "disclaimer": DISCLAIMER,
        "ollama": ollama_available(),
        "brand": "Speak. Cited page. No provider login for the GP.",
    }


@app.get("/people")
def list_people(session: Session = Depends(get_session)):
    rows = session.exec(select(PersonProfile)).all()
    return [{"id": p.id, "name": p.name, "age": p.age, "conditions": p.conditions} for p in rows]


@app.get("/users")
def list_users(session: Session = Depends(get_session)):
    rows = session.exec(select(User)).all()
    return [{"id": u.id, "display_name": u.display_name, "role": u.role} for u in rows]


@app.get("/profile")
def profile(person_id: Optional[int] = None, session: Session = Depends(get_session)):
    person = resolve_person(session, person_id)
    meds = session.exec(select(MedicationSchedule).where(MedicationSchedule.person_id == person.id)).all()
    return {
        "id": person.id,
        "name": person.name,
        "age": person.age,
        "conditions": person.conditions,
        "allergies": person.allergies,
        "disclaimer": DISCLAIMER,
        "brand": "They keep care inside the provider app. We turn a spoken sentence into a cited page.",
        "medications": [
            {
                "name": m.name,
                "dose": m.dose,
                "scheduled_times": m.scheduled_times,
                "last_changed_at": m.last_changed_at.isoformat() if m.last_changed_at else None,
            }
            for m in meds
        ],
    }


@app.get("/events")
def list_events(person_id: Optional[int] = None, session: Session = Depends(get_session)):
    person = resolve_person(session, person_id)
    rows = session.exec(
        select(CareEvent).where(CareEvent.person_id == person.id).order_by(CareEvent.event_time.desc())
    ).all()
    return [_event_out(row) for row in rows]


@app.get("/flags")
def list_flags(person_id: Optional[int] = None, session: Session = Depends(get_session)):
    person = resolve_person(session, person_id)
    rows = session.exec(select(PatternFlag).where(PatternFlag.person_id == person.id)).all()
    return [_flag_out(session, r) for r in rows]


@app.get("/patterns")
def patterns(person_id: Optional[int] = None, session: Session = Depends(get_session)):
    person = resolve_person(session, person_id)
    return chart_payload(session, person.id)


@app.post("/shifts")
def start_shift(body: ShiftStartRequest, session: Session = Depends(get_session), role: str = Depends(_role)):
    _require_writer(role)
    user = None
    if body.user_id:
        user = session.get(User, body.user_id)
    if not user:
        user = session.exec(select(User).where(User.role == "support_worker")).first()
    if not user:
        raise HTTPException(400, "No user")
    shift = Shift(
        user_id=user.id,
        started_at=body.started_at or datetime.utcnow(),
        ended_at=body.ended_at,
    )
    session.add(shift)
    session.commit()
    session.refresh(shift)
    return {
        "id": shift.id,
        "user_id": shift.user_id,
        "started_at": shift.started_at.isoformat(),
        "ended_at": shift.ended_at.isoformat() if shift.ended_at else None,
    }


@app.post("/shifts/{shift_id}/end")
def end_shift(shift_id: int, session: Session = Depends(get_session), role: str = Depends(_role)):
    _require_writer(role)
    shift = session.get(Shift, shift_id)
    if not shift:
        raise HTTPException(404, "No shift")
    shift.ended_at = datetime.utcnow()
    session.add(shift)
    session.commit()
    session.refresh(shift)
    return {
        "id": shift.id,
        "started_at": shift.started_at.isoformat(),
        "ended_at": shift.ended_at.isoformat() if shift.ended_at else None,
    }


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = DATA_DIR / "tmp"
    tmp.mkdir(exist_ok=True)
    dest = tmp / (file.filename or "clip.webm")
    dest.write_bytes(await file.read())
    try:
        from .whisper_stt import transcribe_file

        text = transcribe_file(dest, WHISPER_MODEL)
    except Exception as exc:
        dest.unlink(missing_ok=True)
        raise HTTPException(503, f"Whisper unavailable: {exc}") from exc
    dest.unlink(missing_ok=True)
    return {"transcript": text}


def _store_log(
    session: Session,
    person: PersonProfile,
    transcript: str,
    urgent: bool,
    use_heuristic: bool,
    shift_id: Optional[int],
    logger_id: Optional[int] = None,
) -> dict:
    if is_emergency(transcript):
        return {
            "emergency": True,
            "screen": "Call 999 now. Second Shift will not process this with the AI.",
            "events": [],
            "flags": [],
            "similar": [],
            "confirmation": None,
        }

    now = datetime.utcnow()
    extracted = heuristic_extract(transcript, now) if use_heuristic else ollama_extract(transcript, now)
    stored = []
    for item in extracted.get("events") or []:
        event = CareEvent(
            person_id=person.id,
            logger_id=logger_id,
            shift_id=shift_id,
            logged_at=now,
            event_time=parse_event_time(item.get("event_time"), now),
            type=item.get("type") or "note",
            subtype=item.get("subtype") or "note",
            detail=item.get("detail") or "",
            raw_transcript=transcript,
            confidence=float(item.get("confidence") or 0.5),
            urgent=urgent,
        )
        session.add(event)
        stored.append(event)
    session.commit()
    for event in stored:
        session.refresh(event)
    flags = recompute_flags(session, person.id)
    subtypes = list({e.subtype for e in stored if e.subtype not in {"note"}})
    similar = similar_events(session, person.id, subtypes or ["vomiting", "confusion"])
    similar = [e for e in similar if e.id not in {s.id for s in stored}]
    confirmation = strip_advice(extracted.get("confirmation") or "Logged.")
    flag_note = next((f.message for f in flags if f.subtype in {"confusion", "vomiting"}), None)
    if flag_note:
        confirmation = f"{confirmation} {flag_note}".strip()
    return {
        "emergency": False,
        "events": [_event_out(e) for e in stored],
        "flags": [_flag_out(session, f) for f in flags],
        "similar": [_event_out(e) for e in similar[:6]],
        "confirmation": confirmation,
        "clarifying_question": extracted.get("clarifying_question"),
        "nhs111": "If you are worried and it is not an emergency, call NHS 111.",
    }


@app.post("/log")
def log_event(
    body: LogRequest,
    session: Session = Depends(get_session),
    role: str = Depends(_role),
):
    _require_writer(role)
    transcript = body.transcript.strip()
    if not transcript:
        raise HTTPException(400, "Empty transcript")
    person = resolve_person(session, body.person_id)
    return _store_log(
        session, person, transcript, body.urgent, body.use_heuristic, body.shift_id, body.logger_id
    )


@app.post("/log/audio")
async def log_audio(
    file: UploadFile = File(...),
    person_id: Optional[int] = None,
    urgent: bool = False,
    use_heuristic: bool = False,
    shift_id: Optional[int] = None,
    logger_id: Optional[int] = None,
    session: Session = Depends(get_session),
    role: str = Depends(_role),
):
    _require_writer(role)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = DATA_DIR / "tmp"
    tmp.mkdir(exist_ok=True)
    dest = tmp / (file.filename or "clip.webm")
    dest.write_bytes(await file.read())
    try:
        from .whisper_stt import transcribe_file

        text = transcribe_file(dest, WHISPER_MODEL)
    except Exception as exc:
        dest.unlink(missing_ok=True)
        raise HTTPException(503, f"Whisper unavailable: {exc}") from exc
    dest.unlink(missing_ok=True)
    if not text or not text.strip():
        raise HTTPException(400, "Heard nothing")
    person = resolve_person(session, person_id)
    result = _store_log(session, person, text.strip(), urgent, use_heuristic, shift_id, logger_id)
    result["transcript"] = text.strip()
    return result


class PersonRef(BaseModel):
    person_id: Optional[int] = None


@app.post("/briefs")
def create_brief(
    body: Optional[PersonRef] = None,
    person_id: Optional[int] = None,
    session: Session = Depends(get_session),
):
    person = resolve_person(session, (body.person_id if body else None) or person_id)
    path = str(_pdf_path("brief", person.id))
    events = session.exec(select(CareEvent).where(CareEvent.person_id == person.id)).all()
    brief = generate_brief(session, person, path, urgent=any(e.urgent for e in events))
    return {"id": brief.id, "markdown": brief.markdown, "pdf_path": brief.pdf_path, "person_id": person.id}


@app.get("/briefs/latest.pdf")
def latest_brief_pdf(person_id: Optional[int] = None, session: Session = Depends(get_session)):
    person = resolve_person(session, person_id)
    path = _pdf_path("brief", person.id)
    if not path.exists():
        raise HTTPException(404, "No brief yet")
    return FileResponse(path, media_type="application/pdf", filename=f"{person.name.lower()}-gp-brief.pdf")


@app.post("/handover")
def create_handover(
    body: Optional[HandoverRequest] = None,
    session: Session = Depends(get_session),
):
    payload = body or HandoverRequest()
    person = resolve_person(session, payload.person_id)
    shift = session.get(Shift, payload.shift_id) if payload.shift_id else None
    path = str(_pdf_path("handover", person.id))
    brief = generate_handover(
        session,
        person,
        path,
        name=payload.name,
        window=payload.window,
        shift=shift,
    )
    return {"id": brief.id, "markdown": brief.markdown, "pdf_path": brief.pdf_path, "person_id": person.id}


@app.get("/handover/latest.pdf")
def latest_handover_pdf(person_id: Optional[int] = None, session: Session = Depends(get_session)):
    person = resolve_person(session, person_id)
    path = _pdf_path("handover", person.id)
    if not path.exists():
        raise HTTPException(404, "No handover yet")
    return FileResponse(path, media_type="application/pdf", filename=f"{person.name.lower()}-handover.pdf")
