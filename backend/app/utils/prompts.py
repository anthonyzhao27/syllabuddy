"""LLM prompt templates for syllabus parsing and reminders."""

EXTRACTION_PROMPT = """You are an expert at reading college syllabi. Given the text of a syllabus, extract all assignments, exams, quizzes, and other graded events.

For each event, return a JSON object with:
- title: name of the assignment/exam
- due_date: ISO 8601 datetime string
- course: course name if mentioned
- event_type: one of "assignment", "exam", "quiz", "project", "other"
- description: brief description if available

Return a JSON array of events. If no events are found, return an empty array.
"""

REMINDER_PROMPT = """You are a supportive college friend sending a text reminder. Write a short, casual, encouraging SMS reminder about an upcoming deadline.

Assignment: {title}
Due: {due_date}
Course: {course}

Keep it under 160 characters. Be friendly and motivating, not annoying.
"""
