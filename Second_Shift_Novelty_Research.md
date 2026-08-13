# Second Shift — UK Novelty & Competitive Research Report
*Is a voice-first AI agent for whoever is on the shift (family and paid staff) novel in the UK? Verdict: the integrated loop is novel; DSCR incumbents own the operational record, not person-level speech → patterns → cited brief. Details below.*

## Executive summary

- **No equivalent UK product exists** that closes the full loop for **dementia care**: voice-first logging → missed-medicine / symptom pattern detection → shift handout + auto-generated, evidence-cited GP / memory-clinic brief, with **memory stored on the person** so the next worker (or a nurse/GP) sees last week’s events.
- **The UK market is converging on pieces of it**: Jointly (Carers UK coordination), Share2Care (NHS West Yorkshire unpaid-carer app + contingency plan), KinKeeper (family hub with PDF journal for GPs, UK launch 2026), Heidi / Tortus / Accurx (AI scribes of the GP consultation itself), **Nourish / Birdie / PASSforcare** (paid-staff DSCRs, visits, eMAR).
- **UK policy tailwind**: 5.8 million unpaid carers; unpaid care worth about £184 billion a year; NHS 10 Year Health Plan; Digitising Social Care / DSCR MODS; Nuffield Trust found only about 1.4% of unpaid carers are identifiable in GP data versus the Census.
- **Academia (2023–2026)** has GPT/LLM assistants for dementia carers, plus UK pilots (Curendi, PuntoCare, council voice assessments). Almost all are Q&A, guidance, or social-care intake. None do operational logging → pattern detection → GP briefs.
- **Hackathon arena**: no notable UK hackathon winner found with this full concept.
- **Beachhead**: dementia. Users: unpaid family **and** paid support workers. Nurses/GPs get a simple view. We do **not** rebuild eMAR or a full DSCR.
- **Novelty score (UK)**: concept ~6.5/10; integrated speech → person memory → GP/shift handout ~8.5/10; UK hackathon-context novelty ~9/10.

## Beachhead: dementia (family and paid staff)

There are many types of care, and many care *settings*. Second Shift is one *job*, not one *setting*: turn what the person on shift says into a log, patterns, and a handout the next worker and the GP can use.

| Setting | Who records | In scope? |
|---|---|---|
| **Family care at home** | Unpaid carer (son, daughter, partner) | **Yes.** Demo persona: Ravi / Dad. |
| **Paid domiciliary / home care** | Agency support workers | **Yes, as recorders.** Do not rebuild Birdie visits/eMAR. |
| **Residential / nursing / dementia care home** | Care/support workers | **Yes, as recorders.** Do not rebuild Nourish DSCR/eMAR. |
| Nurse on the unit / caseload | Registered nurse | **Simple view** (flags, trends, PDF). Not a second EHR. |
| GP / memory clinic | Doctor | **Simple view** (trends + cited brief). No shift clock. |

Nourish, Birdie, and PASSforcare already exist for professional **operations**. The gap is **organisational memory on the person** when staff change, plus a cited GP handout from speech. That is still novel against those incumbents.

Within *home* care, later verticals could include stroke, Parkinson’s, frailty, and end of life. **Start with dementia** because:

- ~**982,000** people live with dementia in the UK (Alzheimer’s Society / Carnall Farrar, 2024), rising to **1.4 million by 2040**.
- Dementia is the UK’s **biggest killer**.
- Annual cost ~**£42 billion**; **unpaid care is 50%** of that cost. Families bear most of it.
- A **third of unpaid dementia carers** report **100+ hours a week**.
- Most people with dementia live in the community, not in a care home. The exhausted family carer is the missing clinical informant.
- Academic and NHS innovation (Curendi, PuntoCare, Dementia Carers Count) already clusters here, but as Q&A, guidance, or cognitive testing, not logging → patterns → GP brief.
- Memory-clinic and GP appointments are short. A one-page evidence brief of confusion episodes, missed medicines, sleep, and appetite is the format they can use.

**Personas:** **Ravi**, 34, night shifts, cares at home for his 71-year-old father with dementia (6 medicines). **Priya**, support worker, was off last week and must still see that Able vomited after food.

**Demo logs:** “Gave dad his 8pm meds, 40 minutes late. More confused again this evening, third time this week.” / “Able has eaten; after eating he was vomiting.”

## Why the UK, not the US

| UK fact | Why it matters for Second Shift |
|---|---|
| 5.8 million unpaid carers (Census / Carers UK) | Named market; use “unpaid carer”, not “caregiver” |
| Unpaid care valued at ~£184bn a year | Same order of magnitude as NHS spend; impact slide |
| Only ~1.4% of unpaid carers visible in GP records (Nuffield Trust vs Census) | Home knowledge never reaches the GP. That *is* the product gap |
| Care Act 2014: carers are entitled to assessment | Voice tools exist for *council assessments* (Tovie), not for day-to-day care logs |
| NHS 10 Year Health Plan: hospital → community, analogue → digital | Home observations belong in the community shift |
| 10-minute GP appointments | A one-page evidence brief is the format GPs can actually use |
| MHRA / DTAC / DSPT / UK GDPR | Frame as organising notes and drafting questions, not a medical device |

**The UK insight:** the carer is the missing clinical informant. The GP record, the NHS App, and the consultation scribe all start *after* the person walks into the surgery. Second Shift starts at 11pm at home.

## UK competitor landscape

| Product | What it does | Gap vs. Second Shift |
|---|---|---|
| **Jointly** (Carers UK) | Circle of care, tasks, calendar, medicine lists, notes; designed by carers | Tap/text logging; no voice-first capture; no pattern engine; no auto GP visit brief (contingency plan can be exported, not generated from home events) |
| **Share2Care** (Care Networx + NHS West Yorkshire ICB) | Unpaid-carer app: coordinate a circle of care, record medicines, note symptom changes, digital contingency plan into the NHS record via NHS login | Closest NHS-backed rival. Still tap-based organisation, not conversational voice logging; no missed-dose / symptom pattern detection; no evidence-cited GP brief from the home log |
| **KinKeeper** (UK, launching 2026) | Family care hub: medicine logs, shared calendar, document vault, care journal exportable to PDF for GPs, AI weekly summary digest | Closest *brief* rival. Not voice-first; weekly digest is not a pattern-flagged, evidence-cited visit brief tied to voice-log timestamps; not live yet |
| **Heidi, Tortus, Accurx Scribe** | Ambient AI scribes of the GP / clinic consultation; notes into EMIS / SystmOne | Capture the surgery, not the home. Know nothing about late doses or evening confusion between appointments |
| **NHS App** | Appointments, prescriptions, GP record, messages | Patient-facing record access. No carer voice log, no pattern detection, no visit brief from home observations |
| **PASSforcare / everyLIFE** | Paid home-care staff: visit check-in, eMAR, voice-to-text notes, GP Connect | Operational agency record. No person-level recurrence memory → cited GP brief from speech; not for unpaid family at 11pm either |
| **Nourish Care** | Leading UK DSCR for residential and home-care providers; care plans, point-of-care notes, rostering (Empower), CQC-oriented records; NHS Assured Solutions list | Digitises the *paid care record*. Alerts are operational. Does not turn natural speech into deterministic patterns plus a cited GP/shift handout for whoever was *not* on last week |
| **Birdie** | Home-care agency hub + carer app: visit check-in/out, observations, eMAR alerts | Visit and compliance alerts, not “Able vomited after meals last week” as evidence-cited person memory |
| **Curendi** (NHS Clinical Entrepreneur Programme) | Dementia carer guidance between appointments: “help me now”, diaries, signposting to GP / memory clinic | Support and next-step advice, not operational event logging → patterns → GP brief |
| **PuntoCare** (Punto Health; NHS pilots) | Speech AI for cognitive assessment plus a patient/carer daily-plan app | Detection and activity plans for the person with dementia, not carer home-event logging for the GP |
| **Tovie AI** (Richmond & Wandsworth councils) | 24/7 voice/text assistant so unpaid carers can complete a *carer assessment* | Social-care intake, not a longitudinal care log or GP visit brief |

### International products a UK judge may still name

| Product | Gap vs. Second Shift |
|---|---|
| ianacare (US) | Tap-based coordination + AI chat; not voice-first; no GP brief |
| Medisafe | Reminder-first, mostly patient-facing; no visit briefs |
| Hedy.ai | Records the clinic visit; no home knowledge |
| CareCurrent | Pre-visit briefs from hospital/EHR data, not carer voice logs |
| ElliQ | Senior-facing companion robot; not a carer tool |

**Closest UK pair (family):** Share2Care + KinKeeper. **Closest UK pair (paid staff):** Nourish + Birdie / PASSforcare. None close voice → structured log → deterministic person-level patterns → evidence-cited GP brief *and* a shift handout that follows 6h/12h (with 72h only as a family preset).

## Academic and UK research state of the art (2023–2026)

**UK / NHS-adjacent**

- **BMJ Open 2024** (informal carers and medicines for long-term conditions): carers do a large share of medicines management; their role is underestimated and poorly supported.
- **BMJ Open 2025** (realist review): hospital-to-home medicines transitions depend on unpaid carers, who are often left without a clear record of what changed.
- **Nuffield Trust**: Census-scale unpaid caring is almost invisible in GP data (~1.4% identified).
- **Curendi (2026, NHS CEP)**: practical, non-diagnostic dementia-carer guidance between appointments. Still a support tool, not a logging-to-brief pipeline.
- **Punto Health**: speech biomarkers and carer app; NHS pilots at North London NHS FT and Oxleas. Focus is cognition, not GP visit briefs from home logs.
- **Dementia Carers Count / Journal of Dementia Care (2025)**: guides on Alexa-style voice tech for dementia households. Consumer voice assistants, not care-event extraction.
- **EPSRC Network Plus (2025)**: UK funding wave for post-diagnostic dementia technology (BRIDGES, CONSOLIDATE, TEDI). Signals demand; no product yet matching Second Shift.

**International LLM carer assistants (still Q&A / companionship)**

- Zaman et al. 2023 (IEEE): GPT voice assistant for ADRD carers. Q&A.
- Hasan et al. 2024 (npj): conversational support, not operational logging.
- Walter, Steuck & Knackstedt 2025/26 (Springer): context-sensitive voice companion.
- Loc-demcare 2026 (IEEE): local, privacy-preserving chatbot. Privacy angle is useful for UK GDPR pitches.
- Zhou et al. 2026 (JMIR): ChatGPT-4o for early-stage dementia carer Q&A.
- Vafafar et al. 2026 (ACM): emotional support. “Words are not enough.”

**Gap confirmed (UK + literature):** no product or paper combines *voice event-logging* (family or paid staff), medicines/symptom *pattern detection on the person*, and an automated, evidence-cited *GP visit brief* plus a shift handout.

## The novelty delta (UK pitch ammunition)

1. **Speech → next worker and GP.** Heidi/Tortus capture the consultation. Nourish/Birdie capture the paid record. Share2Care stores a contingency plan. Nobody turns what *this shift* said into what *the next shift and the GP* can read, with citations.
2. **Voice-first for the person on shift, not the patient.** Family at 11pm and paid support workers both speak faster than they tap.
3. **Evidence-cited GP brief.** Every line traces to a timestamped log. That is the trust feature for NHS-minded judges.
4. **Handover that matches the shift.** Staff: 6h or 12h of *this* clock, plus open flags from the last 7–14 days. Family/weekend: 72-hour preset. Jointly and Nourish do not auto-write that from speech.
5. **Memory stays with the person.** Priya was off last week; Able’s vomiting still surfaces. Flags store the exact event IDs.
6. **Makes unpaid (and rotating paid) observers visible.** GP systems see ~1.4% of unpaid carers. Structured logs bring observations into the appointment without writing into the NHS record on day one.

## UK risks and mitigations

- A judge knows **Jointly** or **Share2Care** → “they organise the circle of care; we turn speech into a GP brief.”
- A judge knows **Nourish / Birdie / PASSforcare** → “they digitise the paid record and eMAR; we keep memory on the person when staff change, and we write the handout from speech.”
- A judge knows **Heidi / Tortus** → “they transcribe the appointment; we brief the GP on what happened *since* the last one.”
- A judge knows **KinKeeper** → “PDF journal and weekly digest are adjacent; we are voice-first, pattern-flagged, and evidence-cited to the log.”
- **MHRA medical-device** risk → frame as “flags patterns and drafts questions for the GP”; never diagnosis, triage, or treatment advice; persistent “not a medical device” disclaimer.
- **UK GDPR / health data** → encrypted at rest, discard raw audio after transcription, export/delete on demand, synthetic demo personas. Local/on-device STT is a strong UK privacy story.
- **NHS integration temptation** → do *not* claim GP Connect / NHS login in a hackathon build. Pitch “carer brings a PDF to the GP.” Share2Care already occupies the NHS-record-upload lane.

## Ways to sharpen novelty further (UK)

1. Lead with the **handover / handout** (staff: this shift; family: 72h preset). Jointly shares a circle; Nourish stores notes; neither writes the handout from speech.
2. Keep the brief **evidence-cited** (timestamped quotes). NHS judges distrust unsourced AI summaries.
3. Add **carer-burden check-ins** (Carers UK: high stress, worsening health). Products track the cared-for person, not the carer.
4. Mention **offline / on-device** mode for privacy credibility (UK GDPR, Loc-demcare).
5. Show a **pattern chart**: dizziness clustered after a dose change. Visual, clinical, and novel.
6. Optional pitch-only: “this is the missing input to a future GP record,” without building NHS integration.

## Sources

**UK market and policy**

1. Carers UK, Key facts and figures (5.8 million unpaid carers) — https://www.carersuk.org/policy-and-research/key-facts-and-figures/
2. Alzheimer’s Society, dementia scale and impact (~982,000 people; £42bn; unpaid care 50%) — https://www.alzheimers.org.uk/what-we-do/policy-and-influencing/dementia-scale-impact-numbers
3. Alzheimer’s Society / Carnall Farrar, economic impact of dementia — https://www.alzheimers.org.uk/what-we-do/policy-and-influencing/economic-impact-of-dementia
4. Centre for Care / Carers UK, Valuing Carers (~£184bn) — https://www.carersuk.org/media/mfbmjbno/valuing_carers_uk_v3_web.pdf
4. HFMA / Nuffield Trust comparison: Census carers vs GP-identified carers (~1.4%) — https://www.hfma.org.uk/publications/carers-app-unpaid-carers
5. NHS West Yorkshire ICB, Share2Care unpaid carers app — https://www.wypartnership.co.uk/our-priorities/unpaid-carers/carers-programme-news-2
6. UKAuthority, Share2Care launch — https://www.ukauthority.com/articles/unpaid-carers-app-launches-in-west-yorkshire

**UK / UK-launch products**

7. Jointly (Carers UK) — https://www.carersuk.org/help-and-advice/technology-and-equipment/jointly-app-for-carers/
8. KinKeeper — https://kinkeeper.co.uk/
9. PASSforcare / everyLIFE carer app — https://www.everylifetechnologies.com/pass-features/carer-app/
9a. Nourish Care — https://nourishcare.com/
9b. Birdie — https://www.birdie.care/product-features/carer-app
9c. NHS England DAPB4102 DSCR MODS — https://digital.nhs.uk/data-and-information/information-standards/governance/latest-activity/standards-and-collections/dapb4102-adult-social-care-record-minimum-operational-data-standard
9d. DHSC Care Workforce Pathway — https://www.gov.uk/government/publications/care-workforce-pathway-for-adult-social-care
10. Heidi Health (UK GP scribe) — https://www.heidihealth.com
11. Tortus (UK NHS ambient scribe) — https://tortus.ai
12. Accurx — https://www.accurx.com
13. NHS App — https://www.nhs.uk/nhs-app/
14. Curendi, NHS Clinical Entrepreneur Programme — https://nhscep.com/2026/07/09/our-entrepreneurs-guido-bua/
15. Punto Health (NHS pilots) — https://agetechworld.co.uk/news/2m-backs-speech-ai-for-early-dementia-care/
16. Tovie AI carer assessments (Richmond & Wandsworth) — https://tovie.ai/care-assessment

**UK research**

17. BMJ Open 2024, informal carers and medication management — https://doi.org/10.1136/bmjopen-2024-094443
18. BMJ Open 2025, carer involvement in hospital-to-home medicines — https://doi.org/10.1136/bmjopen-2025-107826

**International (secondary)**

19. ianacare — https://www.ianacare.com
20. Medisafe — https://www.medisafe.com
21. Hedy.ai — https://www.hedy.ai
22. CareCurrent — https://www.carecurrent.com
23. Zaman et al. 2023, IEEE — https://ieeexplore.ieee.org/abstract/document/10218142/
24. Hasan et al. 2024, npj Biomedical Innovations — https://www.nature.com/articles/s44385-024-00004-8
25. Loc-demcare 2026, IEEE — https://ieeexplore.ieee.org/abstract/document/11585298/
26. Zhou et al. 2026, JMIR Formative Research — https://formative.jmir.org/2026/1/e79975
