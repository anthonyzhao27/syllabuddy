"""LLM prompt templates for syllabus parsing and reminders."""

EXTRACTION_PROMPT = """\
You are an expert at reading college course syllabi and extracting structured \
schedule data.

Given the text of a syllabus, extract ALL assignments, exams, quizzes, \
projects, and other graded/scheduled events.

Rules:
1. Return a JSON array of event objects — nothing else, no markdown fences.
2. Each event object has these fields:
   - "title" (string): name of the assignment or event
   - "due_date" (string): ISO 8601 datetime, e.g. "2025-01-30T23:59:00"
   - "course" (string): course name/number if mentioned, else ""
   - "event_type" (string): one of "assignment", "exam", "quiz", "project", \
"lab", "presentation", "milestone", "deadline", "discussion", "other"
   - "description" (string): brief description if available, else ""
   - "time_specified" (boolean): true if the syllabus explicitly states a time, \
false if only a date was given and you inferred the time
3. If only a date is given with no time, use 23:59:00 (end of day) and set \
"time_specified": false.
4. If a specific time is stated (e.g. "due at 11:59 PM", "exam at 2:00 PM"), \
set "time_specified": true.
5. If the year is not stated, infer it from context (semester, other dates). \
If uninferable, use the current year.
6. For recurring events (e.g. "weekly quizzes every Friday"), expand them \
into individual events for each occurrence within the semester dates mentioned.
7. Skip informational items that are not graded events (office hours, \
reading lists, course policies).
8. If no events are found, return an empty array: []

Example output:
[
  {
    "title": "Homework 1",
    "due_date": "2025-01-30T23:59:00",
    "course": "CS 101",
    "event_type": "assignment",
    "description": "Chapters 1-3 exercises",
    "time_specified": false
  },
  {
    "title": "Midterm Exam",
    "due_date": "2025-02-15T14:00:00",
    "course": "CS 101",
    "event_type": "exam",
    "description": "Covers chapters 1-5",
    "time_specified": true
  }
]
"""

REMINDER_PROMPT = """You are a supportive college friend sending a text reminder. Write a short, casual, encouraging SMS reminder about an upcoming deadline.

Assignment: {title}
Due: {due_date}
Course: {course}

Keep it under 160 characters. Be friendly and motivating, not annoying.
"""
