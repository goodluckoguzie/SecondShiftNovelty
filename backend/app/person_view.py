from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import Session, select

from .models import CareEvent, PatternFlag, PersonProfile, User
from .ollama_client import ASK_SYSTEM, chat_json, ollama_available
from .safety import strip_advice

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

_CARRY = {
    "medication": "late tablets",
    "confusion": "confusion this week",
    "appetite_low": "low appetite",
    "vomiting": "sick after meals",
    "hospital_return": "back from hospital",
    "not_himself": "not himself",
}

_VIEW_SYSTEM = """You are briefing the next support worker about this resident, as if speaking at handover.
Write natural UK English in the active voice. Short sentences. He ate. He was sick after supper. Staff gave evening tablets late.
Use what the notes actually said: food, how he seemed, time of day. Connect it into a story of the week, not a list.
Never write counts such as "22 notes", "1 times", "Sick / vomit", or "see the cited logs".
Never diagnose. Never invent a symptom, food, or headache that was not in the notes.
JSON only: {"week_summary":"4 to 6 natural sentences","yesterday_summary":"2 natural sentences about yesterday"}
"""

_UNSETTLED = {
    "fall",
    "vomiting",
    "confusion",
    "agitation",
    "dose_late",
    "dose_missed",
    "appetite_low",
    "mood_low",
    "not_himself",
    "awake_night",
}

_EAT_ASK = re.compile(
    r"\b(eat|eaten|ate|meal|breakfast|lunch|supper|dinner|food|appetite|hungry|snack)\b",
    re.I,
)


def _label(event: CareEvent) -> str:
    return _EVENT_LABELS.get(event.subtype) or (event.subtype or event.type or "Note").replace("_", " ")


def _logger(session: Session, event: CareEvent) -> str:
    if not event.logger_id:
        return "Wing" if (event.source or "staff") != "from_home" else "Home"
    user = session.get(User, event.logger_id)
    if not user:
        return "Wing"
    if event.source == "from_home" or user.role == "family":
        return f"{user.display_name} (home)"
    return user.display_name


def _event_row(session: Session, event: CareEvent) -> dict:
    return {
        "id": event.id,
        "event_time": event.event_time.isoformat(),
        "type": event.type,
        "subtype": event.subtype,
        "label": _label(event),
        "detail": event.detail or event.raw_transcript or "",
        "raw_transcript": event.raw_transcript or "",
        "logger": _logger(session, event),
    }


def _shift_events(events: list[CareEvent]) -> list[CareEvent]:
    if not events:
        return []
    latest = max(e.event_time for e in events)
    start = latest - timedelta(hours=14)
    rows = [e for e in events if e.event_time >= start]
    rows.sort(key=lambda e: e.event_time)
    return rows


def _in_day(events: list[CareEvent], day: datetime) -> list[CareEvent]:
    start = day.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    rows = [e for e in events if start <= e.event_time < end]
    rows.sort(key=lambda e: e.event_time)
    return rows


def _factual_day(rows: list[CareEvent], empty: str) -> str:
    if not rows:
        return empty
    bits = [f"{_label(event).lower()} ({event.event_time.strftime('%H:%M')})" for event in rows[:6]]
    extra = f", plus {len(rows) - 6} more." if len(rows) > 6 else "."
    text = ", ".join(bits)
    return text[0].upper() + text[1:] + extra


def _is_unsettled(event: CareEvent) -> bool:
    return event.subtype in _UNSETTLED or event.type == "incident"


def _count(rows: list[CareEvent], *subtypes: str) -> int:
    wanted = set(subtypes)
    return sum(1 for e in rows if e.subtype in wanted)


def _essentials(week: list[CareEvent]) -> list[dict]:
    return [
        {"key": "vomiting", "label": "Sick / vomit", "count": _count(week, "vomiting")},
        {"key": "fall", "label": "Falls", "count": _count(week, "fall")},
        {"key": "medication", "label": "Late tablets", "count": _count(week, "dose_late", "dose_missed")},
        {"key": "appetite_low", "label": "Low appetite", "count": _count(week, "appetite_low")},
        {"key": "confusion", "label": "Confusion", "count": _count(week, "confusion")},
        {"key": "mood", "label": "Low mood", "count": _count(week, "mood_low", "not_himself")},
        {"key": "sleep", "label": "Up at night", "count": _count(week, "awake_night", "settled_late")},
    ]


def _stability(events: list[CareEvent], now: datetime) -> list[dict]:
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    days = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        rows = _in_day(events, day)
        issues = [e for e in rows if _is_unsettled(e)]
        days.append(
            {
                "date": day.date().isoformat(),
                "label": day.strftime("%a"),
                "stable": 0 if issues else 1,
                "issues": len(issues),
            }
        )
    return days


def _day_briefs(events: list[CareEvent]) -> dict[str, str]:
    by_day: dict[str, list[CareEvent]] = {}
    for event in events:
        key = event.event_time.date().isoformat()
        by_day.setdefault(key, []).append(event)
    out = {}
    for key, rows in by_day.items():
        rows.sort(key=lambda e: e.event_time)
        out[key] = _factual_day(rows, "Nothing spoken that day.")
    return out


def _looks_like_counts(text: str) -> bool:
    lowered = (text or "").lower()
    return " times" in lowered or "notes in 7 days" in lowered or "sick / vomit" in lowered


def _narrative_fallback(person: PersonProfile, week: list[CareEvent], empty: str, include_usual: bool = True) -> str:
    if not week:
        return empty
    bits = []
    if include_usual and person.usual:
        bits.append(f"{person.name} usually {person.usual.rstrip('.')}.")
    seen: set[str] = set()
    for event in sorted(week, key=lambda e: e.event_time, reverse=True):
        detail = (event.detail or event.raw_transcript or "").strip().rstrip(".")
        if not detail or event.subtype in seen:
            continue
        seen.add(event.subtype or event.type or "")
        bits.append(f"{detail} ({event.event_time.strftime('%d %b')}).")
        if len(bits) >= 5:
            break
    return " ".join(bits) if bits else empty


def _draft_week(
    person: PersonProfile,
    week: list[CareEvent],
    yesterday: list[CareEvent],
    draft: bool = False,
) -> tuple[str, str, bool]:
    week_text = _narrative_fallback(person, week, f"Nothing has been spoken about {person.name} in the last 7 days.")
    yest_text = _narrative_fallback(person, yesterday, "Nothing spoken yesterday.", include_usual=False)
    if not draft or not week:
        return week_text, yest_text, False
    if not ollama_available():
        return week_text, yest_text, False
    lines = [
        f"Write about {person.name}. He is {person.age}.",
        f"He usually {person.usual}." if person.usual else "",
        "Spoken notes from the last 7 days (use these; do not list them as a tally):",
    ]
    for event in sorted(week, key=lambda e: e.event_time)[-40:]:
        quote = (event.raw_transcript or event.detail or "").replace("\n", " ")
        lines.append(f"- {event.event_time.strftime('%d %b %H:%M')}: {quote}")
    lines.append("Yesterday's spoken notes only:")
    if yesterday:
        for event in yesterday:
            quote = (event.raw_transcript or event.detail or "").replace("\n", " ")
            lines.append(f"- {event.event_time.strftime('%H:%M')}: {quote}")
    else:
        lines.append("- none")
    try:
        out = chat_json("\n".join(line for line in lines if line), _VIEW_SYSTEM, timeout=45.0)
        drafted = str(out.get("week_summary") or "").strip()
        yest_draft = str(out.get("yesterday_summary") or "").strip()
        if drafted and not _looks_like_counts(drafted):
            week_text = drafted
        if yest_draft and not _looks_like_counts(yest_draft):
            yest_text = yest_draft
        return week_text, yest_text, True
    except Exception:
        return week_text, yest_text, False


def build_person_view(
    session: Session,
    person: PersonProfile,
    user_id: Optional[int] = None,
    draft: bool = False,
) -> dict:
    events = session.exec(select(CareEvent).where(CareEvent.person_id == person.id)).all()
    flags = session.exec(select(PatternFlag).where(PatternFlag.person_id == person.id)).all()
    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    week_start = today - timedelta(days=6)
    today_rows = _in_day(events, today)
    yesterday_rows = _in_day(events, yesterday)
    week_rows = [e for e in events if e.event_time >= week_start]
    last_logged = None
    if user_id:
        mine = [e for e in events if e.logger_id == user_id]
        if mine:
            last_logged = max(e.event_time for e in mine)
    chips = []
    for flag in flags:
        chips.append(_CARRY.get(flag.subtype) or (flag.message or "").split(".")[0].lower())
    seen = set()
    unique_chips = []
    for chip in chips:
        if chip and chip not in seen:
            seen.add(chip)
            unique_chips.append(chip)
    essentials = _essentials(week_rows)
    week_text, yest_text, drafted = _draft_week(person, week_rows, yesterday_rows, draft=draft)
    days = sorted({e.event_time.date().isoformat() for e in events})
    return {
        "last_logged_at": last_logged.isoformat() if last_logged else None,
        "week_summary": strip_advice(week_text),
        "yesterday_summary": strip_advice(yest_text),
        "today_count": len(today_rows),
        "yesterday_count": len(yesterday_rows),
        "what_changed_chips": unique_chips[:4],
        "essentials": essentials,
        "stability": _stability(events, now),
        "day_briefs": _day_briefs(events),
        "days": days,
        "today": [_event_row(session, e) for e in today_rows],
        "yesterday": [_event_row(session, e) for e in yesterday_rows],
        "last_shift": [_event_row(session, e) for e in _shift_events(events)],
        "last_shift_label": "",
        "what_changed": week_text,
        "in_short": week_text,
        "drafted": drafted,
    }


def _day_start(now: datetime) -> datetime:
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _is_meal(event: CareEvent) -> bool:
    return event.type == "meal" or event.subtype in {"eaten", "appetite_low"}


def _meal_line(event: CareEvent) -> str:
    quote = (event.detail or event.raw_transcript or _label(event)).replace("\n", " ")
    return f"{event.event_time.strftime('%d %b %Y %H:%M')} {quote}"


def _record_counts(events: list[CareEvent], now: datetime) -> list[str]:
    today = _day_start(now)
    yesterday = today - timedelta(days=1)
    meals = [e for e in events if _is_meal(e)]
    today_meals = [e for e in meals if e.event_time >= today]
    yest_meals = [e for e in meals if yesterday <= e.event_time < today]
    last_meal = meals[-1] if meals else None
    lines = [
        "Python already counted. Do not recount.",
        f"Today ({today.strftime('%d %b %Y')}): {len(today_meals)} meal notes.",
        f"Yesterday: {len(yest_meals)} meal notes.",
    ]
    if today_meals:
        lines.append("Today's meals: " + "; ".join(_meal_line(e) for e in today_meals))
    else:
        lines.append("Today's meals: none. The record does not show they have eaten today.")
    if yest_meals:
        lines.append("Yesterday's meals: " + "; ".join(_meal_line(e) for e in yest_meals))
    if last_meal:
        lines.append(f"Last meal logged: id={last_meal.id} {_meal_line(last_meal)}")
    else:
        lines.append("Last meal logged: none.")
    return lines


def _meal_ask_answer(person: PersonProfile, events: list[CareEvent], now: datetime) -> tuple[str, list[CareEvent], bool]:
    today = _day_start(now)
    meals = [e for e in events if _is_meal(e)]
    meals.sort(key=lambda e: e.event_time)
    today_meals = [e for e in meals if e.event_time >= today]
    last_meal = meals[-1] if meals else None
    name = person.name
    if not today_meals:
        answer = (
            f"The notes do not show a meal today. {name} has not eaten according to the record. "
            "Please confirm they have not eaten."
        )
        if last_meal:
            answer += f" Last meal logged: {_meal_line(last_meal)}."
        return answer, ([last_meal] if last_meal else []), False
    bits = "; ".join(_meal_line(e) for e in today_meals)
    full = any(e.subtype == "eaten" for e in today_meals)
    low = any(e.subtype == "appetite_low" for e in today_meals)
    if low and not full:
        answer = (
            f"The notes do not show a full meal today. {name} has not eaten according to the record "
            f"({bits}). Please confirm they have not eaten."
        )
        return answer, today_meals, False
    if low:
        answer = f"The notes show a meal today, and appetite was low ({bits}). Please confirm what they ate."
        return answer, today_meals, True
    answer = f"The notes show {name} has eaten today ({bits})."
    return answer, today_meals, True


def ask_person_notes(session: Session, person: PersonProfile, question: str, now: Optional[datetime] = None) -> dict:
    q = (question or "").strip()
    if not q:
        raise ValueError("Ask something about the notes.")
    now = now or datetime.utcnow()
    events = session.exec(select(CareEvent).where(CareEvent.person_id == person.id)).all()
    events.sort(key=lambda e: e.event_time)
    if _EAT_ASK.search(q):
        answer, cite_events, in_notes = _meal_ask_answer(person, events, now)
        return {
            "question": q,
            "answer": answer,
            "in_notes": in_notes,
            "cites": [_event_row(session, e) for e in cite_events if e is not None],
        }
    if not ollama_available():
        raise RuntimeError("Ollama is not running. It reads the notes and answers.")
    chosen = events[-48:]
    by_id = {e.id: e for e in chosen if e.id is not None}
    lines = [
        f"Now is {now.strftime('%d %b %Y %H:%M')}.",
        f"Person: {person.name}.",
        f"Question: {q}",
        "",
        *_record_counts(events, now),
        "",
        "Stored notes:",
    ]
    if not chosen:
        lines.append("- none")
    for event in chosen:
        quote = (event.raw_transcript or event.detail or "").replace("\n", " ")
        lines.append(
            f"- id={event.id} {event.event_time.strftime('%d %b %Y %H:%M')} {_label(event)} "
            f"said: {quote} ({_logger(session, event)})"
        )
    data = chat_json("\n".join(lines), ASK_SYSTEM, timeout=90.0)
    answer = str(data.get("answer") or "").strip()
    if not answer:
        answer = "That is not in the notes."
    raw_ids = data.get("cite_ids") or []
    cites = []
    for item in raw_ids:
        try:
            eid = int(item)
        except (TypeError, ValueError):
            continue
        row = by_id.get(eid) or session.get(CareEvent, eid)
        if row and row.person_id == person.id:
            cites.append(_event_row(session, row))
    if not cites and chosen and data.get("in_notes"):
        cites = [_event_row(session, chosen[-1])]
    return {
        "question": q,
        "answer": answer,
        "in_notes": bool(data.get("in_notes", bool(cites))),
        "cites": cites,
    }
