# Second Shift — Section-by-section guide

This document explains **what we built, why, and how each part works**. Read it in order. You do not need to train any model.

---

## 1. What this project is

Second Shift is a **voice-first helper for unpaid family carers** of people with **dementia at home in the UK**.

The carer speaks naturally, for example:

> Gave dad his 8pm meds, 40 minutes late. More confused again this evening, third time this week.

The app then:

1. Turns speech into text (or you type the same words).
2. Turns that text into a **structured care log** (medicine late, confusion, low appetite, and so on).
3. Runs **rules** (not the AI) to spot patterns, such as three confusion episodes after a dose change.
4. Builds a **one-page GP / memory-clinic brief** where every fact cites a log timestamp.
5. Can also build a **72-hour family handover** for the relative taking over.

It **organises notes and drafts questions**. It does **not** diagnose, triage, or give treatment advice. It is **not a medical device**.

Named user: **Ravi**, 34, night shifts, cares for his 71-year-old father.

---

## 2. What we researched (before any code)

We checked whether this idea already exists in the **UK**.

**Finding:** pieces exist. The full loop does not.

| Existing product | What it does | What it does not do |
|---|---|---|
| Jointly (Carers UK) | Circle of care, tasks, medicine lists | Voice logging, pattern engine, GP brief |
| Share2Care (NHS West Yorkshire) | Carer app + contingency plan in the NHS record | Still tap-based organisation |
| Heidi / Tortus / Accurx | AI scribe of the GP appointment | Knows nothing about home |
| Curendi | Dementia carer guidance between appointments | Advice, not logging → brief |

**UK facts we used**

- About 982,000 people with dementia in the UK.
- Unpaid care is about 50% of dementia’s £42bn cost.
- About 5.8 million unpaid carers.
- Only about 1.4% of unpaid carers show up in GP records.

**Beachhead:** dementia **at home**, not a care home (homes already have eMAR). Later we could add stroke, Parkinson’s, frailty.

Full write-up: [Second_Shift_Novelty_Research.md](Second_Shift_Novelty_Research.md).  
One-page pitch: [Second_Shift_One_Pager.pdf](Second_Shift_One_Pager.pdf).

---

## 3. How the system is wired

```text
Microphone or typed text
        ↓
Local Whisper (speech → text)     [skipped if you type]
        ↓
Ollama llama3.2:3b (text → JSON events)
        ↓
SQLite care log
        ↓
Python rules (count late doses, confusion, appetite)
        ↓
Ollama only writes suggested GP questions
        ↓
PDF brief (facts assembled in Python, with citations)
        ↓
Browser speaks a short confirmation
```

**Important split:** the language model **never counts** “three times this week”. Python rules do that. That is the safety design.

This machine has a **GTX 1650 (4GB VRAM)**. Whisper runs on the GPU, then unloads, so Ollama can use memory. If Ollama is not running, a **heuristic extractor** still logs the demo sentence so the demo does not die.

---

## 4. Folders (what lives where)

| Path | Role |
|---|---|
| `backend/` | FastAPI API, database, Whisper, Ollama, rules, PDF |
| `frontend/` | Four screens: Talk, Timeline, Patterns, Brief |
| `tests/` | Automated checks for each phase |
| `scripts/verify_all.sh` | Runs those checks in one go |
| `environment.yml` | conda env named `secondshift` |
| `docs/` | Mockup images and HTML one-pager art |
| `IMPLEMENTATION_PHASES.md` | Original phase plan |

---

## 5. Section by section: what we implemented

### Section A — Environment (Phase 0)

**What:** A conda environment called `secondshift` so Python packages do not mix with other projects.

**How to use**

```bash
conda activate secondshift
```

First-time create (already done on this PC):

```bash
conda env create -f environment.yml
cd frontend && npm install
```

**What was verified:** Python 3.11, FastAPI, pytest, fpdf2, faster-whisper installed. Frontend `npm run build` succeeded.

---

### Section B — Database and seed story (Phase 0)

**What:** SQLite file at `backend/data/secondshift.db`.

Tables:

- `person_profile` — Dad, 71, dementia
- `medication_schedule` — Donepezil, Ramipril, Atorvastatin. Donepezil **changed Friday 7 Aug 2026**
- `care_events` — append-only log
- `pattern_flags` — outputs of the rules engine
- `briefs` — generated GP / handover documents

**Seed (6 days already in the database):**

- Two **late evening doses**
- Two **confusion** episodes (so the live line is the **third**)
- Four **low appetite** notes

That is why the demo line fires a pattern on stage.

**What was verified:** `GET /health` and `GET /events` return Dad + seeded logs (`tests/test_phase0.py`).

---

### Section C — Talk screen and voice (Phase 1 + mic fix)

**What you see:** big **Start** / **Stop** button, a text box, and **Log text**.

**Voice path**

1. Click **Start**. Allow the microphone if Chrome asks.
2. Speak.
3. Click **Stop** (or wait 15 seconds; it auto-stops).
4. Audio is sent to `POST /transcribe`.
5. Local Whisper turns it into text.
6. Audio file is deleted (privacy).
7. Text is sent to `POST /log`.

**If the mic does nothing:** type the sentence and click **Log text**. That is the official fallback.

**Mic bug we fixed:** the first version started recording on one click and never finished unless you clicked again, and the label said “Hold”. It now says Start/Stop and shows “Recording…”.

**What was verified:** typed Ravi sentence creates medicine + confusion events (`tests/test_phase1.py`).

---

### Section D — Turning words into a care log (Phase 1)

**What:** `POST /log` with `{ "transcript": "..." }`.

Ollama is asked for **JSON only**, for example:

- type: `medication` / `symptom` / `meal` / …
- subtype: `dose_late` / `confusion` / `appetite_low` / …
- confidence, detail, event time

If Ollama is down, a small **heuristic** still understands the demo sentence (late meds, confusion, dinner).

The agent replies with a short confirmation. The browser can **speak** it (`speechSynthesis`, UK English).

Hard rule in the prompt: **no diagnosis**.

**What was verified:** text fallback stores events and they appear on Timeline.

---

### Section E — Pattern engine (Phase 2)

**What:** Python in `backend/app/patterns.py`. No Ollama import.

Rules:

1. **Late/missed doses:** 2 or more in 7 days → flag
2. **Confusion:** 3 or more in 7 days → flag, and if they started after Donepezil’s `last_changed_at`, the message names that date
3. **Appetite:** 4 or more low-appetite notes → declining trend flag

After every new log, flags are recomputed.

**What was verified:** adding the third confusion creates `symptom_recurrence` and mentions the dose change (`tests/test_phase2.py`). The rules file does not mention Ollama.

---

### Section F — GP / memory-clinic brief (Phase 3)

**What:** **Generate GP brief** on the Brief tab.

Facts (medicines, symptoms, citations, patterns) are **written in Python** from the database so the model cannot invent counts.

Ollama is only asked for **3–5 questions** the carer can ask the GP. If Ollama is down, three default questions are used.

Every symptom/dose line includes a citation like `[log 11 Aug 2026 20:40]`.

PDF is built with `fpdf2` (no extra system libraries). Download: `GET /briefs/latest.pdf`.

**What was verified:** markdown contains `[log ` and the dose-change pattern; file starts with `%PDF` (`tests/test_phase3.py`).

---

### Section G — Patterns chart, safety, handover (Phase 4)

**Patterns tab:** 7-day bar chart of confusion + dose-change marker.

**Emergency:** if the text contains `unconscious`, `not breathing`, or `severe chest pain`, the app shows **Call 999**. Ollama is **not** called.

**Urgent checkbox:** “Add to the urgent section of the GP brief” plus NHS 111 text. Observational only.

**Family handover:** last 72 hours, open flags, medicines due next. Download `GET /handover/latest.pdf`.

**What was verified:** emergency path never calls Ollama; handover PDF exists; chart includes `2026-08-07` (`tests/test_phase4.py`).

---

## 6. How to run (correct folders)

Port 8000 may already be used by another project. Use **8001** if you see “Address already in use”.

You must be in **this** repo, not `~/backend`.

**Terminal 1 — API**

```bash
conda activate secondshift
cd /home/goodluck/Desktop/MyProjects/Tutorial/SecondShiftNovelty/backend
PYTHONPATH=. uvicorn app.main:app --reload --port 8001
```

**Terminal 2 — website**

```bash
cd /home/goodluck/Desktop/MyProjects/Tutorial/SecondShiftNovelty/frontend
VITE_API_URL=http://127.0.0.1:8001 npm run dev
```

Open **http://127.0.0.1:5173** in Chrome.

**Optional Ollama (better extraction)**

```bash
ollama serve
ollama pull llama3.2:3b
```

Without Ollama, typed demo logging still works.

---

## 7. Two-minute demo script

1. Open Talk. Disclaimer should be visible.
2. Type: `Gave dad his 8pm meds, 40 minutes late. More confused again this evening, third time this week.`
3. Click **Log text**.
4. Timeline should show late medicines + confusion.
5. Patterns should mention three confusion episodes after the Friday dose change.
6. Brief → **Generate GP brief** → download PDF. Check a `[log …]` citation.
7. **Family handover** → download the 72-hour PDF.
8. Optional: type `He is unconscious` and confirm the 999 screen.

---

## 8. Tests we ran

```bash
conda activate secondshift
cd /home/goodluck/Desktop/MyProjects/Tutorial/SecondShiftNovelty
./scripts/verify_all.sh
```

Result when last run: **12 unit tests passed**, plus a text-path closed-loop smoke test (log → flag → GP PDF → handover PDF). Frontend production build succeeded.

---

## 9. What we did not build (on purpose)

- NHS login / writing into the GP record
- Training our own Whisper or Llama
- Care-home or paid-carer app
- Multi-user accounts, push notifications, doctor portal
- Diagnosis or triage

Those stay on the pitch slide only.

---

## 10. If something breaks

| Problem | What to do |
|---|---|
| `Address already in use` | Use `--port 8001` and set `VITE_API_URL` to match |
| Watches `/home/goodluck/backend` | You `cd`’d the wrong folder. Use the `SecondShiftNovelty/backend` path above |
| Mic sits on Start and never finishes | Click **Stop**. Or use **Log text** |
| Whisper error | Type the sentence. First Whisper run may download the `small` model |
| Ollama not found | Install Ollama later; heuristic + typed log still demo the loop |
| Empty page | Start **both** terminals; API first, then frontend |

---

## 11. Pitch line

> Jointly organises the circle of care. Heidi transcribes the appointment. Second Shift turns what the carer says at 11pm into what the GP reads in 10 minutes.
