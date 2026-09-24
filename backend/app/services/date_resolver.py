"""Deterministic resolution of LLM-transcribed schedule refs to calendar dates.

The LLM only transcribes what the syllabus says (month/day as written, week
numbers, meeting days, term). Everything that needs calendar arithmetic —
which year, which Monday is "Week 6", skipping reading week — happens here so
it is testable and can be re-run with a user-corrected anchor at no LLM cost.
"""

import logging
import re
from datetime import date, datetime, time, timedelta

from app.models.schemas import (
    EventType,
    LLMEvent,
    LLMRecurring,
    LLMSyllabus,
    MonthDay,
    ParsedEvent,
    TermContext,
    TermOverride,
)
from app.services import terms

logger = logging.getLogger(__name__)

WEEKDAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]
SEASON_LABEL = {
    "fall": "Fall",
    "winter": "Winter",
    "summer": "Summer",
    "summer_first": "Summer (first half)",
    "summer_second": "Summer (second half)",
    "full_year": "Fall–Winter",
}
CAMPUS_LABEL = {"st_george": "St. George", "mississauga": "UTM", "scarborough": "UTSC"}
TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})")
# Faculty of Applied Science & Engineering course prefixes (own sessional dates)
# UofT-style course codes: CSC148H1, MAT135H5F, PSYA01H3, CSC2541H, ECO100Y1Y
UOFT_CODE_RE = re.compile(r"\b[A-Z]{3}[A-D]?\s?\d{2,4}[HY][0135]?[FSY]?\b")
ENGINEERING_CODE_RE = re.compile(
    r"^\s*(APS|ECE|MIE|CIV|CHE|MSE|ESC|BME|AER|MIN|CME|TEP)\s*\d", re.IGNORECASE
)
MAX_WEEK = 30
WEEKDAY_TOKENS = {
    "monday": r"mon(day)?",
    "tuesday": r"tue(s|sday)?",
    "wednesday": r"wed(s|nesday)?",
    "thursday": r"thu(r|rs|rsday)?",
    "friday": r"fri(day)?",
    "saturday": r"sat(urday)?",
    "sunday": r"sun(day)?",
}


def _monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _parse_time(s: str | None) -> time | None:
    if not s:
        return None
    m = TIME_RE.match(s.strip())
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    if 0 <= h <= 23 and 0 <= mi <= 59:
        return time(h, mi)
    return None


def _year_for_month(season: str, start_year: int, month: int) -> int:
    if season in ("fall", "full_year"):
        return start_year if month >= 7 else start_year + 1
    if season == "winter":
        return start_year - 1 if month >= 9 else start_year
    return start_year


def _safe_date(y: int, m: int, d: int) -> date | None:
    try:
        return date(y, m, d)
    except ValueError:
        return None


def _to_date(md: MonthDay, season: str, start_year: int) -> date | None:
    y = md.year if md.year else _year_for_month(season, start_year, md.month)
    return _safe_date(y, md.month, md.day)


# --------------------------------------------------------------------------
# Term inference
# --------------------------------------------------------------------------


def _explicit_dates(ext: LLMSyllabus) -> list[tuple[MonthDay, str | None]]:
    out = []
    for e in ext.events:
        if e.date is not None:
            out.append((e.date, e.stated_weekday))
    for r in ext.recurring:
        for md in (r.first_date, r.last_date):
            if md is not None:
                out.append((md, r.weekday))
    return out


def _infer_season(ext: LLMSyllabus, today: date) -> str:
    if ext.term.season != "unknown":
        return ext.term.season
    months = [md.month for md, _ in _explicit_dates(ext)]
    if months:
        fall = sum(8 <= m <= 12 for m in months)
        winter = sum(1 <= m <= 4 for m in months)
        summer = sum(5 <= m <= 8 for m in months)
        if fall and winter and min(fall, winter) >= 2:
            return "full_year"
        best = max((fall, "fall"), (winter, "winter"), (summer, "summer"))
        if best[0]:
            return best[1]
    return terms.candidate_terms_near(today)[0][0]


def _weekday_votes(ext: LLMSyllabus, season: str, start_year: int) -> tuple[int, int]:
    """(matches, checked) of stated weekdays vs. the calendar in start_year."""
    hits = checked = 0
    for md, wd in _explicit_dates(ext):
        if not wd or md.year:
            continue
        d = _safe_date(_year_for_month(season, start_year, md.month), md.month, md.day)
        if d is None:
            continue
        checked += 1
        hits += WEEKDAYS[d.weekday()] == wd
    return hits, checked


def _infer_year(ext: LLMSyllabus, season: str, today: date) -> tuple[int, str]:
    base = "summer" if season.startswith("summer") else season
    near = next((y for s, y in terms.candidate_terms_near(today) if s == base), None)
    if near is None:
        near = today.year if season != "winter" or today.month < 8 else today.year + 1
    stated = ext.term.year
    if stated and season == "winter" and ext.term.season == "full_year":
        stated -= 1
    cands = {near - 1, near, near + 1}
    if stated:
        cands |= {stated - 1, stated, stated + 1}
    votes = {y: _weekday_votes(ext, season, y) for y in cands}
    checked = max((c for _, c in votes.values()), default=0)
    if stated:
        s_hits = votes[stated][0]
        best_y, (b_hits, _) = max(
            votes.items(), key=lambda kv: (kv[1][0], kv[0] == stated)
        )
        # Only override an explicitly stated year on strong weekday evidence
        if checked >= 3 and b_hits >= s_hits + 2 and b_hits >= 0.8 * checked:
            return best_y, "weekday_votes"
        return stated, "stated"
    if checked >= 2:
        best_hits = max(h for h, _ in votes.values())
        if best_hits >= 0.6 * checked:
            tied = [y for y, (h, _) in votes.items() if h == best_hits]
            return min(tied, key=lambda y: abs(y - near)), "weekday_votes"
    return near, "upload_date"


# --------------------------------------------------------------------------
# Week grid
# --------------------------------------------------------------------------


class WeekGrid:
    def __init__(
        self,
        week1_monday: date,
        breaks: list[tuple[date, date, str]],
        numbered_rw: bool,
    ):
        self.week1 = week1_monday
        self.breaks = [(_monday(s), e, kind) for s, e, kind in breaks]
        self.numbered_rw = numbered_rw

    def _is_break(self, monday: date) -> bool:
        for s, e, kind in self.breaks:
            if s <= monday <= e:
                return not (self.numbered_rw and kind == "reading")
        return False

    def monday_of(self, week: int) -> date:
        m = self.week1
        count = 1
        guard = 0
        while count < week and guard < 80:
            m += timedelta(days=7)
            guard += 1
            if self._is_break(m):
                continue
            count += 1
        while self._is_break(m) and guard < 80:
            m += timedelta(days=7)
            guard += 1
        return m

    def week_of(self, d: date) -> int | None:
        target = _monday(d)
        if target < self.week1 or self._is_break(target):
            return None
        m, count = self.week1, 1
        while m < target and count < 80:
            m += timedelta(days=7)
            if not self._is_break(m):
                count += 1
        return count


def _week_date_pairs(
    ext: LLMSyllabus, season: str, year: int
) -> list[tuple[int, date]]:
    """(week number, printed date) pairs: schedule rows + events giving both."""
    pairs = []
    for wd in ext.week_dates:
        d = _safe_date(_year_for_month(season, year, wd.month), wd.month, wd.day)
        if d and 1 <= wd.week <= MAX_WEEK:
            pairs.append((wd.week, d))
    for e in ext.events:
        if e.week and e.date and 1 <= e.week <= MAX_WEEK:
            d = _to_date(e.date, season, year)
            if d:
                pairs.append((e.week, d))
    return pairs


def _fit_grid(
    pairs: list[tuple[int, date]],
    breaks,
    numbered_hint: bool,
    table_week1: date,
    fixed_week1: date | None = None,
) -> tuple[date, bool, int] | None:
    """Week-1 Monday + reading-week numbering that best explain printed pairs."""
    if not pairs:
        return None
    if fixed_week1:
        cands = {fixed_week1}
    else:
        cands = set()
        for w, d in pairs:
            base = _monday(d) - timedelta(days=7 * (w - 1))
            cands |= {base - timedelta(days=7 * k) for k in range(4)}
    best = None
    for wk1 in cands:
        for numbered in (numbered_hint, not numbered_hint):
            grid = WeekGrid(wk1, breaks, numbered)
            score = sum(grid.week_of(d) == w for w, d in pairs)
            key = (score, numbered == numbered_hint, -abs((wk1 - table_week1).days))
            if best is None or key > best[0]:
                best = (key, wk1, numbered, score)
    _, wk1, numbered, score = best
    if score < 1 or (len(pairs) >= 3 and score < 0.5 * len(pairs)):
        return None
    return wk1, numbered, score


# --------------------------------------------------------------------------
# Grounding guardrails: distrust fields the syllabus text doesn't support
# --------------------------------------------------------------------------


def _weekday_grounded(wd: str, text: str) -> bool:
    return (
        re.search(rf"\b(?:{WEEKDAY_TOKENS[wd]})s?\b", text, re.IGNORECASE) is not None
    )


def _day_grounded(md: MonthDay, text: str) -> bool:
    return re.search(rf"(?<!\d){md.day}(?!\d)", text) is not None


GROUNDING_WINDOW = 400
MONTHS = {
    m: i + 1
    for i, m in enumerate(
        [
            "jan",
            "feb",
            "mar",
            "apr",
            "may",
            "jun",
            "jul",
            "aug",
            "sep",
            "oct",
            "nov",
            "dec",
        ]
    )
}
# "Jan. 19/22", "Feb 16 / 26": two sittings/sections of one item
SLASH_DATES_RE = re.compile(r"\b([A-Za-z]{3,9})\.?\s*(\d{1,2})\s*/\s*(\d{1,2})\b")
FINAL_RE = re.compile(r"\b(final|exam(ination)?)\b", re.IGNORECASE)
MIDTERM_RE = re.compile(r"\b(mid-?term|term test|test \d)\b", re.IGNORECASE)
# Graded, but never a calendar deadline
NOT_A_DEADLINE_RE = re.compile(
    r"\b(participation|attendance|engagement)\b", re.IGNORECASE
)
# "roughly bi-weekly", "periodic" quizzes: no usable schedule
VAGUE_CADENCE_RE = re.compile(
    r"\b(roughly|approximately|about|periodic(ally)?|occasional(ly)?"
    r"|several|random(ly)?|pop)\b",
    re.IGNORECASE,
)


def _squash(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def _context_for(source_text: str, text_sq: str | None) -> str | None:
    """source_text plus the syllabus text around every place it was quoted from.

    Returns None when the full text is available but the quote can't be found
    in it (paraphrased), meaning "can't verify".
    """
    if not text_sq:
        return source_text
    src = _squash(source_text)
    for probe in (src[:40], src[-40:], src[:20]):
        if len(probe) < 8:
            continue
        spans = [m.start() for m in re.finditer(re.escape(probe), text_sq)]
        if spans:
            parts = [
                text_sq[
                    max(0, pos - GROUNDING_WINDOW) : pos + len(src) + GROUNDING_WINDOW
                ]
                for pos in spans[:5]
            ]
            return source_text + " " + " ".join(parts)
    return None


def _meeting_days(ext: LLMSyllabus, kind: str | None) -> set[str]:
    return {m.weekday for m in ext.meetings if kind is None or m.kind == kind}


def _keep_weekday(
    wd: str, source_text: str, text_sq: str | None, meeting_days: set[str]
) -> bool:
    if wd in meeting_days:
        return True
    ctx_text = _context_for(source_text, text_sq)
    return ctx_text is None or _weekday_grounded(wd, ctx_text)


def _slash_second_date(e: LLMEvent) -> LLMEvent | None:
    """Source says "Jan. 19/22" but the model kept only the 19th: add the 22nd."""
    if e.date_kind != "explicit_date" or e.date is None:
        return None
    for m in SLASH_DATES_RE.finditer(e.source_text):
        month = MONTHS.get(m.group(1)[:3].lower())
        d1, d2 = int(m.group(2)), int(m.group(3))
        if month != e.date.month or d1 != e.date.day or d2 == d1:
            continue
        month2 = month if d2 > d1 else month % 12 + 1
        date2 = e.date.model_copy(update={"month": month2, "day": d2})
        return e.model_copy(
            update={
                "date": date2,
                "stated_weekday": None,
                "title": f"{e.title} (second date)",
            }
        )
    return None


def sanitize(ext: LLMSyllabus, text: str | None = None) -> LLMSyllabus:
    """Drop weekdays/dates the model asserted but the syllabus doesn't show.

    Models tend to "helpfully" compute a weekday for a printed date (using the
    wrong year) or invent a date for "last class". Those poison year inference
    and week anchoring. A weekday survives if it is printed near the quoted
    source_text, is one of the course's meeting days, or the quote can't be
    located to check.
    """
    text_sq = _squash(text) if text else None
    events = []
    for e in ext.events:
        if NOT_A_DEADLINE_RE.search(e.title):
            continue
        upd = {}
        if e.stated_weekday:
            # For printed dates the weekday only feeds year inference, so
            # require it to be literally present rather than merely plausible.
            days = (
                set()
                if e.date_kind == "explicit_date"
                else _meeting_days(ext, e.meeting_kind)
            )
            if not _keep_weekday(e.stated_weekday, e.source_text, text_sq, days):
                upd["stated_weekday"] = None
        if (
            e.date_kind == "explicit_date"
            and e.date
            and not _day_grounded(e.date, e.source_text)
        ):
            if e.week:
                upd.update(date_kind="week", date=None)
            elif re.search(
                r"last (class|lecture|day of class)", e.source_text, re.IGNORECASE
            ):
                upd.update(date_kind="last_class", date=None)
        e = e.model_copy(update=upd) if upd else e
        events.append(e)
    have = {(e.date.month, e.date.day) for e in events if e.date is not None}
    for e in list(events):
        second = _slash_second_date(e)
        if second is not None and (second.date.month, second.date.day) not in have:
            events.append(second)
            have.add((second.date.month, second.date.day))
    recurring = []
    for r in ext.recurring:
        if NOT_A_DEADLINE_RE.search(r.title) or VAGUE_CADENCE_RE.search(r.source_text):
            continue
        ctx_text = _context_for(r.source_text, text_sq)
        if text_sq and ctx_text is not None:
            upd = {}
            for k in ("first_date", "last_date"):
                md = getattr(r, k)
                if md is not None and not _day_grounded(md, ctx_text):
                    upd[k] = None
            if upd:
                r = r.model_copy(update=upd)
        ruleless = not r.weeks and r.first_date is None
        # A rule with no weeks or dates is only usable if its weekday is
        # literally printed; a class-meeting day alone is too weak a signal.
        days = set() if ruleless else _meeting_days(ext, r.meeting_kind)
        if r.weekday and not _keep_weekday(r.weekday, r.source_text, text_sq, days):
            r = r.model_copy(update={"weekday": None})
        if ruleless and r.weekday is None:
            continue
        recurring.append(r)
    return ext.model_copy(update={"events": events, "recurring": recurring})


# --------------------------------------------------------------------------
# Main entry points
# --------------------------------------------------------------------------


def build_context(
    ext: LLMSyllabus, today: date, override: TermOverride | None = None
) -> tuple[TermContext, WeekGrid, terms.TermDates]:
    ov = override or TermOverride()
    season = ov.season or _infer_season(ext, today)
    if ov.year:
        year, year_source = ov.year, "user"
    else:
        year, year_source = _infer_year(ext, season, today)
    campus = ov.campus or ext.term.campus
    division = terms.CAMPUS_TO_DIVISION.get(campus, "artsci_stg")
    if division == "artsci_stg" and ENGINEERING_CODE_RE.match(ext.course_code or ""):
        division = "engineering"
    td = terms.lookup(season, year, division)
    breaks = terms.breaks_for(td, season, year)
    numbered = (
        ov.reading_week_numbered
        if ov.reading_week_numbered is not None
        else bool(ext.schedule_anchor.reading_week_numbered)
    )

    # Without any UofT signal the sessional table is only a guess; say so.
    is_uoft = (
        ext.term.campus != "unknown"
        or bool(UOFT_CODE_RE.search(ext.course_code or ""))
        or bool(ENGINEERING_CODE_RE.match(ext.course_code or ""))
        or "toronto" in ext.term.evidence.lower()
    )
    anchor_source = td.source if is_uoft else "heuristic"
    table_week1 = _monday(td.classes_start)
    week1 = table_week1
    a = ext.schedule_anchor
    if ov.week1_monday:
        week1, anchor_source = _monday(ov.week1_monday), "user"
    elif a.week1_month and a.week1_day:
        d = _safe_date(
            _year_for_month(season, year, a.week1_month), a.week1_month, a.week1_day
        )
        if d and abs((d - td.classes_start).days) <= 35:
            week1, anchor_source = _monday(d), "syllabus_anchor"

    pairs = _week_date_pairs(ext, season, year)
    fixed = week1 if anchor_source in ("user", "syllabus_anchor") else None
    fit = _fit_grid(pairs, breaks, numbered, table_week1, fixed)
    if fit:
        fit_week1, fit_numbered, _ = fit
        if fixed is None and abs((fit_week1 - td.classes_start).days) <= 35:
            week1, anchor_source = fit_week1, "syllabus_dates"
        if ov.reading_week_numbered is None and (fixed is None or fit_week1 == fixed):
            numbered = fit_numbered

    ctx = TermContext(
        term_id=td.term_id,
        label=f"{SEASON_LABEL.get(season, season.title())} {year}"
        + (f"–{year + 1}" if season == "full_year" else "")
        + (f" · {CAMPUS_LABEL[campus]}" if campus in CAMPUS_LABEL else ""),
        season=season,
        year=year,
        campus=campus,
        division=td.division,
        week1_monday=week1,
        reading_week_numbered=numbered,
        classes_start=td.classes_start,
        classes_end=td.classes_end,
        reading_week=list(td.reading_week) if td.reading_week else None,
        exam_period=list(td.exam_period) if td.exam_period else None,
        anchor_source=anchor_source,
        year_source=year_source,
    )
    return ctx, WeekGrid(week1, breaks, numbered), td


def _meeting_for(ext: LLMSyllabus, kind: str | None, week_monday: date | None = None):
    preferred = [kind] if kind else []
    preferred += ["lecture", "seminar", "tutorial", "lab", "other"]
    for k in preferred:
        ms = [m for m in ext.meetings if m.kind == k]
        if ms:
            return sorted(ms, key=lambda m: WEEKDAYS.index(m.weekday))[0]
    return None


def _meeting_on(ext: LLMSyllabus, d: date, kind: str | None):
    wd = WEEKDAYS[d.weekday()]
    ms = [
        m for m in ext.meetings if m.weekday == wd and (kind is None or m.kind == kind)
    ]
    if not ms and kind is not None:
        ms = [m for m in ext.meetings if m.weekday == wd]
    return ms[0] if ms else None


def _mk_event(
    ext: LLMSyllabus,
    title: str,
    event_type: str,
    description: str,
    d: date,
    t: time | None,
    duration: int | None,
    confidence: str,
    source: str,
) -> ParsedEvent:
    return ParsedEvent(
        title=title,
        due_date=datetime.combine(d, t or time(23, 59)),
        course=ext.course_code,
        event_type=EventType(event_type),
        description=description,
        time_specified=t is not None,
        duration_minutes=duration if duration and duration > 0 else None,
        date_confidence=confidence,
        date_source=source,
    )


def _row_date(ext: LLMSyllabus, ctx: TermContext, week: int) -> date | None:
    for wd in ext.week_dates:
        if wd.week == week:
            return _safe_date(
                _year_for_month(ctx.season, ctx.year, wd.month), wd.month, wd.day
            )
    return None


def _resolve_in_week(
    ext, grid: WeekGrid, week: int, weekday, in_class, meeting_kind, ctx=None
):
    """(date, meeting, confidence, how) for an item placed in a numbered week."""
    monday = grid.monday_of(week)
    row = _row_date(ext, ctx, week) if ctx is not None else None
    if row is not None:
        # The schedule printed a date on this week's row: that is the item's
        # date unless a weekday or a tutorial/lab sitting says otherwise.
        monday = _monday(row)
        if not weekday and not (in_class and meeting_kind in ("tutorial", "lab")):
            m = _meeting_on(ext, row, meeting_kind) if in_class else None
            return row, m, "inferred", f"schedule row date ({row:%b %d})"
    if weekday:
        d = monday + timedelta(days=WEEKDAYS.index(weekday))
        return (
            d,
            (_meeting_on(ext, d, meeting_kind) if in_class else None),
            "inferred",
            weekday.title(),
        )
    if in_class:
        m = _meeting_for(ext, meeting_kind)
        if m and meeting_kind in ("tutorial", "lab") and m.kind != meeting_kind:
            m = None  # tutorial day unknown: don't borrow the lecture day
        if m:
            d = monday + timedelta(days=WEEKDAYS.index(m.weekday))
            return d, m, "inferred", f"{m.kind} day ({m.weekday.title()})"
    return monday, None, "estimated", "Monday (no day given)"


def _resolve_event(
    ext: LLMSyllabus, e: LLMEvent, ctx: TermContext, grid, td
) -> ParsedEvent | None:
    explicit_t = _parse_time(e.time)
    if e.date_kind == "explicit_date" and e.date:
        d = _to_date(e.date, ctx.season, ctx.year)
        if d is None:
            return None
        t = explicit_t
        if t is None and e.in_class:
            m = _meeting_on(ext, d, e.meeting_kind)
            t = _parse_time(m.start_time) if m else None
        return _mk_event(
            ext,
            e.title,
            e.event_type,
            e.description,
            d,
            t,
            e.duration_minutes,
            "exact",
            "Date stated in syllabus",
        )
    if e.date_kind == "week" and e.week and 1 <= e.week <= MAX_WEEK:
        d, m, conf, how = _resolve_in_week(
            ext, grid, e.week, e.stated_weekday, e.in_class, e.meeting_kind, ctx
        )
        t = explicit_t or (_parse_time(m.start_time) if m else None)
        return _mk_event(
            ext,
            e.title,
            e.event_type,
            e.description,
            d,
            t,
            e.duration_minutes,
            conf,
            f"Week {e.week} → {how}",
        )
    if e.date_kind == "last_class":
        d, m = _last_class(ext, ctx)
        t = explicit_t or (_parse_time(m.start_time) if (m and e.in_class) else None)
        return _mk_event(
            ext,
            e.title,
            e.event_type,
            e.description,
            d,
            t,
            e.duration_minutes,
            "inferred",
            "Last class of term",
        )
    if (
        e.date_kind == "exam_period"
        and ctx.exam_period
        and FINAL_RE.search(e.title)
        and not MIDTERM_RE.search(e.title)
    ):
        return _mk_event(
            ext,
            e.title,
            e.event_type,
            e.description,
            ctx.exam_period[0],
            None,
            e.duration_minutes,
            "estimated",
            "Final exam period starts (exact date TBA)",
        )
    return None


def _last_class(ext: LLMSyllabus, ctx: TermContext):
    rows = [
        _safe_date(_year_for_month(ctx.season, ctx.year, w.month), w.month, w.day)
        for w in ext.week_dates
    ]
    rows = [r for r in rows if r and r <= ctx.classes_end + timedelta(days=7)]
    if rows:
        d = max(rows)
        return d, _meeting_on(ext, d, None)
    days = {m.weekday for m in ext.meetings if m.kind in ("lecture", "seminar")} or {
        m.weekday for m in ext.meetings
    }
    d = ctx.classes_end
    for _ in range(7):
        if not days or WEEKDAYS[d.weekday()] in days:
            break
        d -= timedelta(days=1)
    return d, _meeting_on(ext, d, None)


def _class_weeks(grid: WeekGrid, ctx: TermContext) -> list[int]:
    last = grid.week_of(ctx.classes_end) or 12
    return list(range(1, min(last, MAX_WEEK) + 1))


def _resolve_recurring(
    ext, r: LLMRecurring, ctx: TermContext, grid
) -> list[ParsedEvent]:
    out: list[ParsedEvent] = []
    explicit_t = _parse_time(r.time)
    step = max(1, r.every_n_weeks or 1)
    dates: list[tuple[date, str, str]] = []
    if r.weeks:
        for w in sorted(set(r.weeks)):
            if 1 <= w <= MAX_WEEK and w not in r.excluded_weeks:
                d, _, conf, how = _resolve_in_week(
                    ext, grid, w, r.weekday, r.in_class, r.meeting_kind, ctx
                )
                dates.append((d, conf, f"Week {w} → {how}"))
    else:
        first = _to_date(r.first_date, ctx.season, ctx.year) if r.first_date else None
        last = _to_date(r.last_date, ctx.season, ctx.year) if r.last_date else None
        if first is None:
            weeks = _class_weeks(grid, ctx)[::step]
            for w in weeks:
                if w in r.excluded_weeks:
                    continue
                d, _, conf, how = _resolve_in_week(
                    ext, grid, w, r.weekday, r.in_class, r.meeting_kind, ctx
                )
                dates.append((d, "estimated", f"Recurring, week {w} → {how}"))
        else:
            if r.weekday and WEEKDAYS[first.weekday()] != r.weekday:
                first += timedelta(
                    days=(WEEKDAYS.index(r.weekday) - first.weekday()) % 7
                )
            end = last or ctx.classes_end
            d = first
            while d <= end and len(dates) < 60:
                wk = grid.week_of(d)
                if wk is not None and wk not in r.excluded_weeks:
                    dates.append((d, "inferred", "Recurring from stated first date"))
                d += timedelta(weeks=step)
    for d, conf, how in dates:
        t = explicit_t
        if t is None and r.in_class:
            m = _meeting_on(ext, d, r.meeting_kind)
            t = _parse_time(m.start_time) if m else None
        out.append(
            _mk_event(
                ext,
                r.title,
                r.event_type,
                r.description,
                d,
                t,
                r.duration_minutes,
                conf,
                how,
            )
        )
    return out


TITLE_STOP = {
    "weekly",
    "the",
    "and",
    "for",
    "due",
    "of",
    "in",
    "on",
    "a",
    "an",
    "online",
    "in-class",
}


def _same_stream(rule_title: str, event_title: str) -> bool:
    """Does a listed event look like an instance of a recurring rule?"""
    rw = [w for w in re.findall(r"[a-z]+", rule_title.lower()) if w not in TITLE_STOP]
    ew = set(re.findall(r"[a-z]+", event_title.lower()))
    if any(
        len(w) >= 4 and (w in ew or w.rstrip("s") in ew or w + "s" in ew) for w in rw
    ):
        return True
    initials = "".join(w[0] for w in rw)
    return len(initials) >= 2 and any(
        t.rstrip("s") == initials[-len(t.rstrip("s")) :] and len(t.rstrip("s")) >= 2
        for t in ew
    )


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def resolve(
    ext: LLMSyllabus, today: date, override: TermOverride | None = None
) -> tuple[list[ParsedEvent], TermContext]:
    ctx, grid, td = build_context(ext, today, override)
    # source_key identifies "the same item" across re-dates (dates change,
    # titles repeat for recurring items): e<i> = i-th one-time event,
    # r<j>:<k> = k-th occurrence of the j-th recurring rule.
    events: list[ParsedEvent] = []
    for i, e in enumerate(ext.events):
        try:
            ev = _resolve_event(ext, e, ctx, grid, td)
        except Exception:
            logger.exception("Failed to resolve event %r", e.title)
            ev = None
        if ev:
            events.append(ev.model_copy(update={"source_key": f"e{i}"}))
    # One-time events listed individually win over a rule describing the same
    # stream of work (models often emit both).
    rules: list[LLMRecurring] = []
    for r in ext.recurring:
        twin = next(
            (
                i
                for i, q in enumerate(rules)
                if q.weekday == r.weekday
                and q.time == r.time
                and q.weeks == r.weeks
                and _same_stream(q.title, r.title)
            ),
            None,
        )
        if twin is None:
            rules.append(r)
        else:  # e.g. "Homework Quiz" + "Homework Written" due together
            q = rules[twin]
            rules[twin] = q.model_copy(update={"title": f"{q.title} / {r.title}"})

    taken: dict[tuple[date, str], list[str]] = {}
    for ev in events:
        taken.setdefault((ev.due_date.date(), ev.event_type), []).append(ev.title)
    for j, r in enumerate(rules):
        try:
            for k, ev in enumerate(_resolve_recurring(ext, r, ctx, grid)):
                same_day = taken.get((ev.due_date.date(), ev.event_type), [])
                if not any(_same_stream(r.title, t) for t in same_day):
                    events.append(ev.model_copy(update={"source_key": f"r{j}:{k}"}))
        except Exception:
            logger.exception("Failed to resolve recurring %r", r.title)

    # Guardrail: explicit dates wildly outside the term are almost always a
    # wrong year; nudge by ±1 year if that lands inside the term window.
    lo = ctx.classes_start - timedelta(days=30)
    hi = (ctx.exam_period[1] if ctx.exam_period else ctx.classes_end) + timedelta(
        days=21
    )
    fixed: list[ParsedEvent] = []
    for ev in events:
        d = ev.due_date.date()
        if not (lo <= d <= hi):
            for dy in (-1, 1):
                alt = _safe_date(d.year + dy, d.month, d.day)
                if alt and lo <= alt <= hi:
                    ev = ev.model_copy(
                        update={"due_date": ev.due_date.replace(year=alt.year)}
                    )
                    break
        fixed.append(ev)

    seen: set[tuple[str, date]] = set()
    deduped = []
    for ev in sorted(fixed, key=lambda x: x.due_date):
        key = (_norm(ev.title), ev.due_date.date())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(ev)
    return deduped, ctx
