from datetime import datetime, timedelta

from sqlmodel import Session, select

from .models import CareEvent, MedicationSchedule, PersonProfile, Shift, User
from .patterns import recompute_flags

DOSE_CHANGE = datetime(2026, 8, 7, 9, 0)

WORKERS = ("Goodluck", "Abena", "Pelumi", "Okunola", "Kemi")
_PERSON_RENAMES = {"Dad": "Dou"}
_USER_RENAMES = {"Abene": "Abena"}
_OLD_DEMO_WORKERS = {"Abene"}

PATIENTS = (
    ("Dou", 71, "father"),
    ("Able", 78, "resident"),
    ("Margaret", 84, "resident"),
    ("Harold", 80, "resident"),
    ("Joyce", 76, "resident"),
    ("Ibrahim", 73, "resident"),
    ("Evelyn", 88, "resident"),
    ("Frank", 82, "resident"),
    ("Aisha", 75, "resident"),
    ("George", 79, "resident"),
)


def seed_if_empty(session: Session) -> None:
    _rename_users(session)
    workers = _ensure_users(session)
    _rename_people(session)
    people = _ensure_people(session)
    _ensure_family(session, people["Dou"])
    _retire_old_demo_workers(session, workers)
    workers = {u.display_name: u for u in session.exec(select(User)).all()}
    _backfill_person_ids(session, people["Dou"])
    _seed_dad_if_needed(session, people["Dou"], workers["Goodluck"])
    _seed_able_if_needed(session, people["Able"], workers["Pelumi"])
    _seed_other_patients(session, people, workers)
    _apply_standout(session, people, workers)
    _close_stale_shifts(session)


def _rename_people(session: Session) -> None:
    changed = False
    found = {p.name: p for p in session.exec(select(PersonProfile)).all()}
    for old, new in _PERSON_RENAMES.items():
        row = found.get(old)
        if not row or new in found:
            continue
        row.name = new
        session.add(row)
        changed = True
    if changed:
        session.commit()


def _rename_users(session: Session) -> None:
    changed = False
    found = {u.display_name: u for u in session.exec(select(User)).all()}
    for old, new in _USER_RENAMES.items():
        row = found.get(old)
        if not row or new in found:
            continue
        row.display_name = new
        session.add(row)
        changed = True
    if changed:
        session.commit()


def _ensure_users(session: Session) -> dict[str, User]:
    found = {u.display_name: u for u in session.exec(select(User)).all()}
    created = False
    for name in WORKERS:
        if name not in found:
            row = User(display_name=name, role="support_worker")
            session.add(row)
            created = True
    if "Dr Chen" not in found:
        session.add(User(display_name="Dr Chen", role="clinician"))
        created = True
    if created:
        session.commit()
    return {u.display_name: u for u in session.exec(select(User)).all()}


def _ensure_family(session: Session, dad: PersonProfile) -> User:
    found = {u.display_name: u for u in session.exec(select(User)).all()}
    ravi = found.get("Ravi")
    if not ravi:
        ravi = User(display_name="Ravi", role="family", family_person_id=dad.id)
        session.add(ravi)
        session.commit()
        session.refresh(ravi)
        return ravi
    changed = False
    if ravi.role != "family":
        ravi.role = "family"
        changed = True
    if ravi.family_person_id != dad.id:
        ravi.family_person_id = dad.id
        changed = True
    if changed:
        session.add(ravi)
        session.commit()
        session.refresh(ravi)
    return ravi


def _ensure_people(session: Session) -> dict[str, PersonProfile]:
    found = {p.name: p for p in session.exec(select(PersonProfile)).all()}
    created = False
    for name, age, relationship in PATIENTS:
        if name not in found:
            session.add(
                PersonProfile(
                    name=name,
                    age=age,
                    conditions="dementia",
                    allergies="none known",
                    relationship=relationship,
                )
            )
            created = True
    if created:
        session.commit()
    return {p.name: p for p in session.exec(select(PersonProfile)).all()}


def _close_stale_shifts(session: Session) -> None:
    now = datetime.utcnow()
    changed = False
    for shift in session.exec(select(Shift).where(Shift.ended_at == None)).all():  # noqa: E711
        if now - shift.started_at <= timedelta(hours=14):
            continue
        shift.ended_at = shift.started_at + timedelta(hours=8)
        session.add(shift)
        changed = True
    if changed:
        session.commit()


def _retire_old_demo_workers(session: Session, workers: dict[str, User]) -> None:
    fallback = workers.get("Goodluck")
    if not fallback:
        return
    leftover = [u for u in session.exec(select(User)).all() if u.display_name in _OLD_DEMO_WORKERS]
    if not leftover:
        return
    leftover_ids = {u.id for u in leftover}
    for event in session.exec(select(CareEvent)).all():
        if event.logger_id in leftover_ids:
            event.logger_id = fallback.id
            session.add(event)
    for row in leftover:
        session.delete(row)
    session.commit()


def _has_events(session: Session, person_id: int) -> bool:
    return session.exec(select(CareEvent).where(CareEvent.person_id == person_id)).first() is not None


def _seed_dad_if_needed(session: Session, dad: PersonProfile, logger: User) -> None:
    meds = session.exec(select(MedicationSchedule).where(MedicationSchedule.person_id == dad.id)).all()
    if not meds:
        session.add_all(
            [
                MedicationSchedule(
                    person_id=dad.id,
                    name="Donepezil",
                    dose="10mg",
                    times_per_day=1,
                    scheduled_times="20:00",
                    start_date=datetime(2026, 7, 1),
                    last_changed_at=DOSE_CHANGE,
                ),
                MedicationSchedule(
                    person_id=dad.id,
                    name="Ramipril",
                    dose="5mg",
                    times_per_day=1,
                    scheduled_times="08:00",
                    start_date=datetime(2026, 6, 1),
                ),
                MedicationSchedule(
                    person_id=dad.id,
                    name="Atorvastatin",
                    dose="20mg",
                    times_per_day=1,
                    scheduled_times="20:00",
                    start_date=datetime(2026, 6, 1),
                ),
            ]
        )
        session.commit()
    if _has_events(session, dad.id):
        return
    session.add_all(
        [
            CareEvent(
                person_id=dad.id,
                logger_id=logger.id,
                logged_at=datetime(2026, 8, 8, 19, 20),
                event_time=datetime(2026, 8, 8, 19, 10),
                type="meal",
                subtype="appetite_low",
                detail="barely touched dinner",
                raw_transcript="He barely touched dinner.",
                confidence=0.95,
            ),
            CareEvent(
                person_id=dad.id,
                logger_id=logger.id,
                logged_at=datetime(2026, 8, 9, 21, 0),
                event_time=datetime(2026, 8, 9, 20, 50),
                type="symptom",
                subtype="confusion",
                detail="agitated after the new tablet",
                raw_transcript="Agitated after the new tablet.",
                confidence=0.9,
            ),
            CareEvent(
                person_id=dad.id,
                logger_id=logger.id,
                logged_at=datetime(2026, 8, 9, 19, 15),
                event_time=datetime(2026, 8, 9, 19, 5),
                type="meal",
                subtype="appetite_low",
                detail="left most of his supper",
                raw_transcript="Left most of his supper.",
                confidence=0.92,
            ),
            CareEvent(
                person_id=dad.id,
                logger_id=logger.id,
                logged_at=datetime(2026, 8, 10, 21, 10),
                event_time=datetime(2026, 8, 10, 21, 5),
                type="symptom",
                subtype="confusion",
                detail="did not recognise me for a few minutes",
                raw_transcript="Didn't recognise me for a few minutes.",
                confidence=0.93,
            ),
            CareEvent(
                person_id=dad.id,
                logger_id=logger.id,
                logged_at=datetime(2026, 8, 10, 20, 55),
                event_time=datetime(2026, 8, 10, 20, 45),
                type="medication",
                subtype="dose_late",
                detail="evening medicines 45 minutes late",
                raw_transcript="Evening pills about 45 minutes late.",
                confidence=0.94,
            ),
            CareEvent(
                person_id=dad.id,
                logger_id=logger.id,
                logged_at=datetime(2026, 8, 10, 19, 20),
                event_time=datetime(2026, 8, 10, 19, 10),
                type="meal",
                subtype="appetite_low",
                detail="picked at dinner",
                raw_transcript="He only picked at dinner.",
                confidence=0.9,
            ),
            CareEvent(
                person_id=dad.id,
                logger_id=logger.id,
                logged_at=datetime(2026, 8, 11, 20, 55),
                event_time=datetime(2026, 8, 11, 20, 40),
                type="medication",
                subtype="dose_late",
                detail="evening medicines 40 minutes late",
                raw_transcript="Gave dad his 8pm meds, 40 minutes late.",
                confidence=0.95,
            ),
            CareEvent(
                person_id=dad.id,
                logger_id=logger.id,
                logged_at=datetime(2026, 8, 11, 19, 15),
                event_time=datetime(2026, 8, 11, 19, 5),
                type="meal",
                subtype="appetite_low",
                detail="barely touched dinner",
                raw_transcript="Barely touched dinner again.",
                confidence=0.91,
            ),
        ]
    )
    session.commit()


def _seed_able_if_needed(session: Session, able: PersonProfile, logger: User) -> None:
    if _has_events(session, able.id):
        return
    session.add_all(
        [
            CareEvent(
                person_id=able.id,
                logger_id=logger.id,
                logged_at=datetime(2026, 8, 7, 20, 10),
                event_time=datetime(2026, 8, 7, 19, 40),
                type="meal",
                subtype="eaten",
                detail="ate supper",
                raw_transcript="Able has eaten his supper.",
                confidence=0.9,
            ),
            CareEvent(
                person_id=able.id,
                logger_id=logger.id,
                logged_at=datetime(2026, 8, 7, 20, 20),
                event_time=datetime(2026, 8, 7, 20, 5),
                type="symptom",
                subtype="vomiting",
                detail="vomited after supper",
                raw_transcript="After eating he was vomiting.",
                confidence=0.92,
            ),
            CareEvent(
                person_id=able.id,
                logger_id=logger.id,
                logged_at=datetime(2026, 8, 8, 9, 10),
                event_time=datetime(2026, 8, 8, 8, 40),
                type="meal",
                subtype="eaten",
                detail="ate breakfast",
                raw_transcript="Able ate breakfast.",
                confidence=0.88,
            ),
            CareEvent(
                person_id=able.id,
                logger_id=logger.id,
                logged_at=datetime(2026, 8, 8, 9, 20),
                event_time=datetime(2026, 8, 8, 9, 0),
                type="symptom",
                subtype="vomiting",
                detail="vomited after breakfast",
                raw_transcript="He was sick again after food this morning.",
                confidence=0.91,
            ),
        ]
    )
    session.commit()


def _seed_other_patients(session: Session, people: dict[str, PersonProfile], workers: dict[str, User]) -> None:
    extras = [
        (
            "Margaret",
            workers["Abena"],
            [
                (datetime(2026, 8, 10, 8, 15), "meal", "eaten", "ate porridge", "Margaret ate her porridge."),
                (datetime(2026, 8, 11, 21, 0), "mood", "mood_low", "quiet and withdrawn", "Margaret was very quiet this evening."),
            ],
        ),
        (
            "Harold",
            workers["Okunola"],
            [
                (datetime(2026, 8, 9, 20, 20), "medication", "dose_late", "evening medicines 20 minutes late", "Harold's 8pm meds were 20 minutes late."),
                (datetime(2026, 8, 11, 7, 40), "symptom", "agitation", "restless at breakfast", "Harold was restless at breakfast."),
            ],
        ),
        (
            "Joyce",
            workers["Kemi"],
            [
                (datetime(2026, 8, 8, 19, 0), "meal", "appetite_low", "left most of supper", "Joyce left most of her supper."),
                (datetime(2026, 8, 10, 19, 10), "meal", "appetite_low", "picked at dinner", "Joyce only picked at dinner."),
            ],
        ),
        (
            "Ibrahim",
            workers["Goodluck"],
            [
                (datetime(2026, 8, 10, 14, 0), "symptom", "confusion", "did not know where he was", "Ibrahim did not know where he was after lunch."),
                (datetime(2026, 8, 11, 14, 20), "note", "note", "slept after lunch", "Ibrahim slept after lunch."),
            ],
        ),
        (
            "Evelyn",
            workers["Pelumi"],
            [
                (datetime(2026, 8, 9, 22, 0), "sleep", "note", "settled late", "Evelyn settled late, about 10pm."),
                (datetime(2026, 8, 11, 8, 10), "meal", "eaten", "ate breakfast", "Evelyn ate breakfast."),
            ],
        ),
        (
            "Frank",
            workers["Abena"],
            [
                (datetime(2026, 8, 8, 11, 0), "incident", "note", "needed two staff to stand", "Frank needed two of us to stand from the chair."),
                (datetime(2026, 8, 11, 16, 30), "mood", "mood_low", "tearful in the lounge", "Frank was tearful in the lounge."),
            ],
        ),
        (
            "Aisha",
            workers["Kemi"],
            [
                (datetime(2026, 8, 10, 9, 0), "meal", "eaten", "ate breakfast", "Aisha ate breakfast well."),
                (datetime(2026, 8, 11, 20, 10), "medication", "note", "evening medicines given on time", "Aisha took her 8pm meds on time."),
            ],
        ),
        (
            "George",
            workers["Okunola"],
            [
                (datetime(2026, 8, 9, 19, 30), "symptom", "confusion", "asked for his wife", "George asked for his wife several times."),
                (datetime(2026, 8, 11, 19, 40), "symptom", "confusion", "asked for his wife again", "George asked for his wife again this evening."),
            ],
        ),
    ]
    added = []
    for name, logger, rows in extras:
        person = people[name]
        if _has_events(session, person.id):
            continue
        for when, typ, subtype, detail, quote in rows:
            added.append(
                CareEvent(
                    person_id=person.id,
                    logger_id=logger.id,
                    logged_at=when,
                    event_time=when,
                    type=typ,
                    subtype=subtype,
                    detail=detail,
                    raw_transcript=quote,
                    confidence=0.9,
                )
            )
    if added:
        session.add_all(added)
        session.commit()


def _has_quote(session: Session, person_id: int, quote: str) -> bool:
    return any(
        (e.raw_transcript or "") == quote
        for e in session.exec(select(CareEvent).where(CareEvent.person_id == person_id)).all()
    )


def _apply_standout(session: Session, people: dict[str, PersonProfile], workers: dict[str, User]) -> None:
    now = datetime.utcnow()
    dad = people["Dou"]
    able = people["Able"]
    frank = people["Frank"]
    margaret = people["Margaret"]
    joyce = people["Joyce"]
    evelyn = people["Evelyn"]
    ravi = _ensure_family(session, dad)
    abena = workers.get("Abena") or workers.get("Goodluck")
    pelumi = workers.get("Pelumi") or workers.get("Goodluck")
    goodluck = workers.get("Goodluck")

    dad.hospital_return_at = now - timedelta(hours=20)
    dad.usual = dad.usual or "sits with the radio on"
    frank.usual = "sings in the lounge"
    frank.mobility = frank.mobility or "walks with a frame"
    margaret.risks = "chokes on thin fluids"
    able.risks = able.risks or ""
    if goodluck and goodluck.assigned_person_id != dad.id:
        goodluck.assigned_person_id = dad.id
        session.add(goodluck)
    session.add_all([dad, frank, margaret, able])
    session.commit()

    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    extras = [
        # Dou — today
        (dad, goodluck, today + timedelta(hours=8, minutes=10), "meal", "eaten", "ate porridge", "Dou ate his porridge this morning.", "staff"),
        (dad, abena, today + timedelta(hours=8, minutes=40), "medication", "dose_given", "morning tablets given", "Gave Dou his morning tablets on time.", "staff"),
        (dad, goodluck, today + timedelta(hours=11, minutes=20), "mood", "mood_low", "quiet in the lounge", "Dou was quiet in the lounge after coffee.", "staff"),
        # Dou — yesterday
        (dad, ravi, yesterday + timedelta(hours=19, minutes=5), "meal", "appetite_low", "barely touched supper", "Barely touched supper.", "from_home"),
        (dad, goodluck, yesterday + timedelta(hours=20, minutes=40), "medication", "dose_late", "evening medicines 25 minutes late", "Gave dad his evening meds 25 minutes late after hospital.", "staff"),
        (dad, abena, yesterday + timedelta(hours=21, minutes=10), "symptom", "confusion", "more confused this evening", "Dou was more confused again this evening.", "staff"),
        (dad, goodluck, yesterday + timedelta(hours=2, minutes=15), "sleep", "awake_night", "up at two", "Dou was up at two looking for his coat.", "staff"),
        # Dou — week patterns
        (dad, abena, now - timedelta(days=2, hours=3), "symptom", "confusion", "confused after supper", "Confused after supper again.", "staff"),
        (dad, goodluck, now - timedelta(days=3, hours=4), "medication", "dose_late", "evening medicines 40 minutes late", "Evening pills about 40 minutes late.", "staff"),
        (dad, ravi, now - timedelta(days=4, hours=5), "meal", "appetite_low", "left most of supper", "Left most of his supper at home.", "from_home"),
        # Able — meal then vomit story
        (able, pelumi, today + timedelta(hours=7, minutes=45), "meal", "eaten", "ate breakfast", "Able ate breakfast this morning.", "staff"),
        (able, pelumi, now - timedelta(days=1, hours=4), "meal", "eaten", "ate supper", "Able has eaten his supper.", "staff"),
        (able, pelumi, now - timedelta(days=1, hours=3, minutes=50), "symptom", "vomiting", "vomited after supper", "After eating he was vomiting.", "staff"),
        # Wing colour
        (frank, abena, now - timedelta(hours=1), "mood", "mood_low", "tearful in the lounge", "Frank was tearful just now.", "staff"),
        (margaret, abena, now - timedelta(hours=3), "meal", "appetite_low", "left her drink", "Margaret left her drink.", "staff"),
        (joyce, goodluck, today + timedelta(hours=9), "meal", "eaten", "ate toast", "Joyce ate toast for breakfast.", "staff"),
        (evelyn, pelumi, today + timedelta(hours=10), "sleep", "settled_late", "settled after ten", "Evelyn settled late after ten.", "staff"),
    ]
    changed = False
    for person, logger, when, typ, subtype, detail, quote, source in extras:
        if not logger:
            continue
        existing = next(
            (
                e
                for e in session.exec(select(CareEvent).where(CareEvent.person_id == person.id)).all()
                if (e.raw_transcript or "") == quote
            ),
            None,
        )
        if existing:
            existing.event_time = when
            existing.logged_at = when
            existing.type = typ
            existing.subtype = subtype
            existing.detail = detail
            existing.logger_id = logger.id
            existing.source = source
            session.add(existing)
            changed = True
            continue
        session.add(
            CareEvent(
                person_id=person.id,
                logger_id=logger.id,
                logged_at=when,
                event_time=when,
                type=typ,
                subtype=subtype,
                detail=detail,
                raw_transcript=quote,
                confidence=0.9,
                source=source,
            )
        )
        changed = True
    if changed:
        session.commit()
        recompute_flags(session, dad.id)
        recompute_flags(session, able.id)

def _backfill_person_ids(session: Session, dad: PersonProfile) -> None:
    changed = False
    for event in session.exec(select(CareEvent)).all():
        if event.person_id is None:
            event.person_id = dad.id
            session.add(event)
            changed = True
    for med in session.exec(select(MedicationSchedule)).all():
        if med.person_id is None:
            med.person_id = dad.id
            session.add(med)
            changed = True
    if changed:
        session.commit()
