---
name: wiring-guide
description: Show wiring, breadboard placement, soldering spots and multimeter probe points as an illustrated page, and keep an index of how far the build has come. Use whenever you explain how to wire or assemble something physical ("where does this go", "check my wiring", "which hole", "where do I solder", "where do I probe"), even if the user does not ask for a picture (also 「どこに挿す」「配線を確認」「どこをハンダ付け」「テスターでどこを測る」). Do not use for schematic or PCB layout design, or for firmware-only questions.
license: MIT. Complete terms in LICENSE.txt
---

# Wiring guide

Explain wiring with **one page that has a drawing**. The page shows how to wire and nothing else: the drawing, steps, table and damage warnings. In chat, write one or two lines on what to check and the link, then a short list of what you assumed without asking, then the sketch to try (see "Trying it"). Write the page and the progress notes in the user's language. Aim to finish in about three minutes: write the spec, run the script once or twice, look once.

## Steps

1. **Know the board.** Read the project's notes (its CLAUDE.md or AGENTS.md, your memory, the progress file). If the breadboard's size, which end number 1 is at, which letter is nearest the user, the rails, or where the other board sits is not written anywhere, ask once and record the answer there. For a value the user did not give (LED color, supply voltage), assume the common one and list it in chat.
2. **Write a spec and run [breadboard.py](breadboard.py).** List the parts and what connects to what; the script picks every hole, adds the wires, writes the steps and the table, draws the page, and checks it. One request gets one page with everything the user asked for. See "The spec".
   `python3 <this skill>/breadboard.py spec.json page.html`
   It prints every net, then any `ERROR:`. Fix each error. If it says a part has no room, keep what fits and say in chat what would fit the rest (a bigger breadboard); never drop a resistor to make room. Read the nets once against the circuit you meant.
3. **Damage warnings.** Add a `notes` entry only for what can damage a part: a 5 V signal into a 3.3 V pin, an LED without a resistor or over the pin's current (5–15 mA on a 5 V Arduino, a few mA on a Pico), a motor or relay coil without a flyback diode, a servo or motor on the board's 5 V pin, a coil "buzzer" (tens of ohms) straight on a pin, modules whose pin order differs (go by the printing). Check pins against the board's file in [boards/](boards/).
4. **Look once.** One desktop screenshot of the page (headless Chrome is fine). If a label hides something, move a part or reorder parts and run again.
5. **Publish.** With the Artifact tool: publish (same `url` for a page that is rewritten) and `open` it. Without it: save the HTML where the project keeps such files and give its path.
6. **Progress notes** (see below): add the page and the planned positions, then rebuild the index:
   `python3 <this skill>/render_index.py <progress.md> <index.html> "<project> build log" <lang>`

For soldering spots, probe points, or anything that is not a breadboard, draw by hand with [drawing.md](drawing.md).

## The spec

Start from [spec.example.json](spec.example.json).

- `lang`, `title`, `eyebrow`, `lead`, `notes` (damage warnings, HTML). For a language other than `en` or `ja`, add `words` with every key of `WORDS` in the script translated.
- `board`: `rows` (30 half, 63 full, 17 mini), `row1` (`left`/`right`), `near` (letter nearest the user, `a` or `j`), `rails` (`both`, `far`, `near`, `none`), `outer` (sign of the outer rails, `-` or `+`).
- `boards`: a board plugged into the breadboard (Pico, Nano) has `id`, `label`, `span` [first, last number], `usb` (`left`/`right`, drawn as a port so the user can match the direction) and `pins` {letter: [pin names in number order]}. A board beside it has `"kind": "offboard"`, `side` (`far`/`near`), `usb` (`left`/`right`), `jack` (true for a round power jack, as on an Uno) and `headers`, nearest the breadboard first, each with `name`, `at` (the number its first socket lines up with) and `pins` (every socket in order, `""` unlabelled, `null` a gap). Copy pin orders from boards/.
- `parts`: `id` and `kind`: `resistor` (`value`: `220`, `4.7k`), `led` (`color`), `cap` (`polar`), `buzzer`, `diode`, `switch` (4-leg tactile), `dip` (`pins`, short `names`), `pot`, `rgb`, `module`, `part` (`names` of the legs in order).
- `connect`: groups of things joined together. A leg is `R1.1`, `R1.2`, `LED1.+`, `LED1.-`, `SW1.1`, `SW1.2`, or a name from `names` (`LED1.K`). A board pin is `uno.5V` or `pico.GP15` (`pico.GND#2` for the second GND; plain `GND` takes the first). `-` and `+` are the rails: put the board's GND pin and every GND leg in the `-` group, and its supply pin in the `+` group.

To draw wiring exactly as the user built it (checking their work), give each part `legs` (holes such as `14f`; rails `F-12`, `N+3`; `[name, hole]` for named legs; `pairs` for a switch; `pin1` for a chip) and `wires` (`n`, `from`, `to`, `color`, `dashed` for a fix) instead of `connect`; the script then only draws and checks.

## Trying it

The sketch goes in chat. Give one that tests every part, what it should show, and where to look if it does not:

- LED: Blink (File → Examples → 01.Basics → Blink) with the pin changed. On and off once a second.
- Button: `INPUT_PULLUP` and print `digitalRead` (check boards/ for pins without pull-ups). 1 released, 0 pressed.
- I2C: [sketches/i2c_scan/i2c_scan.ino](sketches/i2c_scan/i2c_scan.ino). The address from the datasheet (an SSD1306 is usually 0x3C).
- Anything else: print the raw reading or sweep slowly, with the range to expect at each end.

Do not drive pins as outputs unless the page shows nothing else on them.

## Progress notes

One Markdown file per project, outside the repository: the user's notes folder if they have one, otherwise `~/.wiring-guide/<repo>/progress.md`. Record its path where you keep the board facts. Three `##` sections, headings in the user's language:

1. Now / next: the next step and what the user should see when it works. Positions a page plans are "planned, not yet placed" until the user reports them done, one top-level bullet each.
2. Pages: a table `| stage | page | url | status | updated |`; the url is the artifact link or the file's absolute path. Status starting with ✓ shows green, ↗ grey, anything else orange.
3. Log: newest first.

See [progress.example.md](progress.example.md).
