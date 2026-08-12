def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert "not a medical device" in body["disclaimer"].lower()


def test_profile_seeded(client):
    response = client.get("/profile")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Dad"
    assert body["age"] == 71
    assert body["conditions"] == "dementia"
    assert len(body["medications"]) == 3
    donepezil = next(m for m in body["medications"] if m["name"] == "Donepezil")
    assert donepezil["last_changed_at"].startswith("2026-08-07")


def test_events_seeded(client):
    response = client.get("/events")
    assert response.status_code == 200
    events = response.json()
    assert len(events) >= 6
    types = {e["type"] for e in events}
    assert "medication" in types
    assert "symptom" in types
    assert "meal" in types
    confusions = [e for e in events if e["subtype"] == "confusion"]
    assert len(confusions) == 2
