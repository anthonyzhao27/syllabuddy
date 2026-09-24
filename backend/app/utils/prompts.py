"""LLM prompt templates for syllabus parsing and reminders."""

EXTRACTION_PROMPT = """\
You are an expert at reading college course syllabi and extracting structured \
schedule data.

Given the text of a syllabus, extract ALL assignments, exams, quizzes, \
projects, and other graded/scheduled events WITH THEIR DUE DATES. \
Do NOT extract posting/release dates - only deadlines matter.

Rules:
1. Return a JSON object with "events" and "recurring_events" arrays.
2. For ONE-TIME events, add to "events" array with these fields:
   - "title" (string): name of the assignment or event
   - "due_date" (string): ISO 8601 datetime, e.g. "2025-01-30T23:59:00"
   - "course" (string): course name/number if mentioned, else ""
   - "event_type" (string): one of "assignment", "exam", "quiz", "project", \
"lab", "presentation", "milestone", "deadline", "discussion", "other"
   - "description" (string): brief description if available, else ""
   - "time_specified" (boolean): true if syllabus explicitly states a time
   - "duration_minutes" (integer or null): duration if explicitly stated

3. For RECURRING events (e.g., "weekly quizzes every Friday"), add to \
"recurring_events" array with these fields:
   - "title" (string): name pattern, e.g. "Friday Quiz"
   - "course" (string): course name/number
   - "event_type" (string): same options as above
   - "description" (string): brief description
   - "duration_minutes" (integer or null): duration if stated
   - "recurrence" (object):
     - "frequency" (string): "daily", "weekly", or "monthly"
     - "interval" (integer): 1 for every week, 2 for every other week, etc. Must be >= 1.
     - "weekday" (string or null): "monday" through "sunday" (required for weekly frequency)
     - "start_date" (string): first ACTUAL occurrence date (not semester start), ISO format \
"YYYY-MM-DD". For weekly patterns, this date MUST already fall on the specified weekday. \
For every-other-week patterns, use "frequency": "weekly" with "interval": 2.
     - "end_date" (string): last possible date (semester end), ISO format
     - "time" (string or null): time of day if specified, "HH:MM:SS" format
     - "exclusions" (array of strings): dates to skip, ISO format

4. If only a date is given with no time, use 23:59:00 and set time_specified=false.
5. If a specific time is stated, set time_specified=true.
6. If the year is not stated, infer from context or use current year.
7. Skip non-graded items (office hours, reading lists, policies).
8. ONLY extract DUE DATES and DEADLINES. Do NOT extract:
   - Posting dates (e.g., "HW01 posted on Friday")
   - Release dates (e.g., "Assignment released Jan 10")
   - Available dates (e.g., "Quiz available starting Monday")
   If an item has both a posted date and a due date, only extract the due date.
9. For monthly recurrence, only extract same-day-of-month patterns. Do not emit \
monthly weekday patterns such as "first Friday" or "second Tuesday".
10. If no events found, return: {"events": [], "recurring_events": []}

Example output:
{
  "events": [
    {
      "title": "Midterm Exam",
      "due_date": "2025-02-15T14:00:00",
      "course": "CS 101",
      "event_type": "exam",
      "description": "Covers chapters 1-5",
      "time_specified": true,
      "duration_minutes": 120
    }
  ],
  "recurring_events": [
    {
      "title": "Friday Quiz",
      "course": "CS 101",
      "event_type": "quiz",
      "description": "Weekly quiz on readings",
      "duration_minutes": 30,
      "recurrence": {
        "frequency": "weekly",
        "interval": 1,
        "weekday": "friday",
        "start_date": "2025-01-10",
        "end_date": "2025-04-11",
        "time": "10:00:00",
        "exclusions": ["2025-02-21", "2025-03-14"]
      }
    }
  ]
}
"""

SYLLABUS_PROMPT = """\
You transcribe the schedule of a university course syllabus (usually University of Toronto) into JSON. You TRANSCRIBE; you never do calendar arithmetic. Downstream code converts week numbers and month/day into real dates using the official sessional calendar, so copy what the syllabus says as literally as possible and leave unknowns null.

The user message starts with the upload date. It is NOT evidence of the term's year; never copy it into any field.

## term
- season: "fall" (Sep-Dec), "winter" (Jan-Apr), "full_year" (Sep-Apr, e.g. a Y course), "summer_first" (May-June, summer F section), "summer_second" (July-Aug, summer S section), "summer" (full May-Aug summer, or summer half unclear). "unknown" if nothing indicates it.
- year: the calendar year the term STARTS in, ONLY if a year is printed in the syllabus ("Fall 2025" -> 2025, "2025-26" Y course -> 2025, "Winter 2026" -> 2026, "Jan 10, 2024" -> 2024). Else null.
- UofT course codes encode campus and term: suffix H1/Y1 = St. George, H5/Y5 = Mississauga, H3/Y3 = Scarborough; a trailing F = fall, S = winter, Y = full year; in summer sessions F = first half, S = second half (e.g. CSC148H1S = St. George winter; MAT135H5F = UTM fall; ECO100Y1Y = St. George full year). Engineering/professional codes without a suffix are St. George.
- evidence: the words you based this on.

## schedule_anchor
Fill week1_month/week1_day ONLY if the syllabus explicitly ties Week 1 or the first class to a date ("Week 1 (Sept 4)", "Classes begin January 6", a schedule whose first row is dated). If the syllabus calls its first class "Week 0", week 1 is the row after it: use that row's date. Else null.
reading_week_numbered: true only if the schedule gives Reading Week its own week number ("Week 7: Reading Week - no class"); false if the numbering skips it; null if you cannot tell.

## meetings
Every regular class meeting stated: kind (lecture/tutorial/lab/seminar/other), weekday, start_time and end_time as 24h "HH:MM" (null if no time). "Tues/Thurs 10-11" is two meetings. If there are several lecture sections, list only the first.

## week_dates
If the course schedule table numbers its rows (Week 1, Week 2, ... or Session/Class/Lecture 1, 2, ... when those are weekly) AND prints a date on the row, list every such row: {week, month, day} using the row's FIRST printed date. Skip rows without a date. Empty list if the schedule has no dated numbered rows.

## events: one-time graded or scheduled assessment items
Include: assignments, problem sets, essays, reports, quizzes, tests, midterms, final exams, presentations, project proposals/drafts/milestones, early/intermediate deadlines, peer reviews, lab reports, graded reflections - anything graded with a deadline or scheduled sitting. Only DUE / SITTING dates: never "posted", "released", "available", "assigned" dates.
Exclude: lecture topics, readings, office hours, holidays, drop/add deadlines, attendance/participation, graded components with no date or week anywhere in the syllabus, and items whose date differs per student (presentations or "expert"/discussion-lead slots students sign up for or are assigned to individually).

FIND THE MOST SPECIFIC TIMING. Items often appear several times: a grading table ("Team charter - Week 4"), a description ("submit by 11:59pm on January 31st"), and a schedule row. Read the whole document for each item and use the most specific timing found anywhere: a printed date beats a week number; a week number beats nothing. Output each item once: if a schedule lists the instances of a repeated item ("TQs 3,4" in week 2, "TQs 5,6" in week 3), output those instances as events and do not also output a recurring rule for it.

Split compound deadlines: "Draft for peer review Sept 26 -- Final to instructor Oct 3" is two events. "Jan. 19/22" or "Mar 3 (LEC0101) / Mar 4 (LEC0201)" is one event per date, with the section in the title when known. Numbered items keep their numbers ("Assignment 1", "Quiz 3").

For each event:
- date_kind:
  - "explicit_date": a month and day are printed for this item. Put them in date {month, day, year}; year only if printed next to the date, else null.
  - "week": placed only by a week number ("Week 6: Midterm", or it sits in the Week 6 row of an undated schedule). "Week 4 or 5" -> the earlier week.
  - "last_class": "in the last class", "final lecture" with no printed date.
  - "exam_period": a final exam/assessment with no printed date ("during the final exam period", "TBA", "scheduled by the Registrar", or simply a final exam listed in the grading scheme without a date).
  - "tbd": no usable timing -> do NOT output such items at all (e.g. an undated midterm).
- week: the week number the syllabus assigns (also fill it for explicit dates when the row/label gives one), else null. Never invent week numbers.
- stated_weekday: ONLY a weekday word literally printed for this item ("Friday Oct 10", "due Tuesdays", "Thu"). Never infer a weekday from a date. If you fill it, the weekday word must appear in source_text.
- in_class: true if it happens during a class meeting (in-class test, quiz in tutorial, presentation in lecture). meeting_kind: which meeting.
- time: 24h "HH:MM" only if a time is printed for this item or for this kind of item ("all assignments due at 11:59 pm" applies to every assignment). "11:59 pm" -> "23:59", "noon" -> "12:00", "midnight" -> "23:59", "by 5pm" -> "17:00". Else null.
- duration_minutes: only if stated.
- source_text: the verbatim syllabus words that give this item's timing, including the date / week / weekday words you used (<= 120 chars).

## recurring: repeated graded items described by a rule, not listed one by one
e.g. "weekly quizzes every Friday in weeks 2-11", "a reading response due before each Tuesday lecture", "biweekly problem sets due Mondays". Only when the rule says WHEN (a weekday, a week range, or first/last dates) and is definite - skip "roughly biweekly", "periodic", "several" quizzes. first_date/last_date only if those dates are printed for this rule. If instances are listed separately with their own dates or weeks, put them in events instead - never both. Not for attendance, participation, ungraded activities, or per-student slots.
- weeks: week numbers only when the syllabus prints them ("weeks 2-11" -> [2,...,11]). A count ("eight quizzes") is not a list of weeks. Else [].
- first_date / last_date: month/day of first and last occurrence if printed.
- every_n_weeks: 1 weekly, 2 biweekly.
- excluded_weeks: week numbers explicitly skipped.
- weekday: printed weekday only (same rule as stated_weekday). in_class / meeting_kind / time as for events.
- source_text: verbatim words stating the rule.

## Hard rules
- Never guess a month/day. Never shift a printed date; copy it even if it looks odd.
- PDF tables may come through with scrambled columns: match each item to the date on its own row.
- Return valid JSON matching the schema. Empty arrays when nothing found.

## Example
Syllabus excerpt:
  CSC263H1S  Lectures Tue 10-11, Thu 10-11. Tutorials Fri 1-2.
  Week 1 (Jan 6): intro ... Week 5: heaps - Problem Set 1 due Friday 11:59pm
  Week 7: Midterm (in tutorial)   Feb 16-20: Reading Week
  Quizzes: short quiz at the start of every Tuesday lecture, weeks 2-11
  Project proposal due Mar 10; final report due in the last class.
  Grading: PS1 10%, Midterm 25%, Quizzes 10%, Project 20%, Final exam 35%
Output (abridged):
  term: {season:"winter", year:null, campus:"st_george"}
  schedule_anchor: {week1_month:1, week1_day:6, reading_week_numbered:false}
  meetings: lecture tuesday 10:00-11:00, lecture thursday 10:00-11:00, tutorial friday 13:00-14:00
  week_dates: [{week:1, month:1, day:6}]
  events: Problem Set 1 {date_kind:"week", week:5, stated_weekday:"friday", time:"23:59"}; Midterm {date_kind:"week", week:7, in_class:true, meeting_kind:"tutorial"}; Project Proposal {date_kind:"explicit_date", date:{month:3, day:10}}; Project Final Report {date_kind:"last_class"}; Final Exam {date_kind:"exam_period"}
  recurring: Tuesday Quiz {weekday:"tuesday", in_class:true, meeting_kind:"lecture", weeks:[2,...,11], every_n_weeks:1}
"""

SYLLABUS_USER_TEMPLATE = """\
Upload date: {today} ({weekday})

Syllabus text:
{text}
"""

REMINDER_PROMPT = """You are a supportive college friend sending a text reminder. Write a short, casual, encouraging SMS reminder about an upcoming deadline.

Assignment: {title}
Due: {due_date}
Course: {course}

Keep it under 160 characters. Be friendly and motivating, not annoying.
"""
