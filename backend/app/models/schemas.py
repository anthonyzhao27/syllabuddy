"""Pydantic request/response models."""

from datetime import date, datetime
from datetime import time as dt_time
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EventType(StrEnum):
    ASSIGNMENT = "assignment"
    EXAM = "exam"
    QUIZ = "quiz"
    PROJECT = "project"
    LAB = "lab"
    PRESENTATION = "presentation"
    MILESTONE = "milestone"
    DEADLINE = "deadline"
    DISCUSSION = "discussion"
    OTHER = "other"


class RecurrenceFrequency(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class Weekday(StrEnum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class Recurrence(BaseModel):
    """Recurrence specification extracted from syllabus.

    Contract:
    - start_date is the first ACTUAL occurrence, not merely the start of a range
    - for weekly recurrences, start_date must already fall on weekday
    - biweekly schedules are represented as frequency=WEEKLY with interval=2

    Note: Monthly weekday patterns such as "first Friday", "second Tuesday", or
    "last Friday" are not supported in this version. Only same-day-of-month
    monthly recurrence is supported.
    """

    frequency: RecurrenceFrequency
    interval: int = Field(default=1, ge=1)
    weekday: Weekday | None = None
    start_date: date
    end_date: date
    time: dt_time | None = None
    exclusions: list[date] = Field(default_factory=list)


class RecurringEvent(BaseModel):
    """A recurring event as extracted by the LLM (before expansion)."""

    title: str
    course: str = ""
    event_type: EventType = EventType.OTHER
    description: str = ""
    recurrence: Recurrence
    duration_minutes: int | None = None


class ParsedEvent(BaseModel):
    title: str
    due_date: datetime
    course: str = ""
    event_type: EventType = EventType.OTHER
    description: str = ""
    time_specified: bool = True
    duration_minutes: int | None = None
    # "exact" = date printed in the syllabus; "inferred" = derived from a week
    # number + known day; "estimated" = best guess (e.g. no day given, exam TBA)
    date_confidence: str | None = None
    date_source: str = ""
    # Stable identity of the syllabus item across re-dates (see date_resolver)
    source_key: str = ""


class TermContext(BaseModel):
    """The calendar anchor used to turn week numbers into dates."""

    term_id: str
    label: str
    season: str
    year: int
    campus: str
    division: str
    week1_monday: date
    reading_week_numbered: bool = False
    classes_start: date
    classes_end: date
    reading_week: list[date] | None = None
    exam_period: list[date] | None = None
    # user | syllabus_anchor | syllabus_dates | table | heuristic
    anchor_source: str
    # user | stated | weekday_votes | upload_date
    year_source: str


class TermOverride(BaseModel):
    """User corrections to the inferred term anchor."""

    season: str | None = None
    year: int | None = None
    campus: str | None = None
    week1_monday: date | None = None
    reading_week_numbered: bool | None = None


class LLMExtractionResult(BaseModel):
    """Raw extraction result from LLM before processing."""

    events: list[ParsedEvent] = Field(default_factory=list)
    recurring_events: list[RecurringEvent] = Field(default_factory=list)


class ParseResponse(BaseModel):
    events: list[ParsedEvent]
    course_code: str | None = None
    term_context: TermContext | None = None
    # Raw LLM transcription; sent back to /parse/resolve to re-date events
    extraction: dict | None = None


class ResolveRequest(BaseModel):
    extraction: dict
    override: TermOverride = Field(default_factory=TermOverride)
    today: date | None = None


class SaveResponse(BaseModel):
    syllabus_id: str


class ExportRequest(BaseModel):
    events: list[ParsedEvent]
    format: str = "ics"


class ReminderRequest(BaseModel):
    events: list[ParsedEvent]
    phone_number: str


class IcsExportRequest(BaseModel):
    events: list[ParsedEvent]
    filename: str = "syllabus.ics"
    timezone: str


class SyllabusResponse(BaseModel):
    id: str
    name: str
    course_code: str | None = None
    source_type: str
    original_filename: str | None = None
    created_at: str
    event_count: int
    timezone: str | None = None
    term_context: TermContext | None = None
    # True when the stored transcription allows re-dating via /files/{id}/resolve
    can_redate: bool = False


class SyllabusListResponse(BaseModel):
    syllabi: list[SyllabusResponse]


class EventResponse(BaseModel):
    id: str
    title: str
    due_date: str
    course: str
    event_type: str
    description: str
    time_specified: bool
    duration_minutes: int | None = None
    is_edited: bool
    date_confidence: str | None = None
    date_source: str = ""
    source_key: str = ""


class SyllabusResolveRequest(BaseModel):
    override: TermOverride = Field(default_factory=TermOverride)


class SyllabusDetailResponse(BaseModel):
    syllabus: SyllabusResponse
    events: list[EventResponse]


class DeleteResponse(BaseModel):
    message: str


class EventUpdateRequest(BaseModel):
    title: str | None = None
    due_date: date | datetime | None = None
    course: str | None = None
    event_type: EventType | None = None
    description: str | None = None
    time_specified: bool | None = None
    duration_minutes: int | None = Field(default=None, gt=0)


class SyllabusUpdateRequest(BaseModel):
    timezone: str | None = None


# --------------------------------------------------------------------------
# Strict schema the LLM fills in. It transcribes; Python does the date math
# (services/date_resolver.py). Every field is required and nullable where
# optional, so it can drive OpenAI strict json_schema structured outputs.
# --------------------------------------------------------------------------
WeekdayName = Literal[
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
]
EventTypeName = Literal[
    "assignment",
    "exam",
    "quiz",
    "project",
    "lab",
    "presentation",
    "milestone",
    "deadline",
    "discussion",
    "other",
]
MeetingKind = Literal["lecture", "tutorial", "lab", "seminar", "other"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TermInfo(_Strict):
    season: Literal[
        "fall",
        "winter",
        "summer",
        "summer_first",
        "summer_second",
        "full_year",
        "unknown",
    ]
    year: int | None
    campus: Literal["st_george", "mississauga", "scarborough", "unknown"]
    evidence: str


class ScheduleAnchor(_Strict):
    week1_month: int | None
    week1_day: int | None
    evidence: str
    reading_week_numbered: bool | None


class Meeting(_Strict):
    kind: MeetingKind
    weekday: WeekdayName
    start_time: str | None
    end_time: str | None


class MonthDay(_Strict):
    month: int
    day: int
    year: int | None


class LLMEvent(_Strict):
    title: str
    event_type: EventTypeName
    description: str
    date_kind: Literal["explicit_date", "week", "last_class", "exam_period", "tbd"]
    date: MonthDay | None
    stated_weekday: WeekdayName | None
    week: int | None
    in_class: bool
    meeting_kind: MeetingKind | None
    time: str | None
    duration_minutes: int | None
    source_text: str


class LLMRecurring(_Strict):
    title: str
    event_type: EventTypeName
    description: str
    weekday: WeekdayName | None
    in_class: bool
    meeting_kind: MeetingKind | None
    time: str | None
    weeks: list[int]
    first_date: MonthDay | None
    last_date: MonthDay | None
    every_n_weeks: int
    excluded_weeks: list[int]
    duration_minutes: int | None
    source_text: str


class WeekDate(_Strict):
    week: int
    month: int
    day: int


class LLMSyllabus(_Strict):
    course_code: str
    term: TermInfo
    schedule_anchor: ScheduleAnchor
    meetings: list[Meeting]
    week_dates: list[WeekDate]
    events: list[LLMEvent]
    recurring: list[LLMRecurring]
