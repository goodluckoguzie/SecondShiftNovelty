# Second Shift — Stand-out build plan

Five features. One brand. Do not add eMAR, rota, or a CQC dashboard.

**Brand still:** a spoken sentence becomes a cited page for the person who is not in the provider app.

**Order is the design.** Tags make mood real. Mood and last-shift events make “what changed” real. “What changed” is the morning board. About Me rides the same confirm chips. Family is the same person record with a second writer.

---

## What we already have (do not rebuild)

| Piece | Today |
|---|---|
| Speech → text | Whisper, then show **What you said** |
| Tags | Heuristic keywords, or Ollama. Phone uses heuristic. Mood/sleep almost never fire |
| Store | `CareEvent` with `type`, `subtype`, `raw_transcript`, `logger_id`, `person_id` |
| Watch | Rules on late meds, confusion, appetite, vomiting |
| Handout | Shift window or 72h PDF. Still a list of every event |
| Who | “On shift” (any of 5 workers, any person) or Nurse/GP (read only) |

Family and staff can already write to the same SQLite person **if** family pretends to be a worker. That is not the product. Phase 5 names it.

---

## Shared rules (every phase)

1. Quote is ground truth. Tag is a filing label the human can change.
2. Python counts patterns. The LLM never counts “three times this week.”
3. Not a medical device. No diagnosis, no NEWS2, no NHS write-back.
4. One person on screen at a time. Agency staff get 30 seconds, not a 40-field plan.
5. Tests before the next phase. Demo sentence for each phase lives in seed + pytest.

**Locked tag set** (type → subtype):

| type | subtype |
|---|---|
| medication | dose_late, dose_missed, note |
| symptom | confusion, vomiting, agitation |
| meal | eaten, appetite_low |
| mood | mood_low |
| sleep | settled_late, awake_night, note |
| incident | fall, note |
| preference | about_me |
| note | note |

UI chips use the **type** (Medicines, Mood, Sleep, Meal, Symptom, About them, Note). Subtype stays in the event for Watch and the GP page.

---

## Phase 1 — Confirm the tag after speech

**Why first.** “Tearful” is a Note today because the phone path only looks for meds / confuse / ate / vomit. Without confirm chips, every later screen files the wrong thing.

**User loop**

1. Speak → Stop.
2. See **What you said** immediately (already shipped).
3. See one row of chips, guessed from the sentence. More than one chip if the sentence has two facts (late meds **and** tearful).
4. Tap a chip to correct. Tap **Save log**. Only then write to the database.

Do **not** save a wrong tag and patch it later. Agency staff will walk away before they edit History.

**Backend**

- Expand `heuristic_extract` in `backend/app/extractor.py`:
  - mood: tearful, upset, withdrawn, low mood, sad, crying
  - sleep: settled late, up in the night, didn’t sleep, door (only if sleep context — door alone is Phase 4)
  - incident: fall, on the floor, tripped
- Keep existing meds / confusion / meal / vomit.
- New `POST /extract` `{ transcript }` → `{ events, transcript }`. No database write.
- `POST /log` accepts optional `events: [...]`. If present, store those (after confirm). If absent, extract as now (typed path can stay one-shot).
- Typed log: after Save, show the same chips if confidence &lt; 0.7, else save as today.

**Frontend**

- `TalkScreen`: after `mic-heard` / extract, render chips under the quote. Status goes `writing` → `check` → Save.
- Native `App.js`: transcribe → `POST /extract` → `mic-heard` with events → user confirms in WebView → `POST /log` with events. Do not auto-save on stop.
- `labels.js`: Mood, Sleep, About them.

**Demo line**

> He was tearful in the lounge after supper.

Must land as **Mood**, not Note, after one tap if the guess is wrong.

**Tests**

- Heuristic: tearful → `mood` / `mood_low`.
- `POST /extract` does not create a `CareEvent`.
- `POST /log` with overridden `type: mood` stores mood.
- History filter **Mood** returns it.

**Done when** you can speak that line on the phone, see the quote, see Mood (or tap Mood), Save, and History shows Low mood with **See what was said**.

---

## Phase 2 — 30-second “what changed” (agency demo)

**Why this is the stand-out screen.** 29% nursing-home turnover. A new worker will not open Watch, History, and the PDF. They open **one person** and need three facts.

**User loop**

1. Who → person (Able).
2. Land on **What changed**, not an empty Talk mic.
3. Three blocks, nothing else:
   - **Last 12 hours** (or this shift if one is open) — up to 5 lines, tap quote
   - **Still open** — existing Watch flags, max 3, tap Why
   - **About them** — Phase 4; until then a one-line placeholder from profile if we have it
4. Primary button underneath: **Log what happened** → today’s Talk.

Do not add a fifth nav tab. This **is** Talk’s first paint. Mic moves below the fold or behind the button.

**Backend**

- `GET /changed?person_id=&hours=12`
  - `recent`: events in window, newest first, cap 5
  - `flags`: current `PatternFlag`s, cap 3
  - `about`: preference events / about_me (empty until Phase 4)
  - `since`: ISO start of window
- Reuse `_event_out` and `_flag_out`. No new tables.

**Frontend**

- `ChangedPanel` at top of `TalkScreen` when `!recording && !busy && !transcript`.
- Clinical read-only: same panel, no Log button.
- Copy: “What changed for Able” / “Nothing spoken in the last 12 hours. That is not the same as all fine.”

**Seed**

- Able already has vomit-after-food. Add one event **this morning** so the 12-hour block is not empty in a live demo.
- Dad: one late med + confusion in the last 12 hours.

**Tests**

- Able `/changed` includes a vomit flag and at least one recent meal/symptom.
- Empty person (if we add a quiet resident) returns the “not all fine” message, not an empty page.

**Done when** Goodluck → Able → you see last week’s vomiting (Watch) **and** this morning’s line, then one tap to speak.

---

## Phase 3 — Night voice → morning handout

**Why.** CQC treats “all fine” as a smell. Night staff will speak; they will not type a novel. The morning board **is** Phase 2 with a night window.

**User loop**

- **Night:** on shift, speak as now (with confirm chips). End of shift: one button **Make the morning page**. No extra form.
- **Morning / agency:** open the person → What changed is already the board. Optional: **Morning page** on Brief is the same three-block handout, not a dump of every `##` event.

**Rewrite the handout (do not add a new product)**

`generate_handover` in `briefs.py` becomes:

1. **Three things to watch** — flags only. If none: “Nothing was flagged. That is not the same as all fine.”
2. **What was spoken this shift** — max 8 lines, label + time + cite. If none: “Nothing was spoken on this shift. That is not the same as all fine.”
3. **Due next** — medicines, unchanged.

Delete the long “every event as a bullet” as the lead. Quotes stay behind tap / appendix.

**Shift end**

- `POST /shifts/{id}/end` already exists. After end, auto-call `generate_handover(..., window=shift)` so morning does not depend on someone remembering Make page.
- Talk/Changed: if a latest shift handout exists for this person from the last 16 hours, show “Night page ready” → Brief.

**Night window helper**

- Treat 20:00–08:00 local as night for copy (“Night page”) when the shift started after 19:00. Do not invent a second role yet.

**Seed**

- One closed night shift on Able: “Up at 2am. Door open. Tearful. Barely touched the milky drink.” Confirmed tags: sleep, preference, mood, meal.

**Tests**

- Empty shift handout contains “not the same as all fine”.
- Ending a shift creates a handover brief for that person.
- Handout lead is flags + spoken lines, not a raw markdown novel.

**Done when** night speak → end shift → morning worker opens Able and sees three risks plus quotes, without pressing Make page.

---

## Phase 4 — About Me from speech

**Why.** Agency staff fail person-centred care because “door open / tea with milk” lives in someone’s head. PRSB About Me is a standard; we fill it from speech, not a 12-page assessment.

**Do not** put this on `PersonProfile` as one overwriteable string. Preferences change and must stay cited.

**Data**

- Same `CareEvent` with `type=preference`, `subtype=about_me`.
- `detail` is the sticky line: “Prefers the bedroom door open.”
- `raw_transcript` is the quote.
- Latest 5 preference events for that person = the About Me card. Newer detail on the same theme replaces the card line but History keeps both quotes.

**Extractor**

Heuristic cues (only when not already a fall/meds/vomit-only sentence):

- door open / door closed
- tea, milky, sugar
- likes / prefers / always / never / hates (short preference, not a mood dump)
- sleeps with the light on

Chip label: **About them**.

**UI**

- About Me card on What changed (Phase 2 slot).
- Tap a line → quote, same as Watch.
- Talk confirm: if the sentence is only “He likes the door open,” one chip, Save, card updates. If the sentence is mixed (“tearful, door open”), two chips.

**GP / handout**

- One short **About them** block on the morning page and the GP brief. Cited. Not advice.

**Tests**

- “He likes the door open” → preference, appears on `/changed` `about`.
- Second log “tea with milk” appends a second about line.
- Quote still on the event.

**Done when** speak “door open” and “tea with milk,” then the Able What-changed card shows both, each tappable to the sentence.

---

## Phase 5 — Family and home, one person, one GP page

**Why this is the only “revolutionary” claim that is still empty.** Birdie Family App is a window into the agency. Jointly is family-only. We want Ravi at home and Abena on the unit writing to **Dad**, and Dr Chen reading one cited page.

**Data (minimal)**

- `User.role`: `support_worker` | `family` | `clinician` (already two of three).
- New: `UserPerson` (or `family_person_id` on User for the demo). Demo only needs **Ravi → Dad**. Staff stay unscoped (all 10 people) so the home demo still works.
- `CareEvent.logger_id` already exists. History line: “Abena · 21:04” / “Ravi · 22:10”.

**Who screen**

Three paths, still one question:

1. **I am on shift** — worker names (Goodluck, Abena, …)
2. **I am family** — Ravi (only). Then person is **Dad** only (skip the 10-person list, or list of one).
3. **Nurse or GP** — read only, all people.

`canWrite` = `support_worker` **or** `family`. `_require_writer` allows `family`. Clinical still 403 on POST /log.

**Same record**

- No second database. `person_id=Dad` is the join.
- What changed shows family and staff lines together.
- GP brief already person-scoped. Add “Logged by” in the appendix quotes: `Ravi (family)` vs `Abena (shift)`.
- Family default handout = 72h. Staff default = shift / 12h. Same Make page, different default window.

**Do not**

- Let family see Able, Margaret, … (home residents).
- Let family start a paid shift clock.
- Build a family social feed, tasks, or WhatsApp clone.

**Seed**

- User `Ravi`, role `family`, linked to Dad.
- One family log on Dad in the last 12 hours: “Barely touched supper.” So staff What-changed shows a family line.

**Tests**

- Family Ravi `POST /log` on Dad → 200. On Able → 403.
- Clinician still 403 on log.
- `/changed` for Dad includes both a staff logger and Ravi.
- GP brief appendix names both loggers.
- Worker list still five staff; Ravi is not in the shift dropdown.

**Done when** Abena logs late meds on Dad, Ravi logs low appetite on Dad, Dr Chen opens Dad and the GP page cites both, with names.

---

## Suggested calendar (one person, demo-quality)

| Phase | Days | Demo you can film |
|---|---|---|
| 1 Confirm tags | 1–2 | Tearful → Mood → History |
| 2 What changed | 1–2 | Able: vomit flag + this morning |
| 3 Night → morning | 1 | End night shift → morning board |
| 4 About Me | 1 | Door open + tea on the card |
| 5 Family + home | 1–2 | Ravi + Abena → one GP PDF |

Do not start Phase 5 until 1–2 work. Family without trustworthy tags just writes more Notes.

---

## Out of scope (still)

- eMAR, rota, GPS, CQC audits
- Offline clip queue (after these five, if homes need it)
- DSPT / NHS login / writing the GP record
- Sleep/falls Watch **rules** beyond storing the tag (Phase 1 stores sleep/fall; a count rule can follow if the demo needs “two night wakings”)

---

## Files that will move (map)

| Phase | Touch |
|---|---|
| 1 | `extractor.py`, `ollama_client.py` (prompt list), `main.py`, `TalkScreen.jsx`, `App.jsx`, `mobile/App.js`, `labels.js`, `tests/` |
| 2 | `main.py` (`/changed`), `TalkScreen.jsx`, `seed.py`, `PatternsScreen` only if we reuse WatchItem |
| 3 | `briefs.py`, `main.py` (end shift), `BriefScreen.jsx`, `TalkScreen.jsx`, `pdf_render.py` if headings change |
| 4 | `extractor.py`, `/changed` `about`, `TalkScreen` card, `briefs.py` About them block |
| 5 | `models.py` + seed, `RoleGate.jsx`, `PersonPick.jsx`, `_require_writer`, History “logged by”, brief appendix |

---

## If we only ship one slice

Phase 1 + the What-changed panel (Phase 2) using today’s Watch flags. That makes speech trustworthy and makes staff turnover the reason the app exists. Phases 3–5 amplify the same loop.
