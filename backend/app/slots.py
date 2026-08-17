from __future__ import annotations

import json
from typing import Any

MEALS = {"breakfast", "lunch", "dinner", "supper", "snack"}
AMOUNTS = {"all", "half", "refused", "barely"}
SEQUENCES = {"after_meal", "before_meds", "after_meds"}


def sanitize_slots(item: dict[str, Any] | None) -> dict[str, Any]:
    if not item:
        return {}
    out: dict[str, Any] = {}
    meal = str(item.get("meal") or "").strip().lower()
    if meal == "dinner":
        meal = "supper"
    if meal in MEALS:
        out["meal"] = meal
    food = str(item.get("food") or "").strip()
    if food and food.lower() not in {"null", "none", "unknown", "n/a"}:
        out["food"] = food[:80]
    amount = str(item.get("amount") or "").strip().lower()
    if amount in AMOUNTS:
        out["amount"] = amount
    place = str(item.get("place") or "").strip()
    if place and place.lower() not in {"null", "none", "unknown"}:
        out["place"] = place[:40]
    sequence = str(item.get("sequence") or "").strip().lower()
    if sequence in SEQUENCES:
        out["sequence"] = sequence
    late = item.get("minutes_late")
    try:
        minutes = int(late)
        if 0 < minutes < 24 * 60:
            out["minutes_late"] = minutes
    except (TypeError, ValueError):
        pass
    return out


def pack_slots(item: dict[str, Any] | None) -> str:
    slots = sanitize_slots(item)
    return json.dumps(slots) if slots else ""


def unpack_slots(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return sanitize_slots(data) if isinstance(data, dict) else {}
