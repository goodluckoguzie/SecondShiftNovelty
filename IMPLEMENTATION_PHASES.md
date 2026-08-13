# Second Shift — Implementation Phases

Research → product, broken into phases. **Shipped:** Phases 0–4 + Docker. **Next:** [PLAN_OF_ACTION.md](PLAN_OF_ACTION.md) (Phase 6). Users: unpaid family **and** paid support workers; nurse/GP simple view.

Every phase has: **goal**, **what to build**, **research it rests on**, **done when**, and **out of scope**.

```text
Phase 0  Foundations
Phase 1  Voice → structured care log
Phase 2  Pattern engine
Phase 3  Evidence-cited GP / memory-clinic brief
Phase 4  Demo polish + differentiators
Phase 5  Pitch-only (do not build)
Phase 6  Multi-role: login, shifts, person memory (see PLAN_OF_ACTION.md)
```

---

## Phase 0 — Foundations (hours 0–4)

**Goal:** A runnable repo with the dementia persona, schema, and seed data so later phases are not guessing.

### Build
- Monorepo or simple two-folder layout: `frontend/` (React + Vite + Tailwind) · `backend/` (FastAPI + SQLite)
- Data model:
  - `person_profile` (Dad, 71, dementia, allergies)
  - `medication_schedule` (3 meds; one with `last_changed_at` = Friday dose change)
  - `care_events` (append-only)
  - `pattern_flags` (empty at start)
  - `briefs` (empty at start)
- Seed **6 days** of synthetic dementia logs:
  - evening medicines late ×2
  - evening confusion ×2 (so day-7 live log becomes the 3rd)
  - low appetite ×3–4
- STT spike: mic → transcript on screen (Whisper **or** Web Speech API)
- Persistent UI disclaimer: *not a medical device*

### Research this phase uses
- UK beachhead: dementia (family at home *and* paid staff). Do not rebuild eMAR ([research](Second_Shift_Novelty_Research.md))
- Persona and demo narrative from the engineering spec
- Safety framing: organise notes, draft questions for the GP

### Done when
- `npm run dev` + `uvicorn` both start
- Timeline API returns seed events
- Mic (or typed fallback) prints a transcript

### Out of scope
- Real NHS login, GP Connect, or write to the clinical record

---

## Phase 1 — Voice → structured care log (hours 4–10)

**Goal:** Free speech becomes typed care events the rest of the system can trust.

### Build
- Push-to-talk (plus text input fallback)
- LLM extractor with **strict JSON** schema:
  - `type`: medication | symptom | meal | sleep | mood | incident | note
  - dementia-relevant subtypes: `dose_late`, `dose_missed`, `confusion`, `agitation`, `appetite_low`, …
  - `event_time`, `detail`, `raw_transcript`, `confidence`
- Store events in SQLite; show **Timeline** screen (reverse chronological, icons per type)
- Short confirmation reply: “Logged: evening medicines at 20:40, confusion noted.”
- If confidence &lt; 0.7 on medicine name or missed dose → ask **one** clarifying question
- Hard prompt rule: **no diagnosis, triage, or treatment advice**

### Research this phase uses
- Gap vs Jointly / Share2Care: they are tap-based; voice-first for the carer is the wedge
- Academic carers tools are Q&A only; this phase is **operational logging**, not chat support

### Done when
- Live utterance creates 1+ `care_events` rows and appears on Timeline
- Text fallback works without a mic (demo insurance)

### Out of scope
- Pattern charts, PDF brief, multi-user accounts

---

## Phase 2 — Pattern engine (hours 10–16)

**Goal:** Catch what an exhausted carer misses. Deterministic rules only — the LLM never counts.

### Build
- Rules over the care log + medication schedule:
  1. **Late / missed dose:** ≥2 late or missed in rolling 7 days
  2. **Symptom recurrence:** same subtype ≥3 times in 7 days (confusion for dementia demo)
  3. **Dose-change correlation:** if recurrence starts after `last_changed_at`, store that date on the flag
  4. **Declining trend (optional P0):** meal / sleep / mood down over ≥4 entries
- Persist typed `pattern_flags`; LLM may **describe** them, never recompute them
- Conversational note when a flag fires: *“Third confusion episode since Friday’s dose change. Flagged for the GP brief.”*
- Escalation language stays observational (never “this could be serious”)

### Research this phase uses
- Closest competitors stop at logging or weekly digests; they do not flag dose-change clusters
- BMJ Open work on unpaid carers and medicines: carers do the work, systems under-support them
- Safety / MHRA stance: observational flags + draft questions, not triage

### Done when
- Day-7 live confusion log crosses the ≥3 threshold and creates a visible flag
- Flag text mentions the Friday dose change

### Out of scope
- Pretty chart UI (can wait until Phase 4)
- Any clinical scoring or diagnosis language

---

## Phase 3 — Evidence-cited GP / memory-clinic brief (hours 16–24)

**Goal:** Close the home → GP loop. This is the novelty centrepiece.

### Build
- One-tap **Generate brief**
- Input to the LLM = **structured payload only** (events + pattern_flags + schedule), not raw chat history as the sole source of truth
- Fixed PDF / markdown sections:
  1. Patient snapshot
  2. Medicines this period (on time / late / missed + dates)
  3. Symptom episodes (chronological, each with citation)
  4. Notable patterns (copied from pattern engine)
  5. Suggested questions for the GP / memory clinic (3–5)
  6. Appendix: timestamped source quotes
- Render to downloadable PDF (HTML → PDF or browser print)
- Pre-cache one brief PDF as stage failover

### Research this phase uses
- Heidi / Tortus capture the appointment; CareCurrent / KinKeeper-style briefs are not voice-evidence from home
- UK pitch: 10-minute GP appointments need one page of evidence
- Evidence citations = trust differentiator for NHS-minded judges

### Done when
- Full role-play works end-to-end: speak → flag → PDF with at least one `[log …]` citation
- Brief is usable even if ugly

### Out of scope
- Doctor-facing portal or emailing the GP automatically

---

## Phase 4 — Demo polish and differentiators (hours 24–40)

**Goal:** Make the demo unforgettable and add the signature UK features if time remains.

### Build (in order)
1. **Pattern chart UI** — 7-day confusion bars + dose-change marker (the “wow” visual)
2. **Voice UX polish** — confirmations, loading states, mobile layout
3. **Safety pack**
   - Emergency keyword screen → call 999 (no LLM)
   - Output filter for advice-shaped phrasing
   - Privacy copy: discard audio after STT, export/delete
4. **Fallback ladder** (rehearse all): live mic → pre-recorded clip → typed input → cached PDF
5. **P1 if time:** **Handover brief** (family 72-hour preset; staff version follows the actual shift)
6. **P1 if time:** Soft escalation prompt — “Want me to add this to the urgent section of the brief?” + static NHS 111 / local nurse-line text

### Research this phase uses
- Handover brief = strongest unused novelty from the research
- Loc-demcare / UK GDPR: privacy narrative on one slide
- Share2Care occupies NHS-record upload; we stay “carer brings PDF”

### Done when
- Demo rehearsed ≥5 times
- Backup video recorded
- Slides ready: problem, live demo, UK competitor table, architecture, safety

### Out of scope
- Production auth, multi-tenant hosting, app-store release

---

## Phase 5 — Pitch only (do not build)

Mention on slides; do not spend build hours here.

| Idea | Why research likes it | Why not now |
|---|---|---|
| Carer-burden self check-in | Carers UK: high stress, worsening health | Dilutes demo focus |
| Multi-carer accounts + push | Jointly / Share2Care strength | Needs auth and time |
| Full doctor / memory-clinic portal | Nice long-term | Phase 6 is a *simple view* only; not NHS IG |
| On-device / local LLM | Strong UK privacy story | Hard in 48 hours |
| Stroke / Parkinson’s / frailty packs | Later verticals after dementia | Beachhead discipline |
| NHS login write-back | Share2Care already there | Liability + integration risk |
| Full eMAR / Nourish clone | Paid-staff incumbents already here | We own speech → person memory → handout |

---

## Phase 6 — Next build (novelty first, then costume)

Full plan: [PLAN_OF_ACTION.md](PLAN_OF_ACTION.md).

**Goal:** Speech → cited page for the person who is not in Birdie/Nourish. Do not bury that behind login.

### Build (in order) — implemented
0. Theme + split UI (Dad demo still works)  
1. Person-first schema + Able seed  
2. Similar-last-week banner, tap-to-quote, `POST /log/audio`  
3. Handover **screen** + shift window (72h family preset)  
4. Fake login + shared nurse/doctor view (`X-Demo-Role`; Record now opens Talk)  

### Out of scope
eMAR, task lists, rostering, 11-table DSCR, AuditLog, diagnosing in the banner, separate nurse vs doctor apps.

---

## Phase map (who does what)

Assume 4 people. Collapse roles if fewer.

| Role | Owns |
|---|---|
| Voice + frontend | Talk screen, Timeline, Patterns chart, mobile UX |
| Agent + extraction | STT, LLM JSON schema, confirmations, clarifying questions |
| Patterns + PDF | Rules engine, seed data, brief template, PDF render |
| Demo + pitch | Script, slides, seed story, backup video, fallbacks |

---

## Milestone checklist

| Phase | Exit criteria |
|---|---|
| 0 | Seeded dementia DB + mic/text transcript on screen |
| 1 | Voice or text → events on Timeline |
| 2 | Live confusion log fires recurrence + dose-change flag |
| 3 | One-tap evidence-cited PDF |
| 4 | Rehearsed demo + chart + safety + backups |
| 5 | Pitch mentions only (NHS write-back, full eMAR) |
| 6 | Fake login, person-first DB, shift handout, nurse/GP view ([plan](PLAN_OF_ACTION.md)) |

---

## Suggested calendar (48-hour hackathon)

| Block | Phase |
|---|---|
| Hours 0–4 | Phase 0 |
| Hours 4–10 | Phase 1 |
| Hours 10–16 | Phase 2 |
| Hours 16–24 | Phase 3 (ugly brief OK) |
| Hours 24–32 | Phase 4 chart + PDF polish |
| Hours 32–40 | Phase 4 handover / guardrails / fallbacks |
| Hours 40–48 | Rehearse, backup video, slides |

If behind at hour 24: **skip handover**, keep chart + safety + cached PDF. The closed loop (voice → pattern → brief) wins; extras are polish.

---

## Research → phase quick map

| Research finding | Implementation phase |
|---|---|
| Dementia at home is the beachhead | Phase 0 persona + seed data |
| Voice-first for the carer is unserved | Phase 1 |
| Competitors lack pattern detection | Phase 2 |
| Nobody connects home speech to the GP brief | Phase 3 |
| Evidence citations build NHS trust | Phase 3 |
| Family 72h handover (preset) | Phase 4 (P1) |
| Staff handover follows the shift (6h / 12h) | Phase 6 |
| Memory stays with the person when staff change | Phase 6 |
| Simple nurse/GP view | Phase 6 |
| Not a medical device / UK GDPR | Phase 0 disclaimer + Phase 4 safety |
| NHS write-back / full eMAR | Phase 5 (pitch only; do not build) |
