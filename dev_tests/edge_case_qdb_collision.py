"""
DEV TEST - NOT PART OF THE AGENT FLOW.

edge_case_qdb_collision.py
--------------------------
Hard-coded "parsed intent" that asks for a meeting on Monday afternoon -
exactly when QDB weekly (Mon 14:00 Doha) sits.

The agent's scheduler MUST flag QDB as a conflict for any 14:00 candidate.
This file proves the conflict logic works without needing an API key.

Run:  python dev_tests/edge_case_qdb_collision.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from zoneinfo import ZoneInfo
from scheduler import find_candidate_slots, load_config


# Hard-coded intent: "Schedule a partner meeting on Monday afternoon"
INTENT = {
    "duration_min": 60,
    "topic": "Partner sync",
    "scope": "Studio",
    "attendees": [{"name": "Partner", "timezone": "Asia/Qatar", "role": "external"}],
    "day_preference": "Monday",
    "time_preference": "afternoon",
    "week_offset": 1,
    "is_fellow_meeting": False,
    "assumptions": []
}

REFERENCE = datetime(2026, 5, 19, 10, 0, tzinfo=ZoneInfo("Asia/Qatar"))
config = load_config("recurring_meetings.yaml")
slots = find_candidate_slots(INTENT, config, reference_time=REFERENCE)

print("EDGE CASE: Monday afternoon meeting (QDB lives at 14:00 Doha)\n")
print("Top 3 ranked candidates:")
print("-" * 70)
for i, s in enumerate(slots, 1):
    print(f"{i}. {s.start_doha.strftime('%a %H:%M')} -> {s.end_doha.strftime('%H:%M')}  [{s.status}]")
    if s.conflicts:
        for c in s.conflicts:
            print(f"     conflict: {c['name']}")
    print(f"     rationale: {s.rationale}")
    print()

# Assertion: none of the top 3 should overlap with QDB (14:00-15:00)
qdb_collisions = [
    s for s in slots
    if any(c["name"] == "QDB weekly" for c in s.conflicts)
]
if qdb_collisions:
    print("FAIL: top-3 contains a QDB collision (the agent should avoid this)")
    sys.exit(1)

# Also: walk every Mon afternoon slot and confirm 13:30/14:00/14:30 ARE flagged
print("\nFull Monday-afternoon walk (proves QDB is detected, not just avoided):")
print("-" * 70)
from scheduler import _expand_recurring_for_week, _overlaps, _monday_of_week
from datetime import timedelta

monday = _monday_of_week(1, REFERENCE)
busy = _expand_recurring_for_week(config, monday)
slot = monday.replace(hour=12, minute=0)
end = monday.replace(hour=17, minute=0)
detected_qdb = False
while slot + timedelta(minutes=60) <= end:
    slot_end = slot + timedelta(minutes=60)
    conflicts = [m["name"] for m in busy
                 if _overlaps(slot, slot_end, m["start"], m["end"])]
    flag = f"CONFLICT ({', '.join(conflicts)})" if conflicts else "clean"
    if "QDB weekly" in conflicts:
        detected_qdb = True
    print(f"  {slot.strftime('%H:%M')}-{slot_end.strftime('%H:%M')}  {flag}")
    slot += timedelta(minutes=30)

if not detected_qdb:
    print("\nFAIL: QDB weekly was never detected as a conflict.")
    sys.exit(1)

print("\nPASS: QDB correctly detected and avoided.")
