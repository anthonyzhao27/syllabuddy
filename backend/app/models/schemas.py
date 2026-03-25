"""Pydantic request/response models."""

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel

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


class ParsedEvent(BaseModel):
    title: str
    due_date: datetime
    course: str = ""
    event_type: EventType = EventType.OTHER
    description: str = ""
    time_specified: bool = True


class ParseResponse(BaseModel):
    events: list[ParsedEvent]


class ExportRequest(BaseModel):
    events: list[ParsedEvent]
    format: str = "ics"
    google_token: str | None = None


class ReminderRequest(BaseModel):
    events: list[ParsedEvent]
    phone_number: str


class IcsExportRequest(BaseModel):
    events: list[ParsedEvent]
    filename: str = "syllabus.ics"
    timezone: str


class OutlookExportRequest(BaseModel):
    events: list[ParsedEvent]
    timezone: str


class OutlookExportResponse(BaseModel):
    method: Literal["deep_link"]
    url: str


class GoogleExportRequest(BaseModel):
    events: list[ParsedEvent]
    access_token: str | None = None
    calendar_id: str = "primary"
    timezone: str = "UTC"


class GoogleExportResponse(BaseModel):
    created_count: int
    created: list[dict]
    errors: list[dict]
