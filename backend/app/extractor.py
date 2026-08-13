from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Callable

from .ollama_client import EXTRACT_SYSTEM, chat_json
from .safety import strip_advice

ExtractFn = Callable[[str, datetime], dict[str, Any]]


def heuristic_extract(transcript: str, now: datetime) -> dict[str, Any]:
    text = transcript.lower()
    events: list[dict[str, Any]] = []
    event_time = now

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

    low = any(e["confidence"] < 0.7 for e in events)
    confirmation = "Logged: " + "; ".join(f"{e['type']} ({e['subtype']})" for e in events) + "."
    return {
        "events": events,
        "clarifying_question": "Which medicine was that?" if low else None,
        "confirmation": strip_advice(confirmation),
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
