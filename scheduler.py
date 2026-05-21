"""
scheduler.py
------------
Deterministic Python that, given parsed intent + the recurring meetings,
proposes 2-3 ranked candidate slots with conflict status and rationale.

No LLM here on purpose: "does interval A overlap interval B?" is a
question with one correct answer. We don't want a model guessing.
"""

from __future__ import annotations
import yaml
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dataclasses import dataclass
from typing import Optional


DOHA = ZoneInfo("Asia/Qatar")

WEEKDAY_NUM = {
    "Monday": 0, "Tuesday": 1, "Wednesday": 2,
    "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6,
}

# Map time_preference labels to (start_hour, end_hour) in Doha local time.
TIME_WINDOWS = {
    "morning":   (9, 12),
    "afternoon": (12, 17),
    "evening":   (17, 20),
    None:        (9, 17),
}


@dataclass
class Slot:
    """One candidate meeting slot."""
    start_doha: datetime
    duration_min: int
    conflicts: list   # list of conflict dicts: {name, start, end}
    rationale: str = ""

    @property
    def end_doha(self) -> datetime:
        return self.start_doha + timedelta(minutes=self.duration_min)

    @property
    def status(self) -> str:
        return "conflict" if self.conflicts else "clean"


def load_config(path: str = "recurring_meetings.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def _expand_recurring_for_week(config: dict, week_start_monday: datetime) -> list[dict]:
    """Turn every-Monday-10:00 into concrete datetimes for the target week."""
    occurrences = []
    for meeting in config["recurring_meetings"]:
        days = (["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                if meeting["day"] == "daily" else [meeting["day"]])
        for day_name in days:
            offset = WEEKDAY_NUM[day_name]
            day_date = week_start_monday + timedelta(days=offset)
            hour, minute = map(int, meeting["start"].split(":"))
            start = day_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            occurrences.append({
                "name": meeting["name"],
                "start": start,
                "end": start + timedelta(minutes=meeting["duration_min"]),
            })
    return occurrences


def _overlaps(a_start, a_end, b_start, b_end) -> bool:
    """True if two time intervals overlap at all."""
    return a_start < b_end and b_start < a_end


def _monday_of_week(target_week_offset: int, reference: datetime) -> datetime:
    """Return Monday 00:00 (Doha) of the target week."""
    days_since_monday = reference.weekday()
    this_monday = reference - timedelta(days=days_since_monday)
    this_monday = this_monday.replace(hour=0, minute=0, second=0, microsecond=0)
    return this_monday + timedelta(weeks=target_week_offset)


def _build_rationale(slot_start, slot_end, conflicts, intent, fellow_only) -> str:
    """Plain-English explanation of why this slot is or isn't a good pick."""
    parts = []
    day = slot_start.strftime("%A")
    parts.append(f"{day} {slot_start.strftime('%H:%M')}-{slot_end.strftime('%H:%M')} Doha")

    if not conflicts:
        parts.append("no conflicts with recurring meetings")
    else:
        names = ", ".join(c["name"] for c in conflicts)
        parts.append(f"overlaps with {names}")

    if fellow_only and day in ("Monday", "Tuesday", "Wednesday"):
        parts.append("inside fellow-availability window (Mon-Wed)")

    if intent.get("time_preference"):
        parts.append(f"matches '{intent['time_preference']}' preference")

    return "; ".join(parts) + "."


def find_candidate_slots(
    intent: dict,
    config: dict,
    reference_time: Optional[datetime] = None,
    max_candidates: int = 3,
) -> list[Slot]:
    """
    Return up to 3 candidate slots ranked best-first.
    """
    if reference_time is None:
        reference_time = datetime.now(DOHA)

    duration = intent.get("duration_min", 30)
    week_offset = intent.get("week_offset", 0)
    monday = _monday_of_week(week_offset, reference_time)

    fellow_days = config["fellow_availability_days"]
    is_fellow = intent.get("is_fellow_meeting", False)

    if intent.get("day_preference"):
        candidate_days = [intent["day_preference"]]
    elif is_fellow:
        candidate_days = fellow_days
    else:
        candidate_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    win_start_hour, win_end_hour = TIME_WINDOWS[intent.get("time_preference")]
    busy = _expand_recurring_for_week(config, monday)

    candidates: list[Slot] = []
    step = timedelta(minutes=30)

    for day_name in candidate_days:
        day_date = monday + timedelta(days=WEEKDAY_NUM[day_name])
        slot_start = day_date.replace(hour=win_start_hour, minute=0, second=0, microsecond=0)
        window_end = day_date.replace(hour=win_end_hour, minute=0, second=0, microsecond=0)

        while slot_start + timedelta(minutes=duration) <= window_end:
            slot_end = slot_start + timedelta(minutes=duration)
            conflicts = [
                {"name": m["name"],
                 "start": m["start"].isoformat(),
                 "end": m["end"].isoformat()}
                for m in busy
                if _overlaps(slot_start, slot_end, m["start"], m["end"])
            ]
            rationale = _build_rationale(slot_start, slot_end, conflicts, intent, is_fellow)
            candidates.append(Slot(
                start_doha=slot_start,
                duration_min=duration,
                conflicts=conflicts,
                rationale=rationale,
            ))
            slot_start += step

    # Rank: clean slots first, then earlier in the week
    candidates.sort(key=lambda s: (len(s.conflicts), s.start_doha))

    # Try to spread top picks across days for variety
    top: list[Slot] = []
    seen_days = set()
    for c in candidates:
        day_key = c.start_doha.date()
        if day_key not in seen_days:
            top.append(c)
            seen_days.add(day_key)
        if len(top) >= max_candidates:
            break
    if len(top) < max_candidates:
        for c in candidates:
            if c not in top:
                top.append(c)
                if len(top) >= max_candidates:
                    break

    return top


def slot_in_attendee_tz(slot: Slot, tz_name: str) -> datetime:
    """Convert a slot's start to an attendee's local timezone."""
    return slot.start_doha.astimezone(ZoneInfo(tz_name))
