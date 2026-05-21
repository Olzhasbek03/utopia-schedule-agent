
> "Hi! This is my take-home for the Admin track, I didn't find assignment for my track and picked this one. 
>
> **Who is the operator?** The Founder's Associate at Utopia Studio. She runs six recurring meetings every week and gets asked, several times a day, to book ad-hoc calls around them — across Doha, London, Singapore, sometimes APAC.
>
> **What was she doing manually?** For every request she remembers which of the six recurring meetings are blocking, does timezone math in her head, picks a slot, writes the invite in the studio's `[Topic] - [Studio/Fellow]` format, and sends. Roughly ten minutes per request, and the failure mode is the occasional double-booking when something like QDB Monday at 14:00 slips her mind.
>
> **What does the agent do, in plain language?** She types one sentence — "30 minutes with a London investor next Tuesday morning" — and the agent gives back three ranked Doha times, says which ones clash with which recurring meeting, drafts the calendar invite in the studio format, and writes the Slack message announcing the time to the attendee in their own local time. It's two agents talking through structured JSON — the Utopia OS pattern."

1. **Show `dev_tests/edge_case_qdb_collision.py` running.**
   > "First, the scheduling math has to be right. This test asks the agent for a Monday afternoon meeting — exactly when QDB weekly sits — and verifies the agent never proposes a time that overlaps QDB. You can see the full Monday afternoon walk: 13:30, 14:00, 14:30 all flagged as conflicts with QDB; the surrounding slots are clean. This is pure Python, not the LLM, so it's deterministic — same input, same output, every time."

2. **Show the live agent.** Run:
   ```
   python agent.py "30 min with a London investor next week, Tuesday morning ideal"
   ```
   > "The dev test runs without an API key, but this final demo is end-to-end with the real OpenAI API parser. GPT parses my sentence into structured intent — duration 30, attendee in `Europe/London`, day Tuesday, week offset 1. Then Python finds three clean morning slots, all on Tuesday 26 May, and pre-computes the investor's London time for each. The top pick is 09:30 Doha which is 07:30 London — investor-friendly."

3. **Open the `.ics` file.** Double-click `proposed_invite.ics`.
   > "Calendar app picks it up. Title `[Investor intro call] · [Studio]` — studio convention. Granola placeholder in the body. She hits 'send' — done."

4. **Run `python announcer.py out.json`.**
   > "Agent 2 reads Agent 1's JSON — no shared memory, no second LLM call. Out comes the Slack draft with Doha time, London time, two backup options, and confirmation emojis. The reviewer can read the exact same files in `sample_outputs/`."

> "Two halves. Half one is a translator — it reads English and writes down what you meant in a form a machine can use. Half two is a calendar that knows your six recurring meetings; it walks every 30-minute slot in the window you asked for, crosses out the ones that clash, and hands you the cleanest three. A separate small program reads that list and writes the Slack message. If the six meetings change, if you want a different Slack tone, if you want to swap the LLM — three separate small edits, not a rewrite."


> "Three deliberate cuts. One: no Google Calendar write — `.ics` keeps you in control. Two: no multi-turn chat — single input, single output, every assumption surfaced in the JSON. Three: no LLM-based conflict negotiation — when options clash, the agent reports honestly. All three are in the two-more-days list. Thanks — happy to walk through the code live."

