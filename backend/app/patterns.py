from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable

from sqlmodel import Session, select

from .models import CareEvent, MedicationSchedule, PatternFlag


def _in_window(events: Iterable[CareEvent], days: int = 7) -> list[CareEvent]:
    items = list(events)
    if not items:
        return []
    latest = max(e.event_time for e in items)
    start = latest - timedelta(days=days)
    return [e for e in items if e.event_time >= start]


def recompute_flags(session: Session) -> list[PatternFlag]:
    existing = session.exec(select(PatternFlag)).all()
    for row in existing:
        session.delete(row)
    session.commit()

    events = session.exec(select(CareEvent)).all()
    meds = session.exec(select(MedicationSchedule)).all()
    window = _in_window(events)
    now = datetime.utcnow()
    flags: list[PatternFlag] = []

    late = [e for e in window if e.type == "medication" and e.subtype in ("dose_late", "dose_missed")]
    if len(late) >= 2:
        flags.append(
            PatternFlag(
                created_at=now,
                kind="late_or_missed_doses",
                subtype="medication",
                message=f"{len(late)} late or missed evening doses in the last 7 days.",
            )
        )

    confusions = [e for e in window if e.type == "symptom" and e.subtype == "confusion"]
    if len(confusions) >= 3:
        change = next((m.last_changed_at for m in meds if m.last_changed_at), None)
        related = change
        extra = ""
        if change and min(e.event_time for e in confusions) >= change:
            extra = f" Episodes began after the dose change on {change.strftime('%d %b')}."
            related = change
        flags.append(
            PatternFlag(
                created_at=now,
                kind="symptom_recurrence",
                subtype="confusion",
                message=f"Confusion logged {len(confusions)} times in 7 days.{extra}",
                related_date=related,
            )
        )

    appetite = [e for e in window if e.subtype == "appetite_low"]
    if len(appetite) >= 4:
        flags.append(
            PatternFlag(
                created_at=now,
                kind="declining_trend",
                subtype="appetite_low",
                message=f"Low appetite noted {len(appetite)} times in 7 days.",
            )
        )

    session.add_all(flags)
    session.commit()
    for flag in flags:
        session.refresh(flag)
    return flags


def chart_payload(session: Session) -> dict:
    events = session.exec(select(CareEvent)).all()
    meds = session.exec(select(MedicationSchedule)).all()
    change = next((m.last_changed_at for m in meds if m.last_changed_at), None)
    window = _in_window(events) or events
    if not window:
        return {"days": [], "dose_change": change.isoformat() if change else None}

    latest = max(e.event_time for e in window).date()
    days = []
    for i in range(6, -1, -1):
        day = latest - timedelta(days=i)
        count = sum(
            1
            for e in events
            if e.type == "symptom" and e.subtype == "confusion" and e.event_time.date() == day
        )
        days.append({"date": day.isoformat(), "label": day.strftime("%a"), "confusion": count})
    return {
        "days": days,
        "dose_change": change.isoformat() if change else None,
    }
