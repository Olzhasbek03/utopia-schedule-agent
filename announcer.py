"""
announcer.py
------------
Agent 2 in the Utopia OS pattern.

Reads the JSON output of the scheduling agent (Agent 1) and drafts a
ready-to-send Slack message announcing the proposed meeting time to all
attendees, showing each their LOCAL time so nobody does timezone math.

No LLM here on purpose - the JSON contract is structured enough that
plain templating is more reliable.

Usage:
    python agent.py "..." > out.json
    python announcer.py out.json
"""

import json
import sys
from datetime import datetime


def _pretty(iso_str: str) -> str:
    """Turn '2026-05-26T10:00:00+03:00' into 'Tue 26 May, 10:00'."""
    return datetime.fromisoformat(iso_str).strftime("%a %d %b, %H:%M")


def draft_slack_message(agent_output: dict) -> str:
    """Take the full schedule_agent output, return a Slack-ready string."""
    if agent_output.get("status") == "no_slots_found":
        return (":warning: No clean slots found for that request. "
                "Could you widen the window or pick another day?")

    selected = agent_output["selected_recommended_slot"]
    parsed = agent_output["parsed_request"]
    invite = agent_output["calendar_invite_draft"]

    lines = []
    lines.append(f":calendar: *Proposed: {invite['title']}*")
    lines.append("")
    lines.append(
        f"*Doha time:* {_pretty(selected['start_time_doha'])} "
        f"({selected['duration_min']} min)"
    )

    if selected.get("attendee_local_times"):
        lines.append("")
        lines.append("*Local times for attendees:*")
        for attendee in parsed.get("attendees", []):
            tz = attendee["timezone"]
            local_iso = selected["attendee_local_times"].get(tz)
            if local_iso:
                lines.append(
                    f"  - {attendee['name']} ({tz}): {_pretty(local_iso)}"
                )

    # Backup options (other clean slots)
    backups = [
        s for s in agent_output["proposed_slots"]
        if s["start_time_doha"] != selected["start_time_doha"]
        and s["status"] == "clean"
    ]
    if backups:
        lines.append("")
        lines.append("*Backup options if this doesn't work:*")
        for b in backups[:2]:
            lines.append(f"  - {_pretty(b['start_time_doha'])} Doha")

    # If the recommended slot has conflicts, flag them
    if selected["status"] == "conflict":
        lines.append("")
        lines.append(":warning: *Heads up - top option has conflicts:*")
        for c in selected["conflicts"]:
            lines.append(f"  - clashes with {c['name']}")

    lines.append("")
    lines.append(f"_Purpose:_ {invite['purpose']}")
    lines.append(f"_Granola link:_ {invite['granola_link']}")
    lines.append("")
    lines.append(
        ":white_check_mark: React :+1: to confirm or "
        ":calendar_spiral: to suggest another time."
    )

    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        if not sys.stdin.isatty():
            agent_output = json.load(sys.stdin)
        else:
            print("Usage: python announcer.py <path-to-agent-output.json>")
            sys.exit(1)
    else:
        with open(sys.argv[1]) as f:
            agent_output = json.load(f)

    print(draft_slack_message(agent_output))
