# Second Shift — UK Novelty & Competitive Research Report
*Is a voice-first AI agent for unpaid family carers novel in the UK? Verdict: the integrated concept is novel; individual slices exist. Details below.*

## Executive summary

- **No equivalent UK product exists** that closes the full loop for **dementia care at home**: voice-first logging → missed-medicine / symptom pattern detection → escalation prompts → auto-generated, evidence-cited GP / memory-clinic brief.
- **The UK market is converging on pieces of it**: Jointly (Carers UK coordination), Share2Care (NHS West Yorkshire unpaid-carer app + contingency plan), KinKeeper (family hub with PDF journal for GPs, UK launch 2026), Heidi / Tortus / Accurx (AI scribes of the GP consultation itself), PASSforcare (voice notes for *paid* home-care staff).
- **UK policy tailwind**: 5.8 million unpaid carers; unpaid care worth about £184 billion a year; NHS 10 Year Health Plan shifts (hospital to community, analogue to digital); Nuffield Trust found only about 1.4% of unpaid carers are identifiable in GP data versus the Census.
- **Academia (2023–2026)** has GPT/LLM assistants for dementia carers, plus UK pilots (Curendi, PuntoCare, council voice assessments). Almost all are Q&A, guidance, or social-care intake. None do operational logging → pattern detection → GP briefs.
- **Hackathon arena**: no notable UK hackathon winner found with this full concept.
- **Beachhead**: dementia care *at home* (unpaid family carers), not residential care homes.
- **Novelty score (UK)**: concept ~6.5/10; integrated home→GP closed loop ~8.5/10; UK hackathon-context novelty ~9/10.

## Beachhead: dementia at home (not a care home)

There are many types of care, and many care *settings*. Second Shift v1 is one slice only.

| Setting | Who delivers care | In scope for v1? |
|---|---|---|
| **Family care at home** | Unpaid carer (son, daughter, partner) | **Yes. This is the product.** |
| Paid domiciliary / home care | Agency staff (Birdie, PASSforcare) | No. Those tools already exist for professionals. |
| Residential / nursing / dementia care home | Care-home staff | No. Homes already have eMAR and visit notes. |

Within *home* care, later verticals could include stroke, Parkinson’s, frailty, and end of life. **Start with dementia** because:

- ~**982,000** people live with dementia in the UK (Alzheimer’s Society / Carnall Farrar, 2024), rising to **1.4 million by 2040**.
- Dementia is the UK’s **biggest killer**.
- Annual cost ~**£42 billion**; **unpaid care is 50%** of that cost. Families bear most of it.
- A **third of unpaid dementia carers** report **100+ hours a week**.
- Most people with dementia live in the community, not in a care home. The exhausted family carer is the missing clinical informant.
- Academic and NHS innovation (Curendi, PuntoCare, Dementia Carers Count) already clusters here, but as Q&A, guidance, or cognitive testing, not logging → patterns → GP brief.
- Memory-clinic and GP appointments are short. A one-page evidence brief of confusion episodes, missed medicines, sleep, and appetite is the format they can use.

**Persona:** Ravi, 34, night shifts, cares at home for his 71-year-old father with dementia (6 medicines). Untrained. At the GP or memory-clinic appointment, he forgets half of the week.

**Demo log:** “Gave dad his 8pm meds, 40 minutes late. More confused again this evening, third time this week.”

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
| **PASSforcare / everyLIFE** | Paid home-care staff: visit check-in, eMAR, voice-to-text notes, GP Connect | Built for agencies and professional carers, not unpaid family carers at 11pm |
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

**Closest UK pair:** Share2Care (NHS carer app) + KinKeeper (PDF for GPs). Neither closes voice → structured log → deterministic patterns → evidence-cited GP brief.

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

**Gap confirmed (UK + literature):** no product or paper combines unpaid-carer *voice event-logging*, medicines/symptom *pattern detection*, and an automated, evidence-cited *GP visit brief*.

## The novelty delta (UK pitch ammunition)

1. **The home→GP closed loop.** Heidi/Tortus capture the consultation. The NHS App shows the record. Share2Care stores a contingency plan. KinKeeper can export a journal PDF. Nobody turns what the unpaid carer *says at home* into what the GP *reads in the 10-minute appointment*.
2. **Voice-first for the carer, not the patient.** UK voice products target Alexa in the living room, council assessments, or the person with dementia. The exhausted night-shift carer logging hands-free is unserved.
3. **Evidence-cited GP brief.** Every line traces to a timestamped voice log. That is the trust feature for NHS-minded judges.
4. **Family handover briefs.** “Your sister takes over tomorrow. Here is the last 72 hours.” Jointly and Share2Care coordinate people; they do not auto-generate a shift handover from the care log.
5. **Makes the invisible carer visible.** If GP systems only see 1.4% of unpaid carers, a structured home log is a way to bring their observations into the appointment without claiming to write into the NHS record on day one.

## UK risks and mitigations

- A judge knows **Jointly** or **Share2Care** → put the UK comparison table on one slide; say “they organise the circle of care; we turn home speech into a GP brief.”
- A judge knows **Heidi / Tortus** → “they transcribe the appointment; we brief the GP on what happened *since* the last one.”
- A judge knows **KinKeeper** → “PDF journal and weekly digest are adjacent; we are voice-first, pattern-flagged, and evidence-cited to the log.”
- **MHRA medical-device** risk → frame as “flags patterns and drafts questions for the GP”; never diagnosis, triage, or treatment advice; persistent “not a medical device” disclaimer.
- **UK GDPR / health data** → encrypted at rest, discard raw audio after transcription, export/delete on demand, synthetic demo personas. Local/on-device STT is a strong UK privacy story.
- **NHS integration temptation** → do *not* claim GP Connect / NHS login in a hackathon build. Pitch “carer brings a PDF to the GP.” Share2Care already occupies the NHS-record-upload lane.

## Ways to sharpen novelty further (UK)

1. Lead with the **handover brief** (family shift change). Jointly shares a circle; it does not write the handover.
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
