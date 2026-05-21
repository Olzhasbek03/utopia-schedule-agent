# Utopia Studio Take-Home — Writeup

## Operator & problem
The operator is the Founder's Associate at Utopia Studio. She runs six recurring meetings every week and is asked to book ad-hoc calls around them across Doha, London, Singapore, and Asia-Pacific timezones. Today she does this manually: remembering blocked studio slots, doing timezone math, and writing invites in the studio format. This costs about 10 minutes per request and creates double-booking risk, especially around fixed meetings like QDB Monday 14:00.

## The agent
The agent takes one plain-English scheduling request and returns three ranked Doha-time slots, conflict status against recurring meetings, a human-readable invite draft, and a `.ics` file. It calls the OpenAI Chat Completions API (`gpt-4o-mini`) only to parse messy English into structured JSON; scheduling math is deterministic Python. A second agent (`announcer.py`) reads the JSON and drafts a Slack message with attendee local times, creating a simple Utopia OS handoff.

## Sample input
```text
30 min with a London investor next week, Tuesday morning ideal
```

## Sample output
```json
{
  "selected_recommended_slot": {
    "start_time_doha": "2026-05-26T09:30:00+03:00",
    "end_time_doha": "2026-05-26T10:00:00+03:00",
    "attendee_local_times": {"Europe/London": "2026-05-26T07:30:00+01:00"},
    "status": "clean",
    "conflicts": [],
    "rationale": "Tuesday 09:30-10:00 Doha; no conflicts with recurring meetings; matches 'morning' preference."
  },
  "calendar_invite_draft": {"title": "[Investor intro call] · [Studio]"},
  "ics_file_path": "sample_outputs/calendar_invite.ics",
  "second_agent_handoff": {"target_agent": "announcer", "status": "ready_to_consume"}
}
```
Full JSON is in `sample_outputs/admin_schedule_output.json`; Agent 2's Slack draft is in `sample_outputs/slack_handoff.txt`.

## What you cut
- Google Calendar OAuth write: `.ics` is faster, safer, and keeps the operator in control.
- Multi-turn clarification: the agent runs single-input/single-output and surfaces assumptions in JSON.
- LLM conflict negotiation: conflicts are reported deterministically instead of guessed around.

## What broke or surprised you
- The brief gives an exact time only for QDB Monday 14:00, so other meeting times had to become editable YAML defaults, not hidden code assumptions.
- Datetime objects did not serialize cleanly to JSON, so I added explicit slot serialization in `agent.py`.
- The studio stack is Claude.ai, but I used OpenAI because I had API access; the parser is isolated so Anthropic can replace it without rewriting the scheduler.

## If you had two more days
- Add Google Calendar write + Slack posting after the operator confirms the proposed time.
- Query the real calendar so one-off conflicts are detected, not only recurring studio meetings.
- Create Linear issues automatically when the parsed request is a fellow meeting.
