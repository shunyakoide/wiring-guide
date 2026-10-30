---
description: The skill should stay out for this request
tags: [trigger]
runs: 3
max_turns: 3
timeout_seconds: 120
---
My Arduino sketch's debounce logic fires twice on each press. Here it is: if (digitalRead(2) == LOW) { count++; delay(10); } How do I fix the code?
