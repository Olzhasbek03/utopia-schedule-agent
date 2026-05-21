# Utopia Schedule Agent

## One-line description

An AI scheduling agent for Utopia Studio's Founder's Associate: it turns a plain-English scheduling request into ranked Doha-time slots, conflict checks against recurring studio meetings, a calendar invite draft, a `.ics` file, and a second-agent Slack handoff.

## Operator & problem

The operator is the **Founder's Associate** at Utopia Studio. She runs six recurring meetings every week and frequently books ad-hoc calls around them across Doha, London, Singapore, and other timezones. Today this is manual: timezone math, remembering blocked studio meetings, writing invite copy, and avoiding double-bookings. The agent removes that manual scheduling pass and outputs something she can use immediately.

## How to run locally

```bash
cd schedule_agent
pip install -r requirements.txt

cp .env.example .env
# Open .env and paste your real OpenAI API key:
# OPENAI_API_KEY=sk-...

python agent.py "30 min with a London investor next week, Tuesday morning ideal" > out.json
python announcer.py out.json
```

The full agent loads `.env` automatically through `python-dotenv`. The `.ics` file is written to `proposed_invite.ics`.

### Dev test without API key

```bash
python dev_tests/edge_case_qdb_collision.py
```

This deterministic test does **not** call OpenAI. It only proves the scheduler correctly flags/avoids the QDB Monday 14:00 conflict. The final Loom demo should use the real command above with the OpenAI parser.

### Regenerate sample outputs

```bash
python generate_sample_outputs.py
```

This requires a real `OPENAI_API_KEY` and rewrites:

- `sample_outputs/admin_schedule_output.json`
- `sample_outputs/calendar_invite.ics`
- `sample_outputs/slack_handoff.txt`

## Required environment variables

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | Lets `parser.py` call the OpenAI Chat Completions API |

## Example output

Full output lives in `sample_outputs/admin_schedule_output.json`. The important contract looks like this:

```json
{
  "original_request": "30 min with a London investor next week, Tuesday morning ideal",
  "parsed_request": {
    "duration_min": 30,
    "topic": "Investor intro call",
    "attendees": [
      {"name": "London investor", "timezone": "Europe/London", "role": "external"}
    ],
    "day_preference": "Tuesday",
    "time_preference": "morning",
    "week_offset": 1
  },
  "selected_recommended_slot": {
    "start_time_doha": "2026-05-26T09:30:00+03:00",
    "end_time_doha": "2026-05-26T10:00:00+03:00",
    "attendee_local_times": {"Europe/London": "2026-05-26T07:30:00+01:00"},
    "status": "clean",
    "conflicts": []
  },
  "calendar_invite_draft": {
    "title": "[Investor intro call] · [Studio]"
  },
  "second_agent_handoff": {"target_agent": "announcer", "status": "ready_to_consume"},
  "status": "ready_to_send"
}
```

## Prompts used

The parser system prompt is in `parser.py` as `SYSTEM_PROMPT`. It tells the model to act only as a scheduling intent parser and return fixed-schema JSON: duration, topic, scope, attendees with IANA timezones, day/time preference, week offset, fellow-meeting flag, and assumptions.

## APIs and tools called

| API / tool | Role |
|---|---|
| OpenAI Chat Completions API (`gpt-4o-mini`) | Parses plain English into structured JSON |
| `ics` Python library | Builds the `.ics` calendar invite |
| `zoneinfo` Python stdlib | Timezone math |
| `pyyaml` | Reads the recurring-meetings knowledge base |
| `python-dotenv` | Loads the local `.env` file |

## File structure

```text
schedule_agent/
├── agent.py                      # Agent 1 entry point
├── parser.py                     # OpenAI parser: English -> JSON
├── scheduler.py                  # Ranked slots + conflict detection
├── invite.py                     # Human-readable invite + .ics content
├── announcer.py                  # Agent 2: JSON -> Slack message
├── recurring_meetings.yaml       # Six meetings + assumptions
├── generate_sample_outputs.py    # Rebuilds sample_outputs/ with real API key
├── requirements.txt
├── .env.example
├── README.md
├── WRITEUP.md
├── LOOM_SCRIPT.md
├── sample_outputs/
│   ├── admin_schedule_output.json
│   ├── calendar_invite.ics
│   └── slack_handoff.txt
└── dev_tests/
    └── edge_case_qdb_collision.py
```

## Assumptions

The brief gives an exact time for only one recurring meeting: **QDB weekly, Monday 14:00 Doha**. Other recurring meeting times are editable defaults in `recurring_meetings.yaml` and marked with `assumed_default: true`. This keeps the code honest: an operator can adjust studio reality without touching Python.

## Known limitations

- No live Google Calendar write. The agent creates a `.ics` file so the operator stays in control.
- No live calendar lookup, so one-off conflicts outside the six recurring meetings are not detected.
- No multi-turn clarification. Ambiguities are captured in `parsed_request.assumptions`.
- Slot granularity is 30 minutes.
