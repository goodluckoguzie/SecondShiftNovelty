def test_rules_module_has_no_ollama_import():
    import app.patterns as patterns
    import inspect

    source = inspect.getsource(patterns)
    assert "ollama" not in source.lower()
    assert "chat_json" not in source


def test_third_confusion_fires_recurrence_and_dose_change(client):
    before = client.get("/flags").json()
    kinds_before = {f["kind"] for f in before}
    assert "symptom_recurrence" not in kinds_before

    response = client.post(
        "/log",
        json={
            "transcript": "More confused again this evening, third time this week.",
            "use_heuristic": True,
        },
    )
    assert response.status_code == 200
    flags = response.json()["flags"]
    recurrence = next(f for f in flags if f["kind"] == "symptom_recurrence")
    assert "3" in recurrence["message"] or "three" in recurrence["message"].lower()
    assert "dose change" in recurrence["message"].lower()
    late = next(f for f in flags if f["kind"] == "late_or_missed_doses")
    assert late
