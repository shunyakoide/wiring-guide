---
type: llm
---
Judge only whether the answer stops to ask the user for information.
PASS if the answer gives the wiring and does not ask the user for any information it needs. Listed assumptions, things to check while building, and invitations such as "tell me if a label covers something" are not questions.
FAIL if it asks about LED color, wire colors, board placement or anything else before or instead of giving the wiring.
