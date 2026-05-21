# sample_outputs/

These three files are what Agent 1 (`agent.py`) and Agent 2
(`announcer.py`) produce end-to-end when the agent is run on:

> `30 min with a London investor next week, Tuesday morning ideal`

## Files

| File | What it is |
|------|------------|
| `admin_schedule_output.json` | Agent 1's full output. The Utopia OS handoff contract. |
| `calendar_invite.ics` | The calendar file to double-click and add to Calendar/Outlook. |
| `slack_handoff.txt` | Agent 2's Slack message, drafted from the JSON above. |

## How to regenerate

After setting your `OPENAI_API_KEY`:

```bash
export OPENAI_API_KEY=sk-...
python generate_sample_outputs.py
```

This runs the full agent (real OpenAI API call) and overwrites these files.

> Note: re-run this once with your own key before submitting, so the committed `parsed_request` block reflects an actual model response rather than the pre-generated illustrative one.

## Why these are committed

So a reviewer can see what "good" looks like in 30 seconds without
needing to install anything or use an API key.
