def test_brief_contains_citation_and_dose_change(client):
    client.post(
        "/log",
        json={
            "transcript": "More confused again this evening, third time this week.",
            "use_heuristic": True,
        },
    )
    response = client.post("/briefs")
    assert response.status_code == 200
    markdown = response.json()["markdown"]
    assert "[log " in markdown
    assert "dose change" in markdown.lower() or "7 Aug" in markdown or "07 Aug" in markdown
    pdf = client.get("/briefs/latest.pdf")
    assert pdf.status_code == 200
    assert pdf.headers["content-type"].startswith("application/pdf")
    assert pdf.content[:4] == b"%PDF"
