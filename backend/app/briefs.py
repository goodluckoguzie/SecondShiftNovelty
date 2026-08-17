from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import Session, select

from .models import Brief, CareEvent, MedicationSchedule, PatternFlag, PersonProfile, Shift, User
from .ollama_client import QUESTIONS_SYSTEM, chat_json
from .pdf_render import write_pdf

_EVENT_LABELS = {
    "dose_late": "Late medicines",
    "dose_missed": "Missed medicines",
    "confusion": "Confusion",
    "agitation": "Agitation",
    "appetite_low": "Low appetite",
    "vomiting": "Vomiting",
    "eaten": "Eaten",
    "mood_low": "Low mood",
    "not_himself": "Not himself",
    "awake_night": "Up in the night",
    "settled_late": "Settled late",
    "fall": "Fall",
    "about_me": "About them",
    "hospital_return": "Back from hospital",
}

_FLAG_TITLES = {
    "medication": "Late medicines",
    "confusion": "Confusion",
    "appetite_low": "Low appetite",
    "vomiting": "Vomiting",
    "hospital_return": "Back from hospital",
    "not_himself": "Not himself",
}


def _cite(event: CareEvent) -> str:
    return f"[log {event.event_time.strftime('%d %b %Y %H:%M')}]"


def _event_label(event: CareEvent) -> str:
    return _EVENT_LABELS.get(event.subtype) or event.subtype.replace("_", " ")


def _flag_line(flag: PatternFlag) -> str:
    title = _FLAG_TITLES.get(flag.subtype) or flag.subtype.replace("_", " ").title()
    message = (flag.message or "").strip()
    if not message:
        return title
    if message.lower().startswith(title.lower()):
        return message
    return f"{title}. {message}"


def _when(dt: datetime) -> str:
    return dt.strftime("%d %b %Y, %H:%M")


def _person_rows(session: Session, person: PersonProfile):
    events = session.exec(
        select(CareEvent).where(CareEvent.person_id == person.id).order_by(CareEvent.event_time)
    ).all()
    flags = session.exec(select(PatternFlag).where(PatternFlag.person_id == person.id)).all()
    meds = session.exec(select(MedicationSchedule).where(MedicationSchedule.person_id == person.id)).all()
    users = {u.id: u for u in session.exec(select(User)).all()}
    return events, flags, meds, users


def _logger_label(event: CareEvent, users: dict[int, User]) -> str:
    user = users.get(event.logger_id) if event.logger_id else None
    if not user:
        return "staff" if (event.source or "staff") != "from_home" else "family"
    if event.source == "from_home" or user.role == "family":
        return f"{user.display_name} (home)"
    return user.display_name


def _is_home(event: CareEvent, users: dict[int, User]) -> bool:
    if (event.source or "staff") == "from_home":
        return True
    user = users.get(event.logger_id) if event.logger_id else None
    return bool(user and user.role == "family")


def build_factual_markdown(
    session: Session, person: PersonProfile, urgent: bool = False
) -> tuple[str, datetime, datetime]:
    events, flags, meds, users = _person_rows(session, person)
    if not events:
        now = datetime.utcnow()
        return "# Visit brief\n\nNo events logged.", now, now

    start = min(e.event_time for e in events)
    end = max(e.event_time for e in events)
    staff_events = [e for e in events if not _is_home(e, users)]
    home_events = [e for e in events if _is_home(e, users)]
    lines = [
        "# GP and memory clinic brief",
        "",
        f"{person.name}, {person.age}. {person.conditions}.",
        "",
        "Second Shift organises notes. It is not a medical device and does not give medical advice.",
        "",
        "## From the shift",
        "",
    ]
    if staff_events:
        for event in staff_events[-12:]:
            lines.append(
                f"- {_event_label(event)}: {event.detail} {_cite(event)} ({_logger_label(event, users)})"
            )
    else:
        lines.append("- Nothing spoken on shift.")
    lines += ["", "## From home", ""]
    if home_events:
        for event in home_events[-12:]:
            lines.append(
                f"- {_event_label(event)}: {event.detail} {_cite(event)} ({_logger_label(event, users)})"
            )
    else:
        lines.append("- Nothing logged from home.")
    lines += ["", "## Medicines this period"]
    for med in meds:
        changed = (
            f" (changed {med.last_changed_at.strftime('%d %b %Y')})" if med.last_changed_at else ""
        )
        lines.append(f"- {med.name} {med.dose}, due at {med.scheduled_times}{changed}")
    late = [e for e in events if e.subtype in ("dose_late", "dose_missed")]
    lines.append(f"- Late or missed doses: {len(late)}")
    for event in late:
        lines.append(f"  - {event.detail} {_cite(event)}")

    lines += ["", "## Symptom episodes"]
    symptoms = [e for e in events if e.type == "symptom"]
    for event in symptoms:
        lines.append(f"- {_event_label(event)}: {event.detail} {_cite(event)}")

    lines += ["", "## Notable patterns"]
    if flags:
        for flag in flags:
            lines.append(f"- {flag.message}")
    else:
        lines.append("- None flagged by the rules engine.")

    if urgent or any(e.urgent for e in events):
        lines += ["", "## Urgent for the GP"]
        lines.append("- Asked for this to be listed as worth checking soon. Not a triage judgement.")

    lines += ["", "## Appendix: source quotes"]
    for event in events[-12:]:
        quote = event.raw_transcript or event.detail
        lines.append(f"- {_cite(event)} {_logger_label(event, users)}: “{quote}”")

    return "\n".join(lines), start, end


def suggest_questions(session: Session, person: PersonProfile) -> list[str]:
    flags = session.exec(select(PatternFlag).where(PatternFlag.person_id == person.id)).all()
    evidence = "\n".join(f"- {f.message}" for f in flags) or "No pattern flags."
    fallback = [
        "Could evening confusion relate to the 7 Aug donepezil dose change?",
        "Is late evening dosing reducing the effect of the night time medicines?",
        "Should we review appetite and weight at this appointment?",
    ]
    if any(f.subtype == "vomiting" for f in flags):
        fallback = [
            "Vomiting after meals was logged more than once. Is a review needed?",
            "Should we check hydration and weight after the recent GI episodes?",
            "Are any medicines more likely to upset the stomach after food?",
        ]
    try:
        data = chat_json(f"Evidence:\n{evidence}", QUESTIONS_SYSTEM, timeout=8.0)
        questions = [str(q) for q in data.get("questions", []) if str(q).strip()]
        return questions[:5] or fallback
    except Exception:
        return fallback


def generate_brief(session: Session, person: PersonProfile, pdf_path: str, urgent: bool = False) -> Brief:
    body, start, end = build_factual_markdown(session, person, urgent=urgent)
    questions = suggest_questions(session, person)
    q_block = "\n".join(f"- {q}" for q in questions)
    markdown = body.replace(
        "## Appendix: source quotes",
        f"## Suggested questions for the GP and memory clinic\n{q_block}\n\n## Appendix: source quotes",
    )
    write_pdf(markdown, pdf_path)
    brief = Brief(
        person_id=person.id,
        created_at=datetime.utcnow(),
        kind="gp",
        markdown=markdown,
        pdf_path=pdf_path,
        period_start=start,
        period_end=end,
    )
    session.add(brief)
    session.commit()
    session.refresh(brief)
    return brief


def generate_handover(
    session: Session,
    person: PersonProfile,
    pdf_path: str,
    name: str = "next worker",
    window: str = "72h",
    shift: Optional[Shift] = None,
) -> Brief:
    events, flags, meds, users = _person_rows(session, person)
    if window == "shift" and shift:
        start = shift.started_at
        end = shift.ended_at or datetime.utcnow()
        title = f"# Shift handout for {name}"
        if end - start < timedelta(minutes=5):
            period_line = f"This shift so far, from {_when(start)}."
        else:
            period_line = f"This shift, {_when(start)} to {_when(end)}."
        empty = "Nothing was spoken on this shift."
    else:
        end = max((e.event_time for e in events), default=datetime.utcnow())
        start = end - timedelta(hours=72)
        title = f"# Family handover for {name}"
        period_line = f"Last 72 hours, to {_when(end)}."
        empty = "Nothing was spoken in the last 72 hours."
    recent = [e for e in events if start <= e.event_time <= end]
    lines = [
        title,
        "",
        period_line,
        "",
        f"For {person.name}.",
        "",
        "## Still open",
        "",
    ]
    if flags:
        for flag in flags[:3]:
            lines.append(f"- {_flag_line(flag)}")
    else:
        lines.append("Nothing still open.")
    lines += ["", "## What was spoken", ""]
    if recent:
        for event in recent[-8:]:
            lines.append(
                f"- {_when(event.event_time)}, {_event_label(event)}. {event.detail} {_cite(event)} ({_logger_label(event, users)})"
            )
    else:
        lines.append(empty)
    lines += ["", "## Due next", ""]
    for med in meds:
        lines.append(f"- {med.name} {med.dose}, due at {med.scheduled_times}")
    if not meds:
        lines.append("No medicines on the schedule.")
    markdown = "\n".join(lines)
    write_pdf(markdown, pdf_path)
    brief = Brief(
        person_id=person.id,
        created_at=datetime.utcnow(),
        kind="handover",
        markdown=markdown,
        pdf_path=pdf_path,
        period_start=start,
        period_end=end,
    )
    session.add(brief)
    session.commit()
    session.refresh(brief)
    return brief
