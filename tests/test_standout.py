from datetime import datetime, timedelta


def _named(client, name):
    return next(p for p in client.get("/people").json() if p["name"] == name)


def _ravi(client):
    return next(u for u in client.get("/users").json() if u["role"] == "family")


def test_tearful_is_mood(client):
    frank = _named(client, "Frank")
    body = client.post(
        "/log",
        json={"transcript": "He was tearful in the lounge after supper.", "use_heuristic": True, "person_id": frank["id"]},
    ).json()
    assert body["emergency"] is False
    assert any(e["type"] == "mood" for e in body["events"])
    assert any(e["subtype"] == "mood_low" for e in body["events"])


def test_not_himself_extracts(client):
    frank = _named(client, "Frank")
    body = client.post(
        "/log",
        json={"transcript": "Frank wasn't himself this evening.", "use_heuristic": True, "person_id": frank["id"]},
    ).json()
    assert any(e["subtype"] == "not_himself" or e["type"] == "mood" for e in body["events"])
    assert "usually" in (body.get("confirmation") or "").lower() or any(
        f["subtype"] == "not_himself" for f in body.get("flags", [])
    )


def test_note_still_saves(client):
    joyce = _named(client, "Joyce")
    body = client.post(
        "/log",
        json={"transcript": "Sat with her in the garden.", "use_heuristic": True, "person_id": joyce["id"]},
    ).json()
    assert body["events"]
    assert body["events"][0]["raw_transcript"]


def test_board_lists_everyone_worst_first(client):
    board = client.get("/board").json()
    names = [p["name"] for p in board["people"]]
    assert len(names) == 10
    assert set(names) == {
        "Dad",
        "Able",
        "Margaret",
        "Harold",
        "Joyce",
        "Ibrahim",
        "Evelyn",
        "Frank",
        "Aisha",
        "George",
    }
    assert board["people"][0]["name"] in {"Able", "Dad", "Frank"}
    assert board["people"][-1]["score"] == 0
    assert "nurse" not in board or board.get("nurse") in (None, "")
    assert "Margaret" in board["risks"]


def test_stale_open_shift_does_not_hide_lines(client):
    started = (datetime.utcnow() - timedelta(hours=20)).replace(microsecond=0)
    assert client.post("/shifts", json={"started_at": started.isoformat()}).status_code == 200
    board = client.get("/board").json()
    frank = next(p for p in board["people"] if p["name"] == "Frank")
    assert frank["line"]


def test_goodluck_is_assigned_dad(client):
    users = client.get("/users").json()
    goodluck = next(u for u in users if u["display_name"] == "Goodluck")
    dad = _named(client, "Dad")
    assert goodluck["assigned_person_id"] == dad["id"]
    abena = next(u for u in users if u["display_name"] == "Abena")
    assert abena.get("assigned_person_id") in (None, 0)


def test_admin_login_and_add(client):
    assert client.post("/admin/login", json={"password": "0000"}).status_code == 403
    assert client.post("/admin/login", json={"password": "1234"}).json()["ok"] is True
    headers = {"X-Demo-Role": "admin"}
    person = client.post(
        "/admin/people",
        json={"name": "Nora", "age": 81, "risks": "walks with a frame"},
        headers=headers,
    )
    assert person.status_code == 200
    assert person.json()["name"] == "Nora"
    staff = client.post(
        "/admin/staff",
        json={"display_name": "Priya", "assigned_person_id": person.json()["id"]},
        headers=headers,
    )
    assert staff.status_code == 200
    assert staff.json()["role"] == "support_worker"
    assert staff.json()["assigned_person_id"] == person.json()["id"]
    names = {p["name"] for p in client.get("/people").json()}
    assert "Nora" in names
    workers = {u["display_name"] for u in client.get("/users").json() if u["role"] == "support_worker"}
    assert "Priya" in workers
    denied = client.post("/admin/people", json={"name": "Blocked"}, headers={"X-Demo-Role": "support_worker"})
    assert denied.status_code == 403


def test_family_forbidden_on_board(client):
    response = client.get("/board", headers={"X-Demo-Role": "family"})
    assert response.status_code == 403


def test_corridor_splits_two_people(client):
    before = {row["id"]: row["line"] for row in client.get("/board").json()["people"]}
    body = client.post(
        "/log/corridor",
        json={"transcript": "Able up at two. Frank was tearful.", "use_heuristic": True},
    ).json()
    assert body["ok"] is True
    names = {s["person_name"] for s in body["slices"]}
    assert names == {"Able", "Frank"}
    after = client.get("/board").json()["people"]
    able = next(p for p in after if p["name"] == "Able")
    frank = next(p for p in after if p["name"] == "Frank")
    assert able["line"]
    assert frank["line"]
    assert able["id"] in { _named(client, "Able")["id"] }
    assert before


def test_ravi_logs_dad_not_able(client):
    ravi = _ravi(client)
    dad = _named(client, "Dad")
    able = _named(client, "Able")
    ok = client.post(
        "/log",
        json={
            "transcript": "He barely ate his toast.",
            "use_heuristic": True,
            "person_id": dad["id"],
            "logger_id": ravi["id"],
        },
        headers={"X-Demo-Role": "family"},
    )
    assert ok.status_code == 200
    assert ok.json()["events"][0]["source"] == "from_home"
    denied = client.post(
        "/log",
        json={
            "transcript": "Able was sick.",
            "use_heuristic": True,
            "person_id": able["id"],
            "logger_id": ravi["id"],
        },
        headers={"X-Demo-Role": "family"},
    )
    assert denied.status_code == 403


def test_staff_cannot_set_from_home(client):
    dad = _named(client, "Dad")
    response = client.post(
        "/log",
        json={
            "transcript": "He ate lunch.",
            "use_heuristic": True,
            "person_id": dad["id"],
            "source": "from_home",
        },
    )
    assert response.status_code == 400


def test_family_people_only_dad(client):
    people = client.get("/people", headers={"X-Demo-Role": "family"}).json()
    assert [p["name"] for p in people] == ["Dad"]


def test_gp_brief_has_two_authors(client):
    dad = _named(client, "Dad")
    brief = client.post("/briefs", json={"person_id": dad["id"]}).json()
    md = brief["markdown"]
    assert "## From the shift" in md
    assert "## From home" in md
    assert "Ravi" in md
    assert "[log " in md


def test_hospital_return_flag_on_dad(client):
    dad = _named(client, "Dad")
    flags = client.get(f"/flags?person_id={dad['id']}").json()
    assert any(f["kind"] == "hospital_return" or f["subtype"] == "hospital_return" for f in flags)


def test_ravi_is_family_not_a_worker(client):
    users = client.get("/users").json()
    staff = {u["display_name"] for u in users if u["role"] == "support_worker"}
    assert staff == {"Goodluck", "Abena", "Pelumi", "Okunola", "Kemi"}
    assert any(u["display_name"] == "Ravi" and u["role"] == "family" for u in users)


def test_staff_login_needs_password(client):
    goodluck = next(u for u in client.get("/users").json() if u["display_name"] == "Goodluck")
    bad = client.post("/staff/login", json={"user_id": goodluck["id"], "password": "0000"})
    assert bad.status_code == 403
    ok = client.post("/staff/login", json={"user_id": goodluck["id"], "password": "1234"})
    assert ok.status_code == 200
    assert ok.json()["display_name"] == "Goodluck"
    assert ok.json()["role"] == "support_worker"


def test_family_login_needs_password(client):
    dad = _named(client, "Dad")
    able = _named(client, "Able")
    bad = client.post("/family/login", json={"person_id": dad["id"], "password": "0000"})
    assert bad.status_code == 403
    missing = client.post("/family/login", json={"person_id": able["id"], "password": "1234"})
    assert missing.status_code == 404
    ok = client.post("/family/login", json={"person_id": dad["id"], "password": "1234"})
    assert ok.status_code == 200
    assert ok.json()["display_name"] == "Ravi"
    assert ok.json()["family_person_id"] == dad["id"]


def test_corridor_needs_a_name(client):
    response = client.post("/log/corridor", json={"transcript": "Up at two and tearful."})
    assert response.status_code == 400
    assert response.json()["detail"] == "No names heard. Say the name, then what happened."
