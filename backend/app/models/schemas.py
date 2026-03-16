"""Pydantic request/response models."""

from datetime import datetime
from pydantic import BaseModel


class ParsedEvent(BaseModel):
    title: str
    due_date: datetime
    course: str = ""
    event_type: str = ""  # e.g. "assignment", "exam", "quiz"
    description: str = ""


class ParseResponse(BaseModel):
    events: list[ParsedEvent]


class ExportRequest(BaseModel):
    events: list[ParsedEvent]
    format: str = "ics"  # "ics" or "google"
    google_token: str | None = None


class ReminderRequest(BaseModel):
    events: list[ParsedEvent]
    phone_number: str
