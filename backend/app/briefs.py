from __future__ import annotations

from datetime import datetime, timedelta

from sqlmodel import Session, select

from .models import Brief, CareEvent, MedicationSchedule, PatternFlag, PersonProfile
from .ollama_client import QUESTIONS_SYSTEM, chat_json
from .pdf_render import write_pdf


def _cite(event: CareEvent) -> str:
    return f"[log {event.event_time.strftime('%d %b %Y %H:%M')}]"


def build_factual_markdown(session: Session, urgent: bool = False) -> tuple[str, datetime, datetime]:
    person = session.exec(select(PersonProfile)).first()
    meds = session.exec(select(MedicationSchedule)).all()
    events = session.exec(select(CareEvent).order_by(CareEvent.event_time)).all()
    flags = session.exec(select(PatternFlag)).all()
    if not events:
        now = datetime.utcnow()
        return "# Visit brief\n\nNo events logged.", now, now

    start = min(e.event_time for e in events)
    end = max(e.event_time for e in events)
    lines = [
        f"# GP / memory-clinic brief",
        "",
        f"**{person.name if person else 'Patient'}, {person.age if person else ''} · {person.conditions if person else ''}**",
        "",
        "Second Shift organises notes. It is not a medical device and does not give medical advice.",
        "",
        "## Medicines this period",
    ]
    for med in meds:
        changed = (
            f" (changed {med.last_changed_at.strftime('%d %b %Y')})" if med.last_changed_at else ""
        )
        lines.append(f"- {med.name} {med.dose} at {med.scheduled_times}{changed}")
    late = [e for e in events if e.subtype in ("dose_late", "dose_missed")]
    lines.append(f"- Late or missed doses: {len(late)}")
    for event in late:
        lines.append(f"  - {event.detail} {_cite(event)}")

    lines += ["", "## Symptom episodes"]
    symptoms = [e for e in events if e.type == "symptom"]
    for event in symptoms:
        lines.append(f"- {event.subtype}: {event.detail} {_cite(event)}")

    lines += ["", "## Notable patterns"]
    if flags:
        for flag in flags:
            lines.append(f"- {flag.message}")
    else:
        lines.append("- None flagged by the rules engine.")

    if urgent or any(e.urgent for e in events):
        lines += ["", "## Urgent for the GP"]
        lines.append("- Carer asked for this to be listed as worth checking soon. Not a triage judgement.")

    lines += ["", "## Appendix: source quotes"]
    for event in events[-12:]:
        quote = event.raw_transcript or event.detail
        lines.append(f"- {_cite(event)} “{quote}”")

    return "\n".join(lines), start, end


def suggest_questions(session: Session) -> list[str]:
    flags = session.exec(select(PatternFlag)).all()
    evidence = "\n".join(f"- {f.message}" for f in flags) or "No pattern flags."
    fallback = [
        "Could evening confusion relate to the 7 Aug donepezil dose change?",
        "Is late evening dosing reducing the effect of the night-time medicines?",
        "Should we review appetite and weight at this appointment?",
    ]
    try:
        data = chat_json(f"Evidence:\n{evidence}", QUESTIONS_SYSTEM)
        questions = [str(q) for q in data.get("questions", []) if str(q).strip()]
        return questions[:5] or fallback
    except Exception:
        return fallback


def generate_brief(session: Session, pdf_path: str, urgent: bool = False) -> Brief:
    body, start, end = build_factual_markdown(session, urgent=urgent)
    questions = suggest_questions(session)
    q_block = "\n".join(f"- {q}" for q in questions)
    markdown = body.replace(
        "## Appendix: source quotes",
        f"## Suggested questions for the GP / memory clinic\n{q_block}\n\n## Appendix: source quotes",
    )
    write_pdf(markdown, pdf_path)
    brief = Brief(
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


def generate_handover(session: Session, pdf_path: str, name: str = "your sister") -> Brief:
    events = session.exec(select(CareEvent).order_by(CareEvent.event_time)).all()
    flags = session.exec(select(PatternFlag)).all()
    meds = session.exec(select(MedicationSchedule)).all()
    end = max((e.event_time for e in events), default=datetime.utcnow())
    start = end - timedelta(hours=72)
    recent = [e for e in events if e.event_time >= start]
    lines = [
        f"# Family handover for {name}",
        "",
        f"Last 72 hours to {end.strftime('%d %b %Y %H:%M')}.",
        "",
        "## What happened",
    ]
    for event in recent:
        lines.append(
            f"- {event.event_time.strftime('%d %b %H:%M')} {event.type}/{event.subtype}: {event.detail}"
        )
    lines += ["", "## Open flags"]
    for flag in flags:
        lines.append(f"- {flag.message}")
    lines += ["", "## What's due next"]
    for med in meds:
        lines.append(f"- {med.name} {med.dose} at {med.scheduled_times}")
    markdown = "\n".join(lines)
    write_pdf(markdown, pdf_path)
    brief = Brief(
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
