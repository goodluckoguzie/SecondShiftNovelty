def test_person_view_has_shift_and_changed(client, monkeypatch):
    monkeypatch.setattr("app.person_view.ollama_available", lambda: False)
    people = client.get("/people").json()
    dou = next(p for p in people if p["name"] == "Dou")
    goodluck = next(u for u in client.get("/users").json() if u["display_name"] == "Goodluck")
    view = client.get(f"/person/view?person_id={dou['id']}&user_id={goodluck['id']}").json()
    assert "week_summary" in view
    assert "yesterday_summary" in view
    assert "today" in view
    assert isinstance(view["days"], list)
    assert isinstance(view["essentials"], list)
    assert {item["key"] for item in view["essentials"]} >= {"vomiting", "fall", "medication"}
    assert len(view["stability"]) == 7
    assert view["drafted"] is False


def test_person_view_skips_ollama_until_draft(client, monkeypatch):
    called = []
    monkeypatch.setattr("app.person_view.ollama_available", lambda: True)
    monkeypatch.setattr("app.person_view.chat_json", lambda *a, **k: called.append(1) or {})
    people = client.get("/people").json()
    dou = next(p for p in people if p["name"] == "Dou")
    view = client.get(f"/person/view?person_id={dou['id']}").json()
    assert view["drafted"] is False
    assert called == []


def test_week_summary_uses_ollama_voice(client, monkeypatch):
    monkeypatch.setattr("app.person_view.ollama_available", lambda: True)

    def fake_chat(prompt, system, timeout=45.0):
        assert "Spoken notes" in prompt
        assert "Sick / vomit" not in prompt
        return {
            "week_summary": "He barely touched supper after hospital and evening tablets came late. He seemed more confused in the evenings.",
            "yesterday_summary": "He picked at supper and settled late.",
        }

    monkeypatch.setattr("app.person_view.chat_json", fake_chat)
    people = client.get("/people").json()
    dou = next(p for p in people if p["name"] == "Dou")
    view = client.get(f"/person/view?person_id={dou['id']}&draft=true").json()
    assert "barely touched supper" in view["week_summary"].lower()
    assert "1 times" not in view["week_summary"]
    assert view["drafted"] is True
