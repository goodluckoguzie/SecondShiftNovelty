from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from .ollama_client import EXTRACT_SYSTEM, chat_json
from .safety import strip_advice
from .slots import sanitize_slots


def _guess_event_time(text: str, now: datetime) -> datetime:
    if re.search(r"\bup at (two|2)\b", text) or re.search(r"\bat (two|2)\b", text):
        two = now.replace(hour=2, minute=0, second=0, microsecond=0)
        return two + timedelta(days=1) if now.hour >= 12 else two
    clock = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", text)
    if clock:
        hour = int(clock.group(1))
        minute = int(clock.group(2) or 0)
        mer = clock.group(3)
        if mer == "pm" and hour < 12:
            hour += 12
        if mer == "am" and hour == 12:
            hour = 0
        return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return now


def _meal_from_text(text: str) -> str | None:
    if "breakfast" in text:
        return "breakfast"
    if "lunch" in text:
        return "lunch"
    if "supper" in text or "dinner" in text:
        return "supper"
    if "snack" in text:
        return "snack"
    if "porridge" in text:
        return "breakfast"
    if "milky drink" in text:
        return "supper"
    return None

def heuristic_extract(transcript: str, now: datetime) -> dict[str, Any]:
    text = transcript.lower()
    events: list[dict[str, Any]] = []
    event_time = _guess_event_time(text, now)
    meal = _meal_from_text(text)
    food = None
    for word in ("porridge", "chicken", "toast", "soup", "milky drink"):
        if word in text:
            food = word
            break
    amount = "barely" if "barely" in text or "picked at" in text else "refused" if "refused" in text or "wouldn't eat" in text else None
    place = "lounge" if "lounge" in text else "bedroom" if "bedroom" in text else "garden" if "garden" in text else None
    sequence = (
        "after_meal"
        if (
            "after eat" in text
            or "after eating" in text
            or "after supper" in text
            or "after breakfast" in text
            or "after food" in text
            or "then was sick" in text
            or "then sick" in text
            or "then vomit" in text
        )
        else None
    )

    late = re.search(r"(\d+)\s*minutes?\s*late", text)
    if "med" in text or "pill" in text or "donepezil" in text:
        delay = int(late.group(1)) if late else None
        events.append(
            {
                "type": "medication",
                "subtype": "dose_late" if delay or "late" in text else "note",
                "event_time": event_time.isoformat(timespec="minutes"),
                "detail": f"evening medicines {delay} minutes late" if delay else "medicines given",
                "confidence": 0.9 if delay else 0.65,
            }
        )
    if "confus" in text or "recognis" in text or "recognize" in text:
        events.append(
            {
                "type": "symptom",
                "subtype": "confusion",
                "event_time": event_time.isoformat(timespec="minutes"),
                "detail": "evening confusion",
                "confidence": 0.9,
            }
        )
    if "dinner" in text or "appetite" in text or "barely touched" in text:
        events.append(
            {
                "type": "meal",
                "subtype": "appetite_low",
                "event_time": event_time.isoformat(timespec="minutes"),
                "detail": "low appetite",
                "confidence": 0.85,
            }
        )
    if "eaten" in text or "has eat" in text or "ate " in text:
        if not any(e["subtype"] == "appetite_low" for e in events):
            events.append(
                {
                    "type": "meal",
                    "subtype": "eaten",
                    "event_time": event_time.isoformat(timespec="minutes"),
                    "detail": "ate a meal",
                    "confidence": 0.85,
                }
            )
    if "vomit" in text or "was sick" in text or "throwing up" in text:
        events.append(
            {
                "type": "symptom",
                "subtype": "vomiting",
                "event_time": event_time.isoformat(timespec="minutes"),
                "detail": "vomiting after food" if "after" in text or "eaten" in text else "vomiting",
                "confidence": 0.9,
            }
        )
    not_himself = bool(
        re.search(r"not (him|her|them)self", text) or "wasn't himself" in text or "wasnt himself" in text
        or "not himself" in text or "not herself" in text
    )
    moodish = any(
        word in text
        for word in ("tearful", "upset", "withdrawn", "crying", "cried", "sad", "low mood", "tear")
    )
    if not_himself:
        events.append(
            {
                "type": "mood",
                "subtype": "not_himself",
                "event_time": event_time.isoformat(timespec="minutes"),
                "detail": "not himself",
                "confidence": 0.8,
            }
        )
    elif moodish:
        events.append(
            {
                "type": "mood",
                "subtype": "mood_low",
                "event_time": event_time.isoformat(timespec="minutes"),
                "detail": "low mood",
                "confidence": 0.88,
            }
        )
    if any(
        phrase in text
        for phrase in ("up in the night", "up at 2", "up at two", "didn't sleep", "did not sleep", "settled late", "awake")
    ):
        events.append(
            {
                "type": "sleep",
                "subtype": "awake_night" if "up" in text or "awake" in text or "sleep" in text else "settled_late",
                "event_time": event_time.isoformat(timespec="minutes"),
                "detail": "up in the night" if "up" in text or "awake" in text else "settled late",
                "confidence": 0.85,
            }
        )
    if "fall" in text or "fell" in text or "tripped" in text or "on the floor" in text:
        events.append(
            {
                "type": "incident",
                "subtype": "fall",
                "event_time": event_time.isoformat(timespec="minutes"),
                "detail": "fall or trip",
                "confidence": 0.86,
            }
        )
    if "door open" in text or "door closed" in text or "tea with milk" in text or "prefers" in text or "likes the" in text:
        detail = "prefers the bedroom door open" if "door" in text else "tea with milk" if "tea" in text else "preference noted"
        events.append(
            {
                "type": "preference",
                "subtype": "about_me",
                "event_time": event_time.isoformat(timespec="minutes"),
                "detail": detail,
                "confidence": 0.8,
            }
        )
    if not events:
        events.append(
            {
                "type": "note",
                "subtype": "note",
                "event_time": event_time.isoformat(timespec="minutes"),
                "detail": transcript[:180],
                "confidence": 0.55,
            }
        )

    late_minutes = int(late.group(1)) if late else None
    for event in events:
        if event["type"] in {"meal", "symptom"}:
            if meal:
                event["meal"] = meal
            if food:
                event["food"] = food
            if amount and event["type"] == "meal":
                event["amount"] = amount
            if sequence:
                event["sequence"] = sequence
        if place:
            event["place"] = place
        if event["type"] == "medication" and late_minutes:
            event["minutes_late"] = late_minutes
        if event["subtype"] == "eaten" and food:
            event["detail"] = f"ate {food}" + (f" at {meal}" if meal else "")
        if event["subtype"] == "vomiting" and (sequence or food):
            event["detail"] = f"vomiting after {food}" if food else "vomiting after food"

    primary = events[0]
    guess = None
    if primary["type"] != "note" and float(primary.get("confidence") or 0) < 0.75:
        guess = f"Sounds like {primary['type'].replace('_', ' ')}"
    confirmation = "Logged: " + "; ".join(f"{e['type']} ({e['subtype']})" for e in events) + "."
    return {
        "events": events,
        "clarifying_question": None,
        "confirmation": strip_advice(confirmation),
        "guess": guess,
    }


def ollama_extract(transcript: str, now: datetime) -> dict[str, Any]:
    prompt = (
        f"Now is {now.isoformat(timespec='minutes')}. "
        f"Carer said: {transcript}"
    )
    try:
        data = chat_json(prompt, EXTRACT_SYSTEM)
    except Exception:
        return heuristic_extract(transcript, now)
    if not isinstance(data, dict) or "events" not in data:
        return heuristic_extract(transcript, now)
    data["confirmation"] = strip_advice(str(data.get("confirmation") or "Logged."))
    for event in data.get("events") or []:
        if isinstance(event, dict):
            event.update(sanitize_slots(event))
    if "guess" not in data:
        events = data.get("events") or []
        primary = events[0] if events else {}
        conf = float(primary.get("confidence") or 1)
        if primary.get("type") and primary.get("type") != "note" and conf < 0.75:
            data["guess"] = f"Sounds like {str(primary['type']).replace('_', ' ')}"
        else:
            data["guess"] = None
    return data


def parse_event_time(value: Any, fallback: datetime) -> datetime:
    if not value:
        return fallback
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", ""))
    except ValueError:
        return fallback


def split_corridor(transcript: str, names: list[str]) -> tuple[list[tuple[str, str]], str | None]:
    """Split a wing dump into (person_name, slice) using known names. Longest names first."""
    if not transcript.strip() or not names:
        return [], transcript.strip() or None
    ordered = sorted({n for n in names if n}, key=len, reverse=True)
    matches: list[tuple[int, int, str]] = []
    lower = transcript
    for name in ordered:
        for found in re.finditer(rf"\b{re.escape(name)}\b", lower, flags=re.IGNORECASE):
            matches.append((found.start(), found.end(), name))
    if not matches:
        return [], transcript.strip()
    matches.sort(key=lambda row: row[0])
    deduped: list[tuple[int, int, str]] = []
    for start, end, name in matches:
        if deduped and start < deduped[-1][1]:
            continue
        deduped.append((start, end, name))
    unmatched = transcript[: deduped[0][0]].strip() or None
    slices: list[tuple[str, str]] = []
    for i, (start, _end, name) in enumerate(deduped):
        stop = deduped[i + 1][0] if i + 1 < len(deduped) else len(transcript)
        chunk = transcript[start:stop].strip(" .;,\n")
        if chunk:
            slices.append((name, chunk))
    return slices, unmatched
