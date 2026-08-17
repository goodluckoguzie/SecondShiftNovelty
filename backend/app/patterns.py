from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, Optional

from sqlmodel import Session, select

from .models import CareEvent, MedicationSchedule, PatternFlag, PersonProfile
from .slots import unpack_slots


def _in_window(events: Iterable[CareEvent], days: int = 7) -> list[CareEvent]:
    items = list(events)
    if not items:
        return []
    latest = max(e.event_time for e in items)
    start = latest - timedelta(days=days)
    return [e for e in items if e.event_time >= start]


def _ids(events: list[CareEvent]) -> str:
    return ",".join(str(e.id) for e in events if e.id is not None)


def recompute_flags(session: Session, person_id: Optional[int] = None) -> list[PatternFlag]:
    query = select(PatternFlag)
    if person_id is not None:
        query = query.where(PatternFlag.person_id == person_id)
    for row in session.exec(query).all():
        session.delete(row)
    session.commit()

    people: list[Optional[int]]
    if person_id is not None:
        people = [person_id]
    else:
        ids = {e.person_id for e in session.exec(select(CareEvent)).all()}
        people = list(ids) or [None]

    now = datetime.utcnow()
    flags: list[PatternFlag] = []
    for pid in people:
        flags.extend(_flags_for_person(session, pid, now))
    session.add_all(flags)
    session.commit()
    for flag in flags:
        session.refresh(flag)
    return flags


def _flags_for_person(session: Session, person_id: Optional[int], now: datetime) -> list[PatternFlag]:
    event_q = select(CareEvent)
    med_q = select(MedicationSchedule)
    if person_id is not None:
        event_q = event_q.where(CareEvent.person_id == person_id)
        med_q = med_q.where(MedicationSchedule.person_id == person_id)
    events = session.exec(event_q).all()
    meds = session.exec(med_q).all()
    window7 = _in_window(events, 7)
    window14 = _in_window(events, 14)
    flags: list[PatternFlag] = []

    late = [e for e in window7 if e.type == "medication" and e.subtype in ("dose_late", "dose_missed")]
    if len(late) >= 2:
        flags.append(
            PatternFlag(
                person_id=person_id,
                created_at=now,
                kind="late_or_missed_doses",
                subtype="medication",
                message=f"{len(late)} late or missed evening doses in the last 7 days.",
                evidence_event_ids=_ids(late),
            )
        )

    confusions = [e for e in window7 if e.type == "symptom" and e.subtype == "confusion"]
    if len(confusions) >= 3:
        change = next((m.last_changed_at for m in meds if m.last_changed_at), None)
        extra = ""
        related = change
        if change and min(e.event_time for e in confusions) >= change:
            extra = f" Episodes began after the dose change on {change.strftime('%d %b')}."
        flags.append(
            PatternFlag(
                person_id=person_id,
                created_at=now,
                kind="symptom_recurrence",
                subtype="confusion",
                message=f"Confusion logged {len(confusions)} times in 7 days.{extra}",
                related_date=related,
                evidence_event_ids=_ids(confusions),
            )
        )

    appetite = [e for e in window7 if e.subtype == "appetite_low"]
    if len(appetite) >= 4:
        flags.append(
            PatternFlag(
                person_id=person_id,
                created_at=now,
                kind="declining_trend",
                subtype="appetite_low",
                message=f"Low appetite noted {len(appetite)} times in 7 days.",
                evidence_event_ids=_ids(appetite),
            )
        )

    vomits = [e for e in window14 if e.subtype == "vomiting"]
    if len(vomits) >= 2:
        dates = ", ".join(sorted({e.event_time.strftime("%d %b") for e in vomits}))
        flags.append(
            PatternFlag(
                person_id=person_id,
                created_at=now,
                kind="symptom_recurrence",
                subtype="vomiting",
                message=f"Vomiting logged {len(vomits)} times in 14 days ({dates}). Similar issue last week.",
                evidence_event_ids=_ids(vomits),
            )
        )

    meals = [e for e in window14 if e.subtype in ("eaten", "appetite_low") or e.type == "meal"]
    for vomit in vomits:
        paired = [
            m
            for m in meals
            if m.event_time <= vomit.event_time <= m.event_time + timedelta(hours=2)
        ]
        if paired:
            food = next(
                (unpack_slots(item.slots).get("food") for item in paired + [vomit] if unpack_slots(item.slots).get("food")),
                None,
            )
            followed = f"followed {food}" if food else "followed a meal"
            flags.append(
                PatternFlag(
                    person_id=person_id,
                    created_at=now,
                    kind="meal_then_symptom",
                    subtype="vomiting",
                    message=f"Vomiting {followed} within 2 hours. See the cited logs.",
                    evidence_event_ids=_ids(paired + [vomit]),
                )
            )
            break

    person = session.get(PersonProfile, person_id) if person_id is not None else None
    if person and person.hospital_return_at:
        returned = person.hospital_return_at
        window72 = now - timedelta(hours=72)
        if returned >= window72:
            after = [e for e in events if e.event_time >= returned]
            if after:
                flags.append(
                    PatternFlag(
                        person_id=person_id,
                        created_at=now,
                        kind="hospital_return",
                        subtype="hospital_return",
                        message=(
                            f"Back from hospital since {returned.strftime('%d %b %H:%M')}. "
                            f"{len(after)} log(s) in that window."
                        ),
                        related_date=returned,
                        evidence_event_ids=_ids(after[:8]),
                    )
                )

    if person and (person.usual or "").strip():
        recent_mood = [
            e
            for e in window7
            if e.subtype in {"mood_low", "not_himself"} or e.type == "mood"
        ]
        if recent_mood:
            last = max(recent_mood, key=lambda e: e.event_time)
            flags.append(
                PatternFlag(
                    person_id=person_id,
                    created_at=now,
                    kind="not_himself_baseline",
                    subtype="not_himself",
                    message=(
                        f"{person.name} was {last.detail or 'not himself'}. "
                        f"He usually {person.usual.rstrip('.')}."
                    ),
                    evidence_event_ids=_ids([last]),
                )
            )

    return flags


def similar_events(session: Session, person_id: Optional[int], subtypes: list[str], days: int = 14) -> list[CareEvent]:
    events = session.exec(select(CareEvent).where(CareEvent.person_id == person_id)).all() if person_id is not None else session.exec(select(CareEvent)).all()
    window = _in_window(events, days)
    return [e for e in window if e.subtype in subtypes]


def chart_payload(session: Session, person_id: Optional[int] = None) -> dict:
    event_q = select(CareEvent)
    med_q = select(MedicationSchedule)
    if person_id is not None:
        event_q = event_q.where(CareEvent.person_id == person_id)
        med_q = med_q.where(MedicationSchedule.person_id == person_id)
    events = session.exec(event_q).all()
    meds = session.exec(med_q).all()
    change = next((m.last_changed_at for m in meds if m.last_changed_at), None)
    window = _in_window(events) or events
    if not window:
        return {"days": [], "dose_change": change.isoformat() if change else None}

    latest = max(e.event_time for e in window).date()
    days = []
    for i in range(6, -1, -1):
        day = latest - timedelta(days=i)
        confusion = sum(
            1 for e in events if e.subtype == "confusion" and e.event_time.date() == day
        )
        vomiting = sum(
            1 for e in events if e.subtype == "vomiting" and e.event_time.date() == day
        )
        days.append(
            {
                "date": day.isoformat(),
                "label": day.strftime("%a"),
                "confusion": confusion,
                "vomiting": vomiting,
            }
        )
    return {
        "days": days,
        "dose_change": change.isoformat() if change else None,
    }
