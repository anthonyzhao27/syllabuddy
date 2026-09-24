"""Tests for deterministic week/date resolution."""

from datetime import date, datetime

import pytest

from app.models.schemas import LLMSyllabus, TermOverride
from app.services import date_resolver, terms
from app.services.terms import TermDates

WINTER_2026 = TermDates(
    term_id="2026W",
    division="artsci_stg",
    classes_start=date(2026, 1, 5),
    classes_end=date(2026, 4, 2),
    reading_week=(date(2026, 2, 16), date(2026, 2, 20)),
    exam_period=(date(2026, 4, 7), date(2026, 4, 28)),
)
FALL_2025 = TermDates(
    term_id="2025F",
    division="artsci_stg",
    classes_start=date(2025, 9, 2),
    classes_end=date(2025, 12, 2),
    reading_week=(date(2025, 10, 27), date(2025, 10, 31)),
    exam_period=(date(2025, 12, 5), date(2025, 12, 20)),
)


@pytest.fixture(autouse=True)
def fixed_table(monkeypatch):
    table = {
        ("2026W", "artsci_stg"): WINTER_2026,
        ("2025F", "artsci_stg"): FALL_2025,
    }
    monkeypatch.setattr(terms, "_table", lambda: table)


def _event(**kw):
    base = {
        "title": "Item",
        "event_type": "assignment",
        "description": "",
        "date_kind": "week",
        "date": None,
        "stated_weekday": None,
        "week": None,
        "in_class": False,
        "meeting_kind": None,
        "time": None,
        "duration_minutes": None,
        "source_text": "",
    }
    base.update(kw)
    return base


def _syllabus(
    events=(),
    recurring=(),
    meetings=(),
    season="winter",
    year=None,
    anchor=None,
    numbered=False,
    week_dates=(),
):
    return LLMSyllabus.model_validate(
        {
            "course_code": "CSC263H1S",
            "term": {
                "season": season,
                "year": year,
                "campus": "st_george",
                "evidence": "",
            },
            "schedule_anchor": {
                "week1_month": anchor[0] if anchor else None,
                "week1_day": anchor[1] if anchor else None,
                "evidence": "",
                "reading_week_numbered": numbered,
            },
            "meetings": list(meetings),
            "week_dates": [{"week": w, "month": m, "day": d} for w, m, d in week_dates],
            "events": list(events),
            "recurring": list(recurring),
        }
    )


LECTURES = [
    {
        "kind": "lecture",
        "weekday": "tuesday",
        "start_time": "10:00",
        "end_time": "11:00",
    },
    {
        "kind": "lecture",
        "weekday": "thursday",
        "start_time": "10:00",
        "end_time": "11:00",
    },
    {
        "kind": "tutorial",
        "weekday": "friday",
        "start_time": "13:00",
        "end_time": "14:00",
    },
]
UPLOAD = date(2025, 12, 29)


def _only(ext, today=UPLOAD, override=None, text=None):
    events, ctx = date_resolver.resolve(
        date_resolver.sanitize(ext, text), today, override
    )
    return events, ctx


class TestWeekResolution:
    def test_week_without_day_is_monday_estimated(self):
        events, ctx = _only(_syllabus([_event(week=3)]))
        assert ctx.week1_monday == date(2026, 1, 5)
        assert events[0].due_date.date() == date(2026, 1, 19)
        assert events[0].date_confidence == "estimated"
        assert events[0].time_specified is False

    def test_stated_weekday_is_inferred(self):
        events, _ = _only(
            _syllabus(
                [
                    _event(
                        week=5,
                        stated_weekday="friday",
                        time="23:59",
                        source_text="Fri of week 5",
                    )
                ]
            )
        )
        assert events[0].due_date == datetime(2026, 2, 6, 23, 59)
        assert events[0].date_confidence == "inferred"

    def test_reading_week_skipped_when_not_numbered(self):
        events, _ = _only(_syllabus([_event(week=7)]))
        # weeks 1-6 = Jan 5..Feb 9, reading week Feb 16, week 7 = Feb 23
        assert events[0].due_date.date() == date(2026, 2, 23)

    def test_reading_week_counted_when_numbered(self):
        events, _ = _only(_syllabus([_event(week=8)], numbered=True))
        assert events[0].due_date.date() == date(2026, 2, 23)

    def test_in_class_uses_meeting_day_and_time(self):
        ext = _syllabus(
            [_event(week=7, in_class=True, meeting_kind="tutorial", event_type="exam")],
            meetings=LECTURES,
        )
        events, _ = _only(ext)
        assert events[0].due_date == datetime(2026, 2, 27, 13, 0)
        assert events[0].time_specified is True

    def test_syllabus_anchor_overrides_table(self):
        events, ctx = _only(_syllabus([_event(week=2)], anchor=(1, 12)))
        assert ctx.anchor_source == "syllabus_anchor"
        assert events[0].due_date.date() == date(2026, 1, 19)

    def test_anchor_from_events_with_week_and_date(self):
        evs = [
            _event(
                title="A1",
                date_kind="explicit_date",
                date={"month": 1, "day": 23, "year": None},
                week=3,
            ),
            _event(
                title="A2",
                date_kind="explicit_date",
                date={"month": 2, "day": 6, "year": None},
                week=5,
            ),
            _event(title="Test", week=6),
        ]
        events, ctx = _only(_syllabus(evs))
        # Jan 23 in week 3 => week 1 = Jan 5 (table agrees)
        assert ctx.week1_monday == date(2026, 1, 5)
        test = next(e for e in events if e.title == "Test")
        assert test.due_date.date() == date(2026, 2, 9)

    def test_user_override_moves_week_dates(self):
        ext = _syllabus([_event(week=2)])
        events, ctx = _only(ext, override=TermOverride(week1_monday=date(2026, 1, 12)))
        assert ctx.anchor_source == "user"
        assert events[0].due_date.date() == date(2026, 1, 19)


class TestExplicitDates:
    def test_year_from_term(self):
        ext = _syllabus(
            [
                _event(
                    date_kind="explicit_date",
                    date={"month": 3, "day": 13, "year": None},
                )
            ]
        )
        events, _ = _only(ext)
        assert events[0].due_date.date() == date(2026, 3, 13)
        assert events[0].date_confidence == "exact"

    def test_fall_term_january_date_is_next_year(self):
        ext = _syllabus(
            [
                _event(
                    date_kind="explicit_date", date={"month": 1, "day": 8, "year": None}
                )
            ],
            season="full_year",
            year=2025,
        )
        events, _ = _only(ext, today=date(2025, 8, 26))
        assert events[0].due_date.date().year == 2026

    def test_weekday_votes_pick_year_when_unstated(self):
        # Mon Sep 8, Wed Oct 1, Fri Nov 14 are all correct weekdays in 2025
        evs = [
            _event(
                title="a",
                date_kind="explicit_date",
                date={"month": 9, "day": 8, "year": None},
                stated_weekday="monday",
                source_text="Mon Sept 8",
            ),
            _event(
                title="b",
                date_kind="explicit_date",
                date={"month": 10, "day": 1, "year": None},
                stated_weekday="wednesday",
                source_text="Wed. Oct 1",
            ),
            _event(
                title="c",
                date_kind="explicit_date",
                date={"month": 11, "day": 14, "year": None},
                stated_weekday="friday",
                source_text="Friday, November 14",
            ),
        ]
        events, ctx = _only(_syllabus(evs, season="fall"), today=date(2026, 8, 30))
        assert ctx.year == 2025
        assert ctx.year_source == "weekday_votes"

    def test_in_class_explicit_date_takes_meeting_time(self):
        ext = _syllabus(
            [
                _event(
                    date_kind="explicit_date",
                    date={"month": 2, "day": 26, "year": None},
                    in_class=True,
                    event_type="exam",
                )
            ],
            meetings=LECTURES,
        )
        events, _ = _only(ext)
        assert events[0].due_date == datetime(2026, 2, 26, 10, 0)

    def test_exam_period_is_estimated_start(self):
        events, _ = _only(
            _syllabus(
                [_event(title="Final Exam", date_kind="exam_period", event_type="exam")]
            )
        )
        assert events[0].due_date.date() == date(2026, 4, 7)
        assert events[0].date_confidence == "estimated"

    def test_tbd_dropped(self):
        events, _ = _only(_syllabus([_event(date_kind="tbd")]))
        assert events == []


class TestRecurring:
    def _rec(self, **kw):
        base = {
            "title": "Quiz",
            "event_type": "quiz",
            "description": "",
            "weekday": "tuesday",
            "in_class": True,
            "meeting_kind": "lecture",
            "time": None,
            "weeks": [],
            "first_date": None,
            "last_date": None,
            "every_n_weeks": 1,
            "excluded_weeks": [],
            "duration_minutes": None,
            "source_text": "",
        }
        base.update(kw)
        return base

    def test_week_list_expansion(self):
        ext = _syllabus(recurring=[self._rec(weeks=[2, 6, 7])], meetings=LECTURES)
        events, _ = _only(ext)
        assert [e.due_date for e in events] == [
            datetime(2026, 1, 13, 10, 0),
            datetime(2026, 2, 10, 10, 0),
            datetime(2026, 2, 24, 10, 0),
        ]

    def test_date_range_skips_reading_week(self):
        ext = _syllabus(
            recurring=[
                self._rec(
                    first_date={"month": 2, "day": 3, "year": None},
                    last_date={"month": 3, "day": 3, "year": None},
                )
            ],
            meetings=LECTURES,
        )
        events, _ = _only(ext)
        dates = [e.due_date.date() for e in events]
        assert date(2026, 2, 17) not in dates
        assert dates[0] == date(2026, 2, 3) and dates[-1] == date(2026, 3, 3)


def test_dedupes_same_title_same_day():
    evs = [
        _event(
            title="Midterm",
            date_kind="explicit_date",
            date={"month": 2, "day": 26, "year": None},
        ),
        _event(
            title="midterm",
            date_kind="explicit_date",
            date={"month": 2, "day": 26, "year": None},
        ),
    ]
    events, _ = _only(_syllabus(evs))
    assert len(events) == 1


def test_heuristic_when_term_missing_from_table():
    ext = _syllabus([_event(week=1)], season="fall", year=2031)
    events, ctx = _only(ext, today=date(2031, 8, 25))
    assert ctx.anchor_source == "heuristic"
    assert events[0].due_date.date().weekday() == 0


class TestGrounding:
    def test_unquoted_weekday_is_ignored(self):
        # "Quiz 1" row never prints a weekday; the model's guess must not count
        ext = _syllabus(
            [_event(week=3, stated_weekday="wednesday", source_text="Quiz 1")]
        )
        events, _ = _only(ext)
        assert events[0].due_date.date() == date(2026, 1, 19)
        assert events[0].date_confidence == "estimated"

    def test_hallucinated_weekdays_do_not_flip_stated_year(self):
        # Wednesdays in 2024, but nothing in source_text says "Wednesday"
        evs = [
            _event(
                title=f"q{i}",
                date_kind="explicit_date",
                date={"month": 9, "day": d, "year": None},
                stated_weekday="wednesday",
                source_text=f"Sep. {d} Quiz",
            )
            for i, d in enumerate((11, 18, 25))
        ]
        _, ctx = _only(
            _syllabus(evs, season="fall", year=2025), today=date(2025, 8, 26)
        )
        assert ctx.year == 2025

    def test_ungrounded_date_falls_back_to_week(self):
        ext = _syllabus(
            [
                _event(
                    date_kind="explicit_date",
                    date={"month": 3, "day": 5, "year": None},
                    week=4,
                    source_text="Week 4 essay",
                )
            ]
        )
        events, _ = _only(ext)
        assert events[0].due_date.date() == date(2026, 1, 26)

    def test_last_class_uses_final_meeting(self):
        ext = _syllabus(
            [
                _event(
                    date_kind="explicit_date",
                    date={"month": 12, "day": 5, "year": None},
                    source_text="Last class",
                    in_class=True,
                )
            ],
            meetings=LECTURES,
        )
        events, _ = _only(ext)
        # classes end Thu Apr 2 2026; last lecture = Thu Apr 2 10:00
        assert events[0].due_date == datetime(2026, 4, 2, 10, 0)


class TestWeekDates:
    def test_row_date_used_for_week_item(self):
        ext = _syllabus(
            [_event(week=4, time="23:59")], week_dates=[(1, 1, 7), (4, 1, 28)]
        )
        events, _ = _only(ext)
        assert events[0].due_date == datetime(2026, 1, 28, 23, 59)
        assert events[0].date_confidence == "inferred"

    def test_rows_fit_week1_and_reading_week_numbering(self):
        # rows: wk1 Jan 13, wk6 Feb 17 is only possible if reading week is numbered
        rows = [(1, 1, 13), (2, 1, 20), (6, 2, 17), (7, 2, 24)]
        ext = _syllabus([_event(week=9)], week_dates=rows, numbered=False)
        events, ctx = _only(ext)
        assert ctx.week1_monday == date(2026, 1, 12)
        assert ctx.reading_week_numbered is True
        assert ctx.anchor_source == "syllabus_dates"


def test_weekday_grounded_by_surrounding_text():
    rec = {
        "title": "PCRS",
        "event_type": "quiz",
        "description": "",
        "weekday": "tuesday",
        "in_class": False,
        "meeting_kind": None,
        "time": "10:00",
        "weeks": [2],
        "first_date": None,
        "last_date": None,
        "every_n_weeks": 1,
        "excluded_weeks": [],
        "duration_minutes": None,
        "source_text": "Lecture Preparation (PCRS) 5% (best 10 of 11",
    }
    text = (
        "Lecture Preparation (PCRS) 5% (best 10 of 11)\n"
        "Tuesdays before 10:00am (weeks 2 - 12)"
    )
    events, _ = _only(_syllabus(recurring=[rec]), text=text)
    assert events[0].due_date == datetime(2026, 1, 13, 10, 0)
    events, _ = _only(_syllabus(recurring=[rec]))
    assert events[0].due_date.date() == date(2026, 1, 12)


def _rec(**kw):
    base = {
        "title": "Quiz",
        "event_type": "quiz",
        "description": "",
        "weekday": None,
        "in_class": False,
        "meeting_kind": None,
        "time": None,
        "weeks": [],
        "first_date": None,
        "last_date": None,
        "every_n_weeks": 1,
        "excluded_weeks": [],
        "duration_minutes": None,
        "source_text": "",
    }
    base.update(kw)
    return base


def test_participation_is_not_a_calendar_event():
    ext = _syllabus(
        [_event(title="Class Participation", week=3)],
        recurring=[_rec(title="Participation", weeks=[1, 2])],
    )
    events, _ = _only(ext)
    assert events == []


def test_vague_cadence_recurring_dropped():
    ext = _syllabus(
        recurring=[
            _rec(weeks=[2, 4, 6], source_text="Quizzes will be roughly bi-weekly")
        ]
    )
    events, _ = _only(ext)
    assert events == []


def test_invented_recurring_range_dropped():
    text = (
        "Eight tasks/quizzes associated with eight reading assignments "
        "are to be completed."
    )
    ext = _syllabus(
        recurring=[
            _rec(
                weekday="monday",
                source_text="Eight tasks/quizzes associated with eight reading",
                first_date={"month": 1, "day": 12, "year": None},
                last_date={"month": 3, "day": 30, "year": None},
            )
        ]
    )
    events, _ = _only(ext, text=text)
    assert events == []


def test_slash_dates_become_two_events():
    ext = _syllabus(
        [
            _event(
                title="Lab 1",
                date_kind="explicit_date",
                date={"month": 1, "day": 29, "year": None},
                source_text="Lab 1 10% Jan. 29/2",
            )
        ]
    )
    events, _ = _only(ext)
    assert [e.due_date.date() for e in events] == [date(2026, 1, 29), date(2026, 2, 2)]


def test_midterm_never_placed_in_final_exam_period():
    events, _ = _only(
        _syllabus(
            [_event(title="Midterm exam", date_kind="exam_period", event_type="exam")]
        )
    )
    assert events == []


def test_tutorial_quiz_does_not_borrow_lecture_day():
    lectures_only = [m for m in LECTURES if m["kind"] == "lecture"]
    ext = _syllabus(
        [_event(week=3, in_class=True, meeting_kind="tutorial", event_type="quiz")],
        meetings=lectures_only,
    )
    events, _ = _only(ext)
    assert events[0].due_date.date() == date(2026, 1, 19)
    assert events[0].date_confidence == "estimated"


def test_slash_dates_not_duplicated_when_model_already_split():
    evs = [
        _event(
            title="Lab 1 (PRA0101)",
            date_kind="explicit_date",
            date={"month": 1, "day": 26, "year": None},
            source_text="Lab 1 10% Jan. 26/29",
        ),
        _event(
            title="Lab 1 (PRA0102)",
            date_kind="explicit_date",
            date={"month": 1, "day": 29, "year": None},
            source_text="Lab 1 10% Jan. 26/29",
        ),
    ]
    events, _ = _only(_syllabus(evs))
    assert len(events) == 2


def test_listed_instances_beat_recurring_rule():
    evs = [
        _event(
            title="TQs 3,4",
            date_kind="explicit_date",
            date={"month": 1, "day": 15, "year": None},
            source_text="Jan 15 TQs 3,4",
        )
    ]
    rec = _rec(
        title="Textbook Questions",
        event_type="assignment",
        weekday="thursday",
        weeks=[2, 3],
        source_text="due every Thursday",
    )
    events, _ = _only(_syllabus(evs, recurring=[rec]))
    assert [(e.title, e.due_date.date()) for e in events] == [
        ("TQs 3,4", date(2026, 1, 15)),
        ("Textbook Questions", date(2026, 1, 22)),
    ]


def test_same_stream_matching():
    assert date_resolver._same_stream("Weekly Textbook Questions", "TQs 3,4")
    assert date_resolver._same_stream("Weekly Quiz", "Quiz 3")
    assert not date_resolver._same_stream("Weekly Textbook Questions", "RCT Report")


def test_same_time_recurring_streams_merge():
    a = _rec(
        title="Homework Quiz",
        weekday="tuesday",
        weeks=[2, 3],
        time="09:00",
        source_text="Due Tuesdays 9am",
    )
    b = _rec(
        title="Homework Written",
        weekday="tuesday",
        weeks=[2, 3],
        time="09:00",
        source_text="Due Tuesdays 9am",
    )
    events, _ = _only(_syllabus(recurring=[a, b]))
    assert [e.title for e in events] == ["Homework Quiz / Homework Written"] * 2


def test_non_uoft_syllabus_anchor_marked_as_guess():
    ext = _syllabus([_event(week=2)])
    ext = ext.model_copy(
        update={
            "course_code": "CS 101",
            "term": ext.term.model_copy(update={"campus": "unknown", "evidence": ""}),
        }
    )
    _, ctx = _only(ext)
    assert ctx.anchor_source == "heuristic"


def test_uoft_code_keeps_table_anchor():
    ext = _syllabus([_event(week=2)])
    ext = ext.model_copy(
        update={"term": ext.term.model_copy(update={"campus": "unknown"})}
    )
    _, ctx = _only(ext)  # course_code CSC263H1S
    assert ctx.anchor_source == "table"


def test_source_keys_stable_across_redates():
    ext = _syllabus(
        [_event(title="Essay", week=3)],
        recurring=[
            _rec(title="Quiz", weekday="tuesday", weeks=[2, 3, 4], source_text="Tue")
        ],
    )
    a, _ = _only(ext)
    b, _ = _only(ext, override=TermOverride(year=2027))
    key = {e.source_key: e.title for e in a}
    assert key == {e.source_key: e.title for e in b}
    assert set(key) == {"e0", "r0:0", "r0:1", "r0:2"}
