# Utopia Studio Take-Home — Writeup

## Operator & problem

I built this for the Founder’s Associate at Utopia Studio. This person has to book calls around recurring studio meetings, fellows’ availability, and external time zones like Doha, London, and Singapore. Right now, that means manually checking blocked slots, doing timezone math, and writing calendar invites in the right studio format. It is a small task once, but when it happens several times a day, it becomes easy to lose time or accidentally double-book something like the QDB Monday 14:00 meeting.

## The agent

I built a scheduling agent for the Admin track. It takes one plain-English request, for example: “30 min with a London investor next week, Tuesday morning ideal.” The agent uses the OpenAI API to turn that request into structured JSON, then uses deterministic Python to check recurring meetings and return three ranked time options in Doha time. It also creates a human-readable calendar invite draft, writes a `.ics` file, and passes structured JSON to a second agent that drafts the Slack announcement.


## Sample input
" 30 min with a London investor next week, Tuesday morning ideal"


## Sample output

{
  "selected_recommended_slot": {
    "start_time_doha": "2026-05-26T09:30:00+03:00",
    "end_time_doha": "2026-05-26T10:00:00+03:00",
    "attendee_local_times": {
      "Europe/London": "2026-05-26T07:30:00+01:00"
    },
    "status": "clean",
    "conflicts": [],
    "rationale": "Tuesday 09:30-10:00 Doha; no conflicts with recurring meetings; matches 'morning' preference."
  },
  "calendar_invite_draft": {
    "title": "[Investor intro call] · [Studio]"
  },
  "ics_file_path": "sample_outputs/calendar_invite.ics",
  "second_agent_handoff": {
    "target_agent": "announcer",
    "status": "ready_to_consume"
  }
}

## Explanation

Full output is saved in sample_outputs/admin_schedule_output.json. The Slack draft from Agent 2 is saved in sample_outputs/slack_handoff.txt.

## What I cut
I cut direct Google Calendar creation. A .ics file was faster to build, easier to test, and still useful because the operator can review it before sending.
I cut multi-turn clarification. I wanted the agent to work as a simple one-input, one-output tool, so it makes its best guess and lists assumptions in the JSON.
I cut LLM-based conflict handling. The LLM only parses the request; I kept the actual scheduling and conflict checks in Python so the logic is predictable.


## What broke or surprised me
The brief only gave one exact recurring meeting time: QDB weekly on Monday at 14:00. For the other meetings, I had to use editable default times in recurring_meetings.yaml instead of pretending the brief gave exact times.
Datetime objects did not serialize nicely into JSON at first, so I added a cleaner slot serialization step in agent.py.
I used OpenAI because I had API access, but I kept the parser separate from the scheduler. In a production Utopia setup, I could swap the parser to Anthropic without rewriting the whole agent.


## If I had two more days
I would add Google Calendar creation after the operator confirms a slot.
I would connect Slack so Agent 2 can post the message directly instead of only drafting it.
I would query the real calendar, not just recurring meetings, so one-off conflicts are also caught.
