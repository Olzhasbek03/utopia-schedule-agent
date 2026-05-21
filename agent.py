"""
agent.py
--------
The main scheduling agent. Wires parser -> scheduler -> invite together
and emits the JSON contract that Agent 2 (announcer.py) consumes.

Usage:
    python agent.py "30 min with a London investor next week, Tuesday morning"

Outputs to stdout:  the full handoff JSON
Also writes:        proposed_invite.ics in the working directory
"""

import json
import sys
from datetime import datetime
from pathlib import Path

from parser import parse_request
from scheduler import find_candidate_slots, load_config, slot_in_attendee_tz
from invite import build_invite


BASE_DIR = Path(__file__).resolve().parent


def _serialise_slot(slot, intent: dict) -> dict:
    """One slot in the proposed_slots[] array."""
    attendee_local_times = {}
    for a in intent.get("attendees", []):
        attendee_local_times[a["timezone"]] = (
            slot_in_attendee_tz(slot, a["timezone"]).isoformat()
        )
    return {
        "start_time_doha": slot.start_doha.isoformat(),
        "end_time_doha": slot.end_doha.isoformat(),
        "duration_min": slot.duration_min,
        "attendee_local_times": attendee_local_times,
        "status": slot.status,
        "conflicts": slot.conflicts,
        "rationale": slot.rationale,
    }


def run(user_text: str, ics_path: str = "proposed_invite.ics") -> dict:
    """
    Top-level. Takes one English sentence; returns the full handoff JSON
    and writes the .ics file to disk.
    """
    config = load_config(str(BASE_DIR / "recurring_meetings.yaml"))

    # Step 1: parse English to intent (real LLM/API call)
    parsed = parse_request(user_text)

    # Step 2: find candidate slots (deterministic Python)
    slots = find_candidate_slots(parsed, config)

    if not slots:
        return {
            "schema_version": "1.0",
            "agent": "schedule_agent",
            "original_request": user_text,
            "parsed_request": parsed,
            "proposed_slots": [],
            "selected_recommended_slot": None,
            "calendar_invite_draft": None,
            "ics_file_path": None,
            "second_agent_handoff": {"target_agent": "announcer", "status": "no_slots_found"},
            "status": "no_slots_found",
        }

    # Step 3: build invite for the top-ranked slot
    chosen = slots[0]
    invite = build_invite(chosen, parsed, config["invite_convention"])

    # Step 4: write the .ics to disk so the operator can double-click it
    Path(ics_path).parent.mkdir(parents=True, exist_ok=True)
    with open(ics_path, "w") as f:
        f.write(invite["ics_content"])

    # Step 5: assemble the handoff JSON
    proposed_slots = [_serialise_slot(s, parsed) for s in slots]
    selected = proposed_slots[0]

    return {
        "schema_version": "1.0",
        "agent": "schedule_agent",
        "request_id": f"req_{int(datetime.now().timestamp())}",
        "original_request": user_text,
        "parsed_request": parsed,
        "proposed_slots": proposed_slots,
        "selected_recommended_slot": selected,
        "calendar_invite_draft": {
            "title": invite["title"],
            "body": invite["body"],
            "purpose": invite["purpose"],
            "human_readable": invite["human_readable"],
            "attendees": invite["attendees"],
            "granola_link": invite["granola_link"],
        },
        "ics_file_path": ics_path,
        "second_agent_handoff": {
            "target_agent": "announcer",
            "purpose": "draft Slack announcement to attendees",
            "status": "ready_to_consume",
        },
        "status": "ready_to_send",
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python agent.py "your scheduling request"', file=sys.stderr)
        sys.exit(1)

    user_text = " ".join(sys.argv[1:])
    try:
        output = run(user_text)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(output, indent=2, default=str))
    print(f"\n.ics file written to: {output.get('ics_file_path')}", file=sys.stderr)
