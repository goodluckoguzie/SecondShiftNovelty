from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from .briefs import generate_brief, generate_handover
from .config import CACHED_BRIEF_PDF, CACHED_HANDOVER_PDF, DATA_DIR, DISCLAIMER, WHISPER_MODEL
from .db import engine, get_session, init_db
from .extractor import heuristic_extract, ollama_extract, parse_event_time
from .models import CareEvent, MedicationSchedule, PatternFlag, PersonProfile
from .ollama_client import ollama_available
from .patterns import chart_payload, recompute_flags
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


class HandoverRequest(BaseModel):
    name: str = "your sister"


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
    }


@app.get("/profile")
def profile(session: Session = Depends(get_session)):
    person = session.exec(select(PersonProfile)).first()
    meds = session.exec(select(MedicationSchedule)).all()
    if not person:
        raise HTTPException(404, "No profile")
    return {
        "name": person.name,
        "age": person.age,
        "conditions": person.conditions,
        "allergies": person.allergies,
        "disclaimer": DISCLAIMER,
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
def list_events(session: Session = Depends(get_session)):
    rows = session.exec(select(CareEvent).order_by(CareEvent.event_time.desc())).all()
    return [_event_out(row) for row in rows]


@app.get("/flags")
def list_flags(session: Session = Depends(get_session)):
    rows = session.exec(select(PatternFlag)).all()
    return [
        {
            "id": r.id,
            "kind": r.kind,
            "subtype": r.subtype,
            "message": r.message,
            "related_date": r.related_date.isoformat() if r.related_date else None,
        }
        for r in rows
    ]


@app.get("/patterns")
def patterns(session: Session = Depends(get_session)):
    return chart_payload(session)


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


@app.post("/log")
def log_event(body: LogRequest, session: Session = Depends(get_session)):
    transcript = body.transcript.strip()
    if not transcript:
        raise HTTPException(400, "Empty transcript")
    if is_emergency(transcript):
        return {
            "emergency": True,
            "screen": "Call 999 now. Second Shift will not process this with the AI.",
            "events": [],
            "flags": [],
            "confirmation": None,
        }

    now = datetime.utcnow()
    extracted = heuristic_extract(transcript, now) if body.use_heuristic else ollama_extract(transcript, now)
    stored = []
    for item in extracted.get("events") or []:
        event = CareEvent(
            logged_at=now,
            event_time=parse_event_time(item.get("event_time"), now),
            type=item.get("type") or "note",
            subtype=item.get("subtype") or "note",
            detail=item.get("detail") or "",
            raw_transcript=transcript,
            confidence=float(item.get("confidence") or 0.5),
            urgent=body.urgent,
        )
        session.add(event)
        stored.append(event)
    session.commit()
    for event in stored:
        session.refresh(event)
    flags = recompute_flags(session)
    confirmation = strip_advice(extracted.get("confirmation") or "Logged.")
    flag_note = next((f.message for f in flags if f.subtype == "confusion"), None)
    if flag_note:
        confirmation = f"{confirmation} {flag_note}".strip()
    return {
        "emergency": False,
        "events": [_event_out(e) for e in stored],
        "flags": [
            {"kind": f.kind, "subtype": f.subtype, "message": f.message} for f in flags
        ],
        "confirmation": confirmation,
        "clarifying_question": extracted.get("clarifying_question"),
        "nhs111": "If you are worried and it is not an emergency, call NHS 111.",
    }


@app.post("/briefs")
def create_brief(session: Session = Depends(get_session)):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = str(CACHED_BRIEF_PDF)
    brief = generate_brief(session, path, urgent=any(e.urgent for e in session.exec(select(CareEvent)).all()))
    return {"id": brief.id, "markdown": brief.markdown, "pdf_path": brief.pdf_path}


@app.get("/briefs/latest.pdf")
def latest_brief_pdf():
    if not CACHED_BRIEF_PDF.exists():
        raise HTTPException(404, "No brief yet")
    return FileResponse(CACHED_BRIEF_PDF, media_type="application/pdf", filename="gp-brief.pdf")


@app.post("/handover")
def create_handover(body: Optional[HandoverRequest] = None, session: Session = Depends(get_session)):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    name = body.name if body else "your sister"
    brief = generate_handover(session, str(CACHED_HANDOVER_PDF), name=name)
    return {"id": brief.id, "markdown": brief.markdown, "pdf_path": brief.pdf_path}


@app.get("/handover/latest.pdf")
def latest_handover_pdf():
    if not CACHED_HANDOVER_PDF.exists():
        raise HTTPException(404, "No handover yet")
    return FileResponse(
        CACHED_HANDOVER_PDF, media_type="application/pdf", filename="handover.pdf"
    )


def _event_out(row: CareEvent) -> dict:
    return {
        "id": row.id,
        "logged_at": row.logged_at.isoformat(),
        "event_time": row.event_time.isoformat(),
        "type": row.type,
        "subtype": row.subtype,
        "detail": row.detail,
        "raw_transcript": row.raw_transcript,
        "confidence": row.confidence,
        "urgent": row.urgent,
    }
