"""
parser.py
---------
Turns a plain-English scheduling request into structured intent JSON.

We use the OpenAI Chat Completions API. The model's only job here is
fuzzy-to-structured: "next Tuesday morning" -> day_preference: Tuesday,
time_preference: morning, week_offset: 1. We do NOT use the LLM for
the actual scheduling math - that's deterministic Python in scheduler.py.
"""

import json
import os
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()


SYSTEM_PROMPT = """You are a scheduling intent parser for Utopia Studio's
Founder's Associate. Your only job is to convert a plain-English scheduling
request into a single JSON object with this exact shape:

{
  "duration_min": <integer, default 30 if not stated>,
  "topic": "<short string, what the meeting is about>",
  "scope": "<one of: Studio, Fellow, External>",
  "attendees": [
    {"name": "<person or org>", "timezone": "<IANA tz like Europe/London>", "role": "<internal|fellow|external>"}
  ],
  "day_preference": "<Monday|Tuesday|Wednesday|Thursday|Friday|null>",
  "time_preference": "<morning|afternoon|evening|null>",
  "week_offset": <0 for this week, 1 for next week, etc>,
  "is_fellow_meeting": <true if a fellow is an attendee, else false>,
  "assumptions": ["<plain-English notes about anything you guessed>"]
}

Rules:
- If duration not stated, default to 30 minutes.
- "morning" = 09:00-12:00 Doha, "afternoon" = 12:00-17:00, "evening" = 17:00-20:00.
- If the request mentions a city, infer the IANA timezone (London -> Europe/London,
  Singapore -> Asia/Singapore, NYC -> America/New_York, Doha -> Asia/Qatar).
- If a fellow is mentioned, set scope to "Fellow" and is_fellow_meeting to true.
- If no timezone clue, default attendee timezone to Asia/Qatar.
- Always include at least one attendee (default to Asia/Qatar if unknown).
- Output ONLY the JSON object."""


def parse_request(user_text: str) -> dict:
    """
    Send the user's text to GPT and get back structured intent.
    Returns a Python dict matching the schema above.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing OPENAI_API_KEY. Copy .env.example to .env, paste your key, "
            "then rerun the full agent."
        )

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # cheap, fast, fine for structured extraction
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
        response_format={"type": "json_object"},  # guarantees valid JSON
        temperature=0,  # deterministic: same input -> same output
    )

    return json.loads(response.choices[0].message.content)


# Allow running this file directly to test the parser in isolation.
if __name__ == "__main__":
    test_input = "30 min with a London investor next week, Tuesday morning ideal"
    print(json.dumps(parse_request(test_input), indent=2))
