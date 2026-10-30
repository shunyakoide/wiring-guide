# Evals

What each item below proves, and what it does not. A result only counts for the row it is in.

| What we want | Unit tests (no cost) | Model evals (`claude plugin eval`, costs money) | Still needs a person |
|---|---|---|---|
| 1. Wiring is correct | The drawn SVG's holes rebuild the same nets as `connect`; bad holes, pins and legs stop | `accuracy-*`: a model reads the request and writes the right connections | That facts in a spec match a real datasheet, and a real build works |
| 2. Hazards are found | Every rule in the script, in `tests/` | `hazard-*`: hazards needing a datasheet or judgment | Hazards in no case here. No result here proves a circuit safe |
| 3. Page is easy to read | Text size, wire badge overlap, step, table and theme structure only | None: the judge does not see the page | The sheet below |
| 4. No needless questions | None | `questions-*` | Borderline answers: read the transcript |
| 5. Starts at the right time | None | `trigger-*`, `skip-*` | Requests in no case here |

`llm` graders are a model's opinion from one small sample. Read failures in the transcript before changing the skill.

## Run

```
python3 -m unittest discover tests
claude plugin eval . --case 'trigger-*' --ablation none --no-publish
claude plugin eval . --case 'skip-*' --ablation none --no-publish
claude plugin eval . --case 'hazard-*' --ablation none --no-publish --allow-tools Bash Write Edit Read --max-cost-usd 10
```

Results go to `evals/results/` (not in git). The runs are in an isolated home, with no user settings.

## Reviewing a page by hand

Build the example, open it in light and dark, and at phone width. Fail it on any "no".

1. Can you name both ends of every wire without reading the table?
2. Are all hole numbers, letters and pin labels readable, with none hidden by a wire, part or label?
3. Do wire numbers match the table and the steps?
4. Does each step, on its own, tell you what to place and where?
5. Are the LED's long leg and the resistor's value easy to find?
6. Could a beginner follow it without asking anything?
