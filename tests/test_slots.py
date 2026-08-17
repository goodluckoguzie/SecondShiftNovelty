from datetime import datetime

from app.extractor import heuristic_extract
from app.slots import pack_slots, sanitize_slots


def test_heuristic_keeps_food_time_and_sequence(client):
    joyce = next(p["id"] for p in client.get("/people").json() if p["name"] == "Joyce")
    response = client.post(
        "/log",
        json={
            "transcript": "Joyce ate porridge at supper then was sick.",
            "use_heuristic": True,
            "person_id": joyce,
        },
    )
    assert response.status_code == 200
    events = response.json()["events"]
    meal = next(e for e in events if e["subtype"] == "eaten")
    vomit = next(e for e in events if e["subtype"] == "vomiting")
    assert meal["slots"]["food"] == "porridge"
    assert meal["slots"]["meal"] == "supper"
    assert "porridge" in meal["detail"]
    assert vomit["slots"]["sequence"] == "after_meal"
    meal_then = next(f for f in response.json()["flags"] if f["kind"] == "meal_then_symptom")
    assert "porridge" in meal_then["message"]


def test_ollama_slots_are_stored(client, monkeypatch):
    def fake(_transcript, _now):
        return {
            "events": [
                {
                    "type": "meal",
                    "subtype": "eaten",
                    "event_time": "2026-08-15T19:10:00",
                    "detail": "ate porridge at supper",
                    "meal": "supper",
                    "food": "porridge",
                    "amount": "all",
                    "confidence": 0.9,
                },
                {
                    "type": "symptom",
                    "subtype": "vomiting",
                    "event_time": "2026-08-15T19:30:00",
                    "detail": "sick 20 minutes after porridge",
                    "meal": "supper",
                    "food": "porridge",
                    "sequence": "after_meal",
                    "confidence": 0.9,
                },
            ],
            "confirmation": "Logged supper and vomiting.",
            "guess": None,
        }

    monkeypatch.setattr("app.main.ollama_extract", fake)
    able = next(p["id"] for p in client.get("/people").json() if p["name"] == "Able")
    response = client.post(
        "/log",
        json={"transcript": "Able ate porridge at supper then was sick.", "person_id": able},
    )
    assert response.status_code == 200
    meal = next(e for e in response.json()["events"] if e["subtype"] == "eaten")
    assert meal["slots"]["food"] == "porridge"
    assert meal["slots"]["amount"] == "all"
    assert "19:10" in meal["event_time"]


def test_sanitize_drops_invented_and_counts():
    assert sanitize_slots({"food": "null", "meal": "brunch", "minutes_late": "nope"}) == {}
    assert "food" not in sanitize_slots({"food": "unknown"})
    packed = pack_slots({"meal": "dinner", "food": "chicken", "amount": "half"})
    assert '"meal": "supper"' in packed or '"meal":"supper"' in packed.replace(" ", "")


def test_heuristic_up_at_two_is_02_00():
    now = datetime(2026, 8, 15, 22, 10)
    extracted = heuristic_extract("Able up at two.", now)
    sleep = next(e for e in extracted["events"] if e["type"] == "sleep")
    assert "02:00" in sleep["event_time"]
    assert sleep["event_time"].startswith("2026-08-16")
