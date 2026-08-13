ABLE = "Able has eaten; after eating he was vomiting."


def _able_id(client):
    people = client.get("/people").json()
    return next(p["id"] for p in people if p["name"] == "Able")


def test_people_include_dad_and_able(client):
    names = {p["name"] for p in client.get("/people").json()}
    assert {"Dad", "Able"} <= names
    assert len(names) == 10


def test_five_named_care_workers(client):
    users = client.get("/users").json()
    names = {u["display_name"] for u in users if u["role"] == "support_worker"}
    assert names == {"Goodluck", "Abene", "Pelumi", "Okunola", "Kemi"}


def test_person_isolation(client):
    able = _able_id(client)
    dad_events = client.get("/events").json()
    able_events = client.get(f"/events?person_id={able}").json()
    assert all(e["person_id"] != able for e in dad_events)
    assert all(e["person_id"] == able for e in able_events)
    assert any(e["subtype"] == "dose_late" for e in dad_events)
    assert not any(e["subtype"] == "dose_late" for e in able_events)
    assert any(e["subtype"] == "vomiting" for e in able_events)


def test_able_vomiting_banner_and_evidence(client):
    able = _able_id(client)
    response = client.post(
        "/log",
        json={"transcript": ABLE, "use_heuristic": True, "person_id": able},
    )
    assert response.status_code == 200
    body = response.json()
    subtypes = {e["subtype"] for e in body["events"]}
    assert "vomiting" in subtypes
    assert "eaten" in subtypes
    similar = body["similar"]
    assert any(e["subtype"] == "vomiting" for e in similar)
    flags = body["flags"]
    vomit = next(f for f in flags if f["subtype"] == "vomiting" and f["kind"] == "symptom_recurrence")
    assert len(vomit["evidence_event_ids"]) >= 3
    assert vomit["evidence"]
    assert any("sick" in (e["raw_transcript"] or "").lower() or "vomit" in (e["raw_transcript"] or "").lower() for e in vomit["evidence"])


def test_clinician_cannot_log(client):
    response = client.post(
        "/log",
        json={"transcript": ABLE, "use_heuristic": True},
        headers={"X-Demo-Role": "clinician"},
    )
    assert response.status_code == 403


def test_shift_handover_window(client):
    started = client.post("/shifts", json={"started_at": "2026-08-13T08:00:00", "ended_at": "2026-08-13T14:00:00"})
    assert started.status_code == 200
    shift_id = started.json()["id"]
    able = _able_id(client)
    handover = client.post(
        "/handover",
        json={"name": "Priya", "window": "shift", "shift_id": shift_id, "person_id": able},
    )
    assert handover.status_code == 200
    markdown = handover.json()["markdown"]
    assert "Shift handout" in markdown
    assert "This shift" in markdown
    assert "08:00" in markdown or "8:00" in markdown


def test_family_72h_preset_still_works(client):
    response = client.post("/handover", json={"name": "Priya", "window": "72h"})
    assert "72 hours" in response.json()["markdown"].lower() or "Last 72" in response.json()["markdown"]


def test_able_brief_has_citations(client):
    able = _able_id(client)
    client.post("/log", json={"transcript": ABLE, "use_heuristic": True, "person_id": able})
    brief = client.post("/briefs", json={"person_id": able})
    assert "[log " in brief.json()["markdown"]
    pdf = client.get(f"/briefs/latest.pdf?person_id={able}")
    assert pdf.status_code == 200
    assert pdf.content[:4] == b"%PDF"
