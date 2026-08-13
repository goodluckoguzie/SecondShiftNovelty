# Second Shift — Build plan

Rewritten after a second brutal pass. This is the spec we are implementing.

---

## Brutal critique (why the last plan was still weak)

The first rewrite still treated login, shifts, and a nurse card as equal to the product. They are not. Birdie already has voice-to-text, food/mood observations, task lists, a Family App, Analytics, and SmartPlans (speech → cited care-plan fields **inside Birdie**). Nourish already has a handover screen and Insights.

If we ship task lists, a 11-table DSCR, or a login wall before Talk, we look like a worse Birdie. Judges who know those tools will say the Able banner is “a filtered observation report.”

**The only honest brand:** a messy sentence becomes a cited page that can leave the building.

---

## Brand (must be visible on first screen)

**Line:** They keep care inside the provider app. We turn a spoken sentence into a cited page for the person who is not in that app.

**Loop (this is the product):** Speak or type → chips + “similar last week” with tap-to-quote → one-pager with `[log 7 Aug 19:40]`.

Login, shift clock, and nurse/GP view are **after** that loop. The app opens on Talk. “Record now” skips the role gate.

---

## Stand of the app after this build

| Who | What they get |
|---|---|
| Ravi / support worker | Talk first. Speech or type. Human chips. Similar-last-week banner with quotes. GP brief + handover screen. |
| Priya on Able | Same. Able’s last-week vomiting is already in the seed. Live sentence fires the banner. |
| Nurse / doctor | Same person record, no mic. Timeline, chart, cited PDFs. Cannot write. |
| GP who is not a user | Holds a PDF. No Birdie/Nourish login. |

**Still not a medical device.** Banners cite dates. They do not diagnose.

---

## What we are still missing (do not pretend we fixed these)

| Gap | Why it is OK for this build | Later |
|---|---|---|
| Offline / poor signal | Typed + heuristic works; Whisper needs the box | Cache queue |
| Real auth / GDPR access control | Fake role header only | NHS login is pitch-only |
| Task lists / eMAR / rota | Deliberately not ours | Never as the brand |
| Multi-home / real roster | One demo org implied | Not this repo |
| Merged transcribe+log on the old UI path | New `POST /log/audio` is the fix | Delete two-hop when UI uses it |
| Brief history per visit | Latest per person | Keep versions later |
| Sleep / falls / hydration rules | Schema allows; only vomit + existing three rules ship | Add when a demo needs them |

**Improvements we do ship now:** theme + components, person-first DB, Able story, tap-to-quote, `/log/audio`, handover screen, shift vs 72h, clinical view.

---

## Copy vs do not copy

| Copy | Do not copy |
|---|---|
| Tap fact → quote (SmartPlans receipt) | Task lists, GPS, eMAR |
| No AI on emergencies | CQC dashboards |
| Chips after speech (food, vomit, mood, late meds) | Assessment libraries |
| Handover as a screen | Claiming MODS compliance |
| Read-only clinical view | AuditLog theatre |

---

## Six tables

`User`, `Person` (existing `PersonProfile`), `Shift`, `CareEvent` (+ person_id, logger_id, shift_id), `PatternFlag` (+ person_id, evidence_event_ids), `Brief` (+ person_id).

Enums for type/subtype. Indexes on `(person_id, event_time)` and `(person_id, subtype, event_time)`.

---

## Phases (all include tests)

0. Theme + split UI. Dad demo still works. No hardcoded hex.
1. Person-first + Able seed. Isolation tests.
2. Vomiting rule, banner, tap-to-quote, `POST /log/audio`.
3. Handover screen. Shift window vs 72h family preset.
4. Fake login + clinical view. Clinician `POST /log` → 403.

Verify: existing phase 0–4 tests + new phase 6 tests + `scripts/verify_all.sh` + frontend build.

---

## Demo (do not start on login)

1. Talk (Dad). Ravi sentence. GP PDF with `[log …]`.
2. Switch to Able. “Able has eaten; after eating he was vomiting.” Banner 7–8 Aug. Tap quote. Handover screen.
3. Optional: Nurse card. Same Able. No mic.

**Say:** Birdie would put this in Analytics for the office. We put it on a page the GP can take.
