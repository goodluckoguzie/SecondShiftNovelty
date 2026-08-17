import threading
from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from .board import build_board
from .briefs import generate_brief, generate_handover
from .config import ADMIN_PASSWORD, DATA_DIR, DISCLAIMER, FAMILY_PASSWORD, STAFF_PASSWORD, WHISPER_MODEL
from .db import engine, get_session, init_db, resolve_person
from .extractor import heuristic_extract, ollama_extract, parse_event_time, split_corridor
from .slots import pack_slots, unpack_slots
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
    source: Optional[str] = None


class CorridorRequest(BaseModel):
    transcript: str
    shift_id: Optional[int] = None
    logger_id: Optional[int] = None
    urgent: bool = False
    use_heuristic: bool = False


class EventPatch(BaseModel):
    type: Optional[str] = None
    subtype: Optional[str] = None


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
    if role not in {"support_worker", "family"}:
        raise HTTPException(403, "View only. This role cannot log.")


def _require_admin(role: str) -> None:
    if role != "admin":
        raise HTTPException(403, "Admin only.")


def _pdf_path(kind: str, person_id: int):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / f"{kind}_{person_id}.pdf"


def _logger_label(session: Session, row: CareEvent) -> Optional[str]:
    if not row.logger_id:
        return "family" if (row.source or "staff") == "from_home" else None
    user = session.get(User, row.logger_id)
    if not user:
        return None
    if (row.source or "staff") == "from_home" or user.role == "family":
        return f"{user.display_name} (home)"
    return user.display_name


def _event_out(row: CareEvent, session: Optional[Session] = None) -> dict:
    logger_name = None
    logger_label = None
    if session is not None:
        logger_label = _logger_label(session, row)
        if row.logger_id:
            user = session.get(User, row.logger_id)
            logger_name = user.display_name if user else None
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
        "source": row.source or "staff",
        "logger_id": row.logger_id,
        "logger_name": logger_name,
        "logger_label": logger_label,
        "slots": unpack_slots(row.slots),
    }


def _resolve_family(session: Session, logger_id: Optional[int]) -> Optional[User]:
    if logger_id:
        user = session.get(User, logger_id)
        if user and user.role == "family":
            return user
    return session.exec(select(User).where(User.role == "family")).first()


def _flag_out(session: Session, row: PatternFlag) -> dict:
    ids = [int(x) for x in (row.evidence_event_ids or "").split(",") if x.strip().isdigit()]
    evidence = []
    for event_id in ids:
        event = session.get(CareEvent, event_id)
        if event:
            evidence.append(_event_out(event, session))
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


def _warm_whisper() -> None:
    try:
        from .whisper_stt import warmup

        warmup(WHISPER_MODEL)
    except Exception:
        pass


@app.on_event("startup")
def startup() -> None:
    init_db()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with Session(engine) as session:
        seed_if_empty(session)
        recompute_flags(session)
    threading.Thread(target=_warm_whisper, daemon=True).start()


@app.get("/health")
def health():
    return {
        "ok": True,
        "disclaimer": DISCLAIMER,
        "ollama": ollama_available(),
        "brand": "Speak. Cited page. No provider login for the GP.",
    }


@app.get("/people")
def list_people(session: Session = Depends(get_session), role: str = Depends(_role)):
    rows = session.exec(select(PersonProfile)).all()
    if role == "family":
        family = _resolve_family(session, None)
        allowed = {family.family_person_id} if family and family.family_person_id else set()
        rows = [p for p in rows if p.id in allowed]
    return [
        {
            "id": p.id,
            "name": p.name,
            "age": p.age,
            "conditions": p.conditions,
            "usual": p.usual or "",
            "risks": p.risks or "",
            "mobility": p.mobility or "",
        }
        for p in rows
    ]


@app.get("/users")
def list_users(session: Session = Depends(get_session)):
    rows = session.exec(select(User)).all()
    return [
        {
            "id": u.id,
            "display_name": u.display_name,
            "role": u.role,
            "family_person_id": u.family_person_id,
            "assigned_person_id": u.assigned_person_id,
        }
        for u in rows
    ]


@app.get("/board")
def wing_board(
    since: Optional[str] = None,
    session: Session = Depends(get_session),
    role: str = Depends(_role),
):
    if role == "family":
        raise HTTPException(403, "Wing board is for staff.")
    start = None
    if since:
        try:
            start = datetime.fromisoformat(since.replace("Z", ""))
        except ValueError:
            raise HTTPException(400, "Bad since") from None
    return build_board(session, since=start)


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
        "usual": person.usual or "",
        "risks": person.risks or "",
        "mobility": person.mobility or "",
        "hospital_return_at": person.hospital_return_at.isoformat() if person.hospital_return_at else None,
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
    return [_event_out(row, session) for row in rows]


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
    in_shift = [
        e
        for e in session.exec(select(CareEvent)).all()
        if e.shift_id == shift.id
        or (e.event_time and shift.started_at <= e.event_time <= shift.ended_at)
    ]
    for pid in {e.person_id for e in in_shift if e.person_id}:
        person = session.get(PersonProfile, pid)
        if not person:
            continue
        generate_handover(
            session,
            person,
            str(_pdf_path("handover", person.id)),
            name="next worker",
            window="shift",
            shift=shift,
        )
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
    source: str = "staff",
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
            source=source or "staff",
            slots=pack_slots(item),
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
    flag_note = next(
        (f.message for f in flags if f.subtype in {"confusion", "vomiting", "not_himself", "hospital_return"}),
        None,
    )
    if flag_note:
        confirmation = f"{confirmation} {flag_note}".strip()
    elif person.usual and any(e.type == "mood" or e.subtype in {"mood_low", "not_himself"} for e in stored):
        confirmation = f"{confirmation} {person.name} usually {person.usual.rstrip('.')}."
    return {
        "emergency": False,
        "events": [_event_out(e, session) for e in stored],
        "flags": [_flag_out(session, f) for f in flags],
        "similar": [_event_out(e, session) for e in similar[:6]],
        "confirmation": confirmation,
        "clarifying_question": extracted.get("clarifying_question"),
        "guess": extracted.get("guess"),
        "transcript": transcript,
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
    if role == "family":
        family = _resolve_family(session, body.logger_id)
        if not family or not family.family_person_id:
            raise HTTPException(403, "No family person linked.")
        person = resolve_person(session, body.person_id)
        if person.id != family.family_person_id:
            raise HTTPException(403, "You can only log for your person.")
        return _store_log(
            session,
            person,
            transcript,
            body.urgent,
            body.use_heuristic,
            body.shift_id,
            family.id,
            "from_home",
        )
    if (body.source or "").strip() == "from_home":
        raise HTTPException(400, "Staff cannot log as family.")
    person = resolve_person(session, body.person_id)
    return _store_log(
        session,
        person,
        transcript,
        body.urgent,
        body.use_heuristic,
        body.shift_id,
        body.logger_id,
        "staff",
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
        raise HTTPException(400, "Heard nothing. Speak again, then press Stop.")
    if role == "family":
        family = _resolve_family(session, logger_id)
        if not family or not family.family_person_id:
            raise HTTPException(403, "No family person linked.")
        person = resolve_person(session, person_id)
        if person.id != family.family_person_id:
            raise HTTPException(403, "You can only log for your person.")
        result = _store_log(
            session, person, text.strip(), urgent, use_heuristic, shift_id, family.id, "from_home"
        )
        result["transcript"] = text.strip()
        return result
    person = resolve_person(session, person_id)
    result = _store_log(session, person, text.strip(), urgent, use_heuristic, shift_id, logger_id, "staff")
    result["transcript"] = text.strip()
    return result


@app.post("/log/corridor")
def log_corridor(
    body: CorridorRequest,
    session: Session = Depends(get_session),
    role: str = Depends(_role),
):
    _require_writer(role)
    if role == "family":
        raise HTTPException(403, "Corridor dump is for staff.")
    transcript = body.transcript.strip()
    if not transcript:
        raise HTTPException(400, "Empty transcript")
    people = session.exec(select(PersonProfile)).all()
    slices, unmatched = split_corridor(transcript, [p.name for p in people])
    if not slices:
        raise HTTPException(400, "No names heard. Say the name, then what happened.")
    by_name = {p.name: p for p in people}
    results = []
    for name, chunk in slices:
        person = by_name[name]
        result = _store_log(
            session,
            person,
            chunk,
            body.urgent,
            body.use_heuristic,
            body.shift_id,
            body.logger_id,
            "staff",
        )
        result["person_id"] = person.id
        result["person_name"] = person.name
        result["transcript"] = chunk
        results.append(result)
    return {"ok": True, "slices": results, "warning": unmatched}


@app.patch("/events/{event_id}")
def patch_event(
    event_id: int,
    body: EventPatch,
    session: Session = Depends(get_session),
    role: str = Depends(_role),
):
    _require_writer(role)
    event = session.get(CareEvent, event_id)
    if not event:
        raise HTTPException(404, "No event")
    if role == "family":
        family = _resolve_family(session, None)
        if not family or event.person_id != family.family_person_id:
            raise HTTPException(403, "You can only change your person's logs.")
        if (event.source or "staff") != "from_home":
            raise HTTPException(403, "You can only change notes from home.")
    defaults = {
        "mood": "mood_low",
        "sleep": "awake_night",
        "meal": "note",
        "symptom": "note",
        "medication": "note",
        "incident": "note",
        "preference": "about_me",
        "note": "note",
    }
    if body.type:
        event.type = body.type
        if not body.subtype:
            event.subtype = defaults.get(body.type, event.subtype)
    if body.subtype:
        event.subtype = body.subtype
    session.add(event)
    session.commit()
    session.refresh(event)
    recompute_flags(session, event.person_id)
    return _event_out(event, session)


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


class AdminLogin(BaseModel):
    password: str


class StaffCreate(BaseModel):
    display_name: str
    assigned_person_id: Optional[int] = None


class StaffAssign(BaseModel):
    assigned_person_id: Optional[int] = None


class PersonCreate(BaseModel):
    name: str
    age: int = 80
    conditions: str = "dementia"
    allergies: str = "none known"
    relationship: str = "resident"
    usual: str = ""
    risks: str = ""
    mobility: str = ""


def _user_out(u: User) -> dict:
    return {
        "id": u.id,
        "display_name": u.display_name,
        "role": u.role,
        "family_person_id": u.family_person_id,
        "assigned_person_id": u.assigned_person_id,
    }


@app.post("/admin/login")
def admin_login(body: AdminLogin):
    if (body.password or "").strip() != ADMIN_PASSWORD:
        raise HTTPException(403, "Wrong password.")
    return {"ok": True, "role": "admin"}


class StaffLogin(BaseModel):
    user_id: int
    password: str


@app.post("/staff/login")
def staff_login(body: StaffLogin, session: Session = Depends(get_session)):
    if (body.password or "").strip() != STAFF_PASSWORD:
        raise HTTPException(403, "Wrong password.")
    user = session.get(User, body.user_id)
    if not user or user.role != "support_worker":
        raise HTTPException(404, "No support worker")
    return _user_out(user)


class FamilyLogin(BaseModel):
    person_id: int
    password: str


@app.post("/family/login")
def family_login(body: FamilyLogin, session: Session = Depends(get_session)):
    if (body.password or "").strip() != FAMILY_PASSWORD:
        raise HTTPException(403, "Wrong password.")
    person = session.get(PersonProfile, body.person_id)
    if not person:
        raise HTTPException(404, "No person")
    user = session.exec(
        select(User).where(User.role == "family", User.family_person_id == person.id)
    ).first()
    if not user:
        raise HTTPException(404, "No family account for this person.")
    return _user_out(user)


@app.post("/admin/staff")
def admin_add_staff(body: StaffCreate, session: Session = Depends(get_session), role: str = Depends(_role)):
    _require_admin(role)
    name = body.display_name.strip()
    if not name:
        raise HTTPException(400, "Name is required.")
    existing = session.exec(select(User).where(User.display_name == name)).first()
    if existing:
        raise HTTPException(400, "That name is already on the list.")
    assigned = None
    if body.assigned_person_id:
        assigned = session.get(PersonProfile, body.assigned_person_id)
        if not assigned:
            raise HTTPException(404, "No person")
    user = User(
        display_name=name,
        role="support_worker",
        assigned_person_id=assigned.id if assigned else None,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return _user_out(user)


@app.patch("/admin/staff/{user_id}")
def admin_assign_staff(
    user_id: int,
    body: StaffAssign,
    session: Session = Depends(get_session),
    role: str = Depends(_role),
):
    _require_admin(role)
    user = session.get(User, user_id)
    if not user or user.role != "support_worker":
        raise HTTPException(404, "No support worker")
    if body.assigned_person_id:
        person = session.get(PersonProfile, body.assigned_person_id)
        if not person:
            raise HTTPException(404, "No person")
        user.assigned_person_id = person.id
    else:
        user.assigned_person_id = None
    session.add(user)
    session.commit()
    session.refresh(user)
    return _user_out(user)


@app.post("/admin/people")
def admin_add_person(body: PersonCreate, session: Session = Depends(get_session), role: str = Depends(_role)):
    _require_admin(role)
    name = body.name.strip()
    if not name:
        raise HTTPException(400, "Name is required.")
    existing = session.exec(select(PersonProfile).where(PersonProfile.name == name)).first()
    if existing:
        raise HTTPException(400, "That person is already on the wing.")
    person = PersonProfile(
        name=name,
        age=body.age,
        conditions=body.conditions.strip() or "dementia",
        allergies=body.allergies.strip() or "none known",
        relationship=body.relationship.strip() or "resident",
        usual=body.usual.strip(),
        risks=body.risks.strip(),
        mobility=body.mobility.strip(),
    )
    session.add(person)
    session.commit()
    session.refresh(person)
    return {
        "id": person.id,
        "name": person.name,
        "age": person.age,
        "conditions": person.conditions,
        "usual": person.usual or "",
        "risks": person.risks or "",
        "mobility": person.mobility or "",
    }
