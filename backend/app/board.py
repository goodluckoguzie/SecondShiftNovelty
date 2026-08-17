from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import Session, select

from .models import CareEvent, PatternFlag, PersonProfile, User


def board_window_start(
    session: Session,
    since: Optional[datetime] = None,
    now: Optional[datetime] = None,
) -> datetime:
    if since is not None:
        return since
    now = now or datetime.utcnow()
    last_20 = now.replace(hour=20, minute=0, second=0, microsecond=0)
    if now.hour < 20:
        last_20 -= timedelta(days=1)
    twelve = now - timedelta(hours=12)
    return min(last_20, twelve)


def _score(person: PersonProfile, flags: list[PatternFlag], recent: list[CareEvent], now: datetime) -> int:
    score = 0
    if flags:
        score += 100 + 10 * len(flags)
    returned = person.hospital_return_at
    if returned and returned >= now - timedelta(hours=72):
        score += 50
    if any(e.type in {"symptom", "mood", "sleep", "incident"} or e.subtype in {"not_himself", "mood_low"} for e in recent):
        score += 20
    return score


def _about(person: PersonProfile, recent: list[CareEvent]) -> Optional[str]:
    bits = [bit for bit in (person.risks, person.mobility) if bit]
    pref = next((e.detail for e in reversed(recent) if e.type == "preference" or e.subtype == "about_me"), None)
    if pref:
        bits.append(pref)
    if not bits:
        return None
    return ". ".join(bits)


def build_board(session: Session, since: Optional[datetime] = None, now: Optional[datetime] = None) -> dict:
    now = now or datetime.utcnow()
    start = board_window_start(session, since, now)
    people = session.exec(select(PersonProfile).order_by(PersonProfile.name)).all()
    all_flags = session.exec(select(PatternFlag)).all()
    flags_by = {}
    for flag in all_flags:
        flags_by.setdefault(flag.person_id, []).append(flag)
    events = session.exec(select(CareEvent)).all()
    users = {u.id: u for u in session.exec(select(User)).all()}
    rows = []
    flag_count = 0
    risk_names = []
    for person in people:
        flags = flags_by.get(person.id) or []
        flag_count += len(flags)
        recent = [e for e in events if e.person_id == person.id and e.event_time >= start]
        recent.sort(key=lambda e: e.event_time, reverse=True)
        last = recent[0] if recent else None
        logger = users.get(last.logger_id) if last and last.logger_id else None
        source = (last.source or "staff") if last else None
        logger_label = None
        if logger:
            logger_label = f"{logger.display_name} (home)" if source == "from_home" or logger.role == "family" else logger.display_name
        if person.risks or person.mobility:
            risk_names.append(person.name)
        rows.append(
            {
                "id": person.id,
                "name": person.name,
                "age": person.age,
                "score": _score(person, flags, recent, now),
                "line": (last.detail or last.raw_transcript or "") if last else "",
                "quote": last.raw_transcript if last else "",
                "when": last.event_time.isoformat() if last and last.event_time else None,
                "event_id": last.id if last else None,
                "logger": logger_label,
                "source": source,
                "flags": [{"id": f.id, "subtype": f.subtype, "message": f.message} for f in flags],
                "about": _about(person, recent),
                "usual": person.usual or "",
                "risks": person.risks or "",
                "mobility": person.mobility or "",
                "hospital_return_at": person.hospital_return_at.isoformat() if person.hospital_return_at else None,
            }
        )
    rows.sort(key=lambda row: (-row["score"], row["name"]))
    return {
        "since": start.isoformat(),
        "flag_count": flag_count,
        "risks": risk_names,
        "people": rows,
    }
