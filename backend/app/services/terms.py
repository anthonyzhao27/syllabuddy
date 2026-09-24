"""UofT sessional-dates lookup used to turn "Week 6" into a calendar date."""

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

TERMS_PATH = Path(__file__).resolve().parent.parent / "data" / "uoft_terms.json"

SEASON_CODES = {
    "fall": "F",
    "winter": "W",
    "summer": "SY",
    "summer_first": "SF",
    "summer_second": "SS",
    "full_year": "F",
}
CAMPUS_TO_DIVISION = {
    "st_george": "artsci_stg",
    "mississauga": "utm",
    "scarborough": "utsc",
}


@dataclass
class TermDates:
    term_id: str
    division: str
    classes_start: date
    classes_end: date
    reading_week: tuple[date, date] | None = None
    exam_period: tuple[date, date] | None = None
    holidays: list[date] = field(default_factory=list)
    source: str = "table"  # "table" | "heuristic"


def _pair(v) -> tuple[date, date] | None:
    if not v:
        return None
    return (date.fromisoformat(v[0]), date.fromisoformat(v[1]))


@lru_cache(maxsize=1)
def _table() -> dict[tuple[str, str], TermDates]:
    if not TERMS_PATH.exists():
        return {}
    raw = json.loads(TERMS_PATH.read_text())
    out: dict[tuple[str, str], TermDates] = {}
    for t in raw.get("terms", []):
        try:
            td = TermDates(
                term_id=t["term_id"],
                division=t["division"],
                classes_start=date.fromisoformat(t["classes_start"]),
                classes_end=date.fromisoformat(t["classes_end"]),
                reading_week=_pair(t.get("reading_week")),
                exam_period=_pair(t.get("exam_period")),
                holidays=[date.fromisoformat(h["date"]) for h in t.get("holidays", [])],
            )
        except (KeyError, ValueError, TypeError):
            continue
        out[(td.term_id, td.division)] = td
    return out


def term_id_for(season: str, year: int) -> str:
    return f"{year}{SEASON_CODES.get(season, 'F')}"


def _labour_day(year: int) -> date:
    d = date(year, 9, 1)
    return d + timedelta(days=(0 - d.weekday()) % 7)


def _heuristic(season: str, year: int, division: str) -> TermDates:
    """Approximate UofT calendar when the table has no entry for this term."""
    if season in ("fall", "full_year"):
        start = _labour_day(year) + timedelta(days=2)  # Wednesday after Labour Day
        end = date(year, 12, 5) if season == "fall" else date(year + 1, 4, 4)
        rw_mon = date(year, 11, 1) + timedelta(
            days=(0 - date(year, 11, 1).weekday()) % 7
        )
        rw = (rw_mon, rw_mon + timedelta(days=4))
        exams = (end + timedelta(days=4), end + timedelta(days=18))
    elif season == "winter":
        jan5 = date(year, 1, 5)
        start = jan5 + timedelta(days=(0 - jan5.weekday()) % 7)
        end = start + timedelta(weeks=13, days=-3)
        feb = date(year, 2, 15)
        rw_mon = feb + timedelta(days=(0 - feb.weekday()) % 7)
        rw = (rw_mon, rw_mon + timedelta(days=4))
        exams = (end + timedelta(days=4), end + timedelta(days=20))
    else:  # summer, summer_first, summer_second
        start = date(year, 5, 5)
        start += timedelta(days=(0 - start.weekday()) % 7)
        end = date(year, 8, 8)
        if season == "summer_first":
            end = date(year, 6, 20)
        elif season == "summer_second":
            start = date(year, 7, 2)
            start += timedelta(days=(0 - start.weekday()) % 7)
        rw = None
        exams = (end + timedelta(days=3), end + timedelta(days=10))
    return TermDates(
        term_id=term_id_for(season, year),
        division=division,
        classes_start=start,
        classes_end=end,
        reading_week=rw,
        exam_period=exams,
        source="heuristic",
    )


def lookup(season: str, year: int, division: str) -> TermDates:
    """Return sessional dates for a term, falling back sensibly.

    Full-year courses use the fall term's start plus the winter term's end and
    both reading weeks are handled by the resolver via ``extra_breaks``.
    """
    table = _table()
    tid = term_id_for(season, year)
    for div in (division, "artsci_stg"):
        hit = table.get((tid, div))
        if hit:
            if season == "full_year":
                winter = table.get((f"{year + 1}W", div))
                if winter:
                    return TermDates(
                        term_id=f"{year}Y",
                        division=div,
                        classes_start=hit.classes_start,
                        classes_end=winter.classes_end,
                        reading_week=hit.reading_week,
                        exam_period=winter.exam_period,
                        holidays=hit.holidays + winter.holidays,
                    )
            return hit
    return _heuristic(season, year, division)


def breaks_for(term: TermDates, season: str, year: int) -> list[tuple[date, date, str]]:
    """All no-class stretches inside the term as (start, end, kind).

    kind is "reading" (some syllabi give it a week number) or "holiday".
    """
    out = []
    if term.reading_week:
        out.append((*term.reading_week, "reading"))
    if season == "full_year":
        winter = lookup("winter", year + 1, term.division)
        # December exams + holiday break: from end of fall classes to winter start
        fall = lookup("fall", year, term.division)
        out.append(
            (
                fall.classes_end + timedelta(days=1),
                winter.classes_start - timedelta(days=1),
                "holiday",
            )
        )
        if winter.reading_week:
            out.append((*winter.reading_week, "reading"))
    return out


def candidate_terms_near(today: date) -> list[tuple[str, int]]:
    """(season, year) pairs a student uploading on ``today`` most likely means."""
    y, m = today.year, today.month
    if m >= 8:
        return [("fall", y), ("winter", y + 1)]
    if m <= 3:
        return [("winter", y), ("fall", y - 1)]
    if m == 4:
        return [("summer", y), ("winter", y)]
    return [("summer", y), ("fall", y)]
