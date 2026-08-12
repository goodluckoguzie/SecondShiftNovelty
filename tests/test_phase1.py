RAVI = "Gave dad his 8pm meds, 40 minutes late. More confused again this evening, third time this week."


def test_text_fallback_logs_events(client):
    response = client.post("/log", json={"transcript": RAVI, "use_heuristic": True})
    assert response.status_code == 200
    body = response.json()
    assert body["emergency"] is False
    subtypes = {e["subtype"] for e in body["events"]}
    assert "dose_late" in subtypes
    assert "confusion" in subtypes
    assert body["confirmation"]


def test_empty_transcript_rejected(client):
    response = client.post("/log", json={"transcript": "  ", "use_heuristic": True})
    assert response.status_code == 400


def test_logged_events_appear_on_timeline(client):
    client.post("/log", json={"transcript": RAVI, "use_heuristic": True})
    events = client.get("/events").json()
    assert any("40 minutes late" in (e["detail"] + e["raw_transcript"]) for e in events)
