"""
invite.py
---------
Build TWO things from a chosen slot:

1. A human-readable invite draft Sara can paste straight into Gmail
   or read in Slack: title, times, purpose, attendees, body, Granola link.

2. A .ics calendar file content for one-click "add to calendar."
"""

from ics import Calendar, Event
from zoneinfo import ZoneInfo


def build_invite(slot, intent: dict, invite_convention: dict) -> dict:
    """
    Returns a dict containing both:
      - 'human_readable': a paste-ready text draft
      - 'ics_content':    the .ics file body
      - plus the structured fields (title, body, times, attendees)
    """
    title = invite_convention["title_format"].format(
        topic=intent.get("topic", "Meeting"),
        scope=intent.get("scope", "Studio"),
    )

    granola_link = invite_convention["default_granola_link"]
    body = invite_convention["body_template"].format(
        purpose=intent.get("topic", "Discussion"),
        granola_link=granola_link,
    )

    # Build .ics file content
    cal = Calendar()
    ev = Event()
    ev.name = title
    ev.begin = slot.start_doha
    ev.end = slot.end_doha
    ev.description = body
    cal.events.add(ev)
    ics_content = cal.serialize()

    # Attendee local times (for both the draft and the JSON)
    attendees_display = []
    attendees_meta = []
    for a in intent.get("attendees", []):
        local = slot.start_doha.astimezone(ZoneInfo(a["timezone"]))
        attendees_display.append(
            f"  - {a['name']} ({a['timezone']}): "
            f"{local.strftime('%a %d %b %Y, %H:%M')} local"
        )
        attendees_meta.append({
            "name": a["name"],
            "timezone": a["timezone"],
            "role": a.get("role", "external"),
            "local_time": local.isoformat(),
        })

    # Human-readable draft (paste straight into Gmail)
    doha_str = slot.start_doha.strftime("%A %d %B %Y, %H:%M")
    end_str = slot.end_doha.strftime("%H:%M")
    purpose_text = intent.get("topic", "Discussion")

    human_readable = (
        f"Title: {title}\n"
        f"\n"
        f"Doha time:  {doha_str} - {end_str} (Asia/Qatar, UTC+3)\n"
    )
    if attendees_display:
        human_readable += "Attendee local times:\n"
        human_readable += "\n".join(attendees_display) + "\n"
    human_readable += (
        f"\n"
        f"Purpose: {purpose_text}\n"
        f"\n"
        f"Attendees:\n"
    )
    if intent.get("attendees"):
        for a in intent["attendees"]:
            human_readable += f"  - {a['name']} ({a.get('role', 'external')})\n"
    else:
        human_readable += "  (none specified)\n"

    human_readable += (
        f"\n"
        f"Body:\n"
        f"{body}\n"
        f"\n"
        f"Granola: {granola_link}  (placeholder - replace with real link if recorded)\n"
    )

    return {
        "title": title,
        "body": body,
        "purpose": purpose_text,
        "start_doha_iso": slot.start_doha.isoformat(),
        "end_doha_iso": slot.end_doha.isoformat(),
        "attendees": attendees_meta,
        "granola_link": granola_link,
        "human_readable": human_readable,
        "ics_content": ics_content,
    }
