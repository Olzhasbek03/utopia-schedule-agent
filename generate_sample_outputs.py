"""
generate_sample_outputs.py
--------------------------
Runs the FULL agent end-to-end with a real OpenAI API call and writes
the three sample artifacts to sample_outputs/.

Usage:
    cp .env.example .env
    # paste your real OPENAI_API_KEY into .env
    python generate_sample_outputs.py
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

from agent import run
from announcer import draft_slack_message


load_dotenv()

SAMPLE_INPUT = "30 min with a London investor next week, Tuesday morning ideal"


def main():
    out_dir = Path("sample_outputs")
    out_dir.mkdir(exist_ok=True)

    ics_path = out_dir / "calendar_invite.ics"
    json_path = out_dir / "admin_schedule_output.json"
    slack_path = out_dir / "slack_handoff.txt"

    # Run Agent 1 end-to-end with the real OpenAI parser.
    agent_output = run(SAMPLE_INPUT, ics_path=str(ics_path))

    # Save the full JSON contract.
    json_path.write_text(json.dumps(agent_output, indent=2, default=str))

    # Run Agent 2 and save its Slack message.
    slack_text = draft_slack_message(agent_output)
    slack_path.write_text(slack_text)

    print("Wrote:")
    print(f"  {json_path}")
    print(f"  {ics_path}")
    print(f"  {slack_path}")


if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit(
            "Missing OPENAI_API_KEY. Copy .env.example to .env, paste your key, "
            "then rerun python generate_sample_outputs.py."
        )
    main()
