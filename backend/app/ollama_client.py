from __future__ import annotations

import json
from typing import Any

import httpx

from .config import OLLAMA_HOST, OLLAMA_MODEL

EXTRACT_SYSTEM = """You are a care-log extraction engine for whoever is recording (family or support worker) for a person with dementia in the UK.
Unpack the spoken sentence into facts. Output strict JSON only.
Never give medical advice, diagnosis, triage, or treatment suggestions.
Never count how many times something happened this week. Never invent food, times, amounts, or places that were not said.
If a medication time is ambiguous, set confidence below 0.7.
Resolve relative times using "Now is" in the user message ("at two" at night is 02:00, "8pm" is 20:00). If you cannot resolve a time, set event_time null.

JSON shape:
{"events":[{"type":"medication|symptom|meal|sleep|mood|incident|preference|note","subtype":"dose_late|dose_missed|confusion|agitation|appetite_low|vomiting|eaten|mood_low|not_himself|awake_night|settled_late|fall|about_me|note","event_time":"ISO-8601 if known else null","detail":"short UK English including food and time if they were said","meal":"breakfast|lunch|supper|snack|null","food":"what they ate if said else null","amount":"all|half|refused|barely|null","minutes_late":null,"place":"lounge|bedroom|garden|null","sequence":"after_meal|before_meds|after_meds|null","confidence":0.0}],"clarifying_question":null,"confirmation":"short UK English confirmation","guess":null}
"""

QUESTIONS_SYSTEM = """You draft 3 to 5 short questions a family carer can ask a GP or memory clinic.
Use only the structured evidence provided. Do not diagnose. Output JSON: {"questions":["..."]}
"""

ASK_SYSTEM = """You answer a UK support worker who is asking about one person.
You are given Python counts plus that person's stored care notes.
Use the counts. Do not recount. Do not invent food, times, or events.
If the counts say 0 meal notes for the day they asked about, the answer is that they have not eaten according to the record. Ask the worker to confirm.
Do not answer only "not in the notes" when the counts already cover the question. Zero logs for that day is the answer.
Never diagnose, triage, or give medical advice.
Cite notes by their id in cite_ids.
Output JSON only: {"answer":"short UK English","cite_ids":[1],"in_notes":true}
"""


def _loads_json(content: str) -> dict[str, Any]:
    text = (content or "").strip()
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            data = json.loads(text[start : end + 1])
            return data if isinstance(data, dict) else {}
        raise


def chat_json(prompt: str, system: str, model: str | None = None, timeout: float = 120.0) -> dict[str, Any]:
    payload = {
        "model": model or OLLAMA_MODEL,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }
    with httpx.Client(timeout=timeout) as client:
        response = client.post(f"{OLLAMA_HOST}/api/chat", json=payload)
        response.raise_for_status()
        content = response.json()["message"]["content"]
    return _loads_json(content)


def ollama_available() -> bool:
    try:
        with httpx.Client(timeout=2.0) as client:
            return client.get(f"{OLLAMA_HOST}/api/tags").status_code == 200
    except Exception:
        return False
