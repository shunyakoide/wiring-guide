---
name: wiring-guide
description: Show exact wiring, breadboard placement, soldering spots and multimeter probe points as an illustrated page, check the circuit for electrical hazards first, and keep an index of how far the build has come. Use whenever you explain where parts or wires physically go or the steps to assemble something ("where does this go", "which hole", "check my wiring", "wire this sensor to my Pico", "where do I solder", "where do I probe"), or when asked for a wiring diagram or a picture of the connections, even if the user does not ask for a picture (also 「どこに挿す」「配線を教えて」「配線図を描いて」「配線を確認」「組み立て手順」「どこをハンダ付け」「テスターでどこを測る」). Do not use for general electronics questions (how a part works, which part to buy, calculations alone), schematic or PCB layout design, or firmware-only questions.
license: MIT. Complete terms in LICENSE.txt
---

# Wiring guide

Explain wiring with **one page that has a drawing**. The page shows how to wire and nothing else: the drawing, steps, table and damage warnings. In chat, write one or two lines on what to check and the link, then a short list of what you assumed without asking, then the sketch to try (see "Trying it"). Write the page and the progress notes in the user's language. Aim to finish in about three minutes: write the spec, run the script once or twice, look once. Safety comes before that aim.

## Safety

A wrong voltage, polarity or pin can destroy a part or overheat it. These rules apply to every page, drawn by the script or by hand.

- **Do not guess** supply voltage, GPIO voltage tolerance, polarity, current limits or pin order. Take them from the user, the project's notes, [boards/](boards/), then the manufacturer's datasheet or official docs, in that order. Never from memory of a similar part, a seller's listing or a forum.
- **If you cannot confirm one, do not finish that wiring.** Ask one specific question, or draw only the part you could confirm and say what is left out.
- **Assume freely what cannot damage anything** (LED color, wire color, which free pin to use) and list it in chat. Do not ask about these.
- **Never draw a dangerous circuit as if it were fine**, even when asked to. Say what would break and give the fix. To show wiring the user already built, use `as_built`.
- **State the limits.** In chat, say what the script checked, what you read in which datasheet, and what nobody checked: repeat the items in the script's `not checked` line that apply, without explaining them away. Do not call a circuit safe or verified beyond that.

| The script stops the page (`ERROR:`) | The script warns (`warning:`): resolve it or tell the user | Only you can check |
|---|---|---|
| Supply shorted to GND or to another voltage, also when a button is pressed; 5 V on a 3.3 V pin; LED with no resistor, backwards, over its limit or joining a higher voltage to a pin; pin over its limit; both legs on one net; reversed module or electrolytic; module over its `vcc` or `io_max`; flash pins; a board or module with no voltage facts, or a pin or leg named like a supply with no voltage given; a pin, leg or hole that does not exist | Module output level unknown; pull-up above the pin's level; pin over its working level; pin tied straight to a supply; strapping or USB serial pins; supplies of two boards joined | That `vcc`, `out_v`, pin orders and other facts in the spec match the datasheet; flyback diodes on motors and relays; a servo or motor on the board's 5 V pin; coil buzzers; total current against the supply; modules whose pin order differs from the printing; split rails; what the firmware drives |

The script only knows what the spec says: its result is as good as the facts you give it.

## Steps

1. **Know the board.** Read the project's notes (its CLAUDE.md or AGENTS.md, your memory, the progress file). If the breadboard's size, which end number 1 is at, which letter is nearest the user, the rails, or where the other board sits is not written anywhere, ask once and record the answer there. Then find the electrical facts for each board and module, as in "Safety".
2. **Write a spec and run [breadboard.py](breadboard.py).** List the parts and what connects to what; the script picks every hole, adds the wires, writes the steps and the table, draws the page, and checks it. One request gets one page with everything the user asked for. See "The spec".
   `python3 <this skill>/breadboard.py spec.json page.html`
   It prints every net, what it checked and did not check, then any `warning:` and `ERROR:`. An error means no page: fix the circuit, and if the fix is not yours to choose, ask. If it says a part has no room, take out what does not fit and say in chat what would fit the rest (a bigger breadboard); never drop a resistor to make room. Read the nets once against the circuit you meant.
3. **Damage warnings.** Go through the last column of the table in "Safety", and check pins against the board's file in [boards/](boards/). Add a `notes` entry, in the page's language, only for what can still damage a part: each warning that stands and each risk you found (for an LED, aim for 5–15 mA on a 5 V Arduino, a few mA on a Pico).
4. **Look once.** One desktop screenshot of the page (headless Chrome is fine). If a label hides something, move a part or reorder parts and run again.
5. **Publish.** With the Artifact tool: publish (same `url` for a page that is rewritten) and `open` it. Without it: save the HTML where the project keeps such files and give its path.
6. **Progress notes** (see below): add the page and the planned positions, then rebuild the index:
   `python3 <this skill>/render_index.py <progress.md> <index.html> "<project> build log" <lang>`

For soldering spots, probe points, or anything that is not a breadboard, draw by hand with [drawing.md](drawing.md).

## The spec

Start from [spec.example.json](spec.example.json).

- `lang`, `title`, `eyebrow`, `lead`, `notes` (damage warnings, HTML). For a language other than `en` or `ja`, add `words` with every key of `WORDS` in the script translated.
- `board`: `rows` (30 half, 63 full, 17 mini), `row1` (`left`/`right`), `near` (letter nearest the user, `a` or `j`), `rails` (`both`, `far`, `near`, `none`), `outer` (sign of the outer rails, `-` or `+`).
- `boards`: a board plugged into the breadboard (Pico, Nano) has `id`, `label`, `span` [first, last number], `usb` (`left`/`right`, drawn as a port so the user can match the direction) and `pins` {letter: [pin names in number order]}. Both need `model`: `uno-r3`, `nano`, `mega2560`, `pico` or `esp32-devkitc`. For any other board give, from its datasheet, `logic_v`, `power` {pin: volts, `null` for an input such as VIN} and `pin_ma` [working level, limit], using the same pin names. A board beside it has `"kind": "offboard"`, `side` (`far`/`near`), `usb` (`left`/`right`), `jack` (true for a round power jack, as on an Uno) and `headers`, nearest the breadboard first, each with `name`, `at` (the number its first socket lines up with) and `pins` (every socket in order, `""` unlabelled, `null` a gap). Copy pin orders from boards/.
- `parts`: `id` and `kind`: `resistor` (`value`: `220`, `4.7k`), `led` (`color`), `cap` (`polar`), `buzzer`, `diode`, `switch` (4-leg tactile), `dip` (`pins`, short `names`), `pot`, `rgb`, `module`, `part` (`names` of the legs in order).
- Electrical facts on parts: `dip`, `module` or `part` with a supply leg (VCC, VDD, VIN, V, VBAT, 5V and similar) needs `vcc` [min, max]. If its supply leg has another name, list it in `supply`; a `dip` or `module` with no supply leg sets `supply` to `[]`. Add `io_max` if its signal pins take a different maximum than `vcc`, and `out_v` {leg: volts} for what it outputs. An LED may have `vf` and `max_ma` from its datasheet (otherwise Vf is taken low by color). Anything may have `draw_ma`, what it pulls from a pin.
- `connect`: groups of things joined together. A leg is `R1.1`, `R1.2`, `LED1.+`, `LED1.-`, `SW1.1`, `SW1.2`, or a name from `names` (`LED1.K`). A board pin is `uno.5V` or `pico.GP15` (`pico.GND#2` for the second GND; plain `GND` takes the first). `-` and `+` are the rails: put the board's GND pin and every GND leg in the `-` group, and its supply pin in the `+` group.

To draw wiring exactly as the user built it (checking their work), give each part `legs` (holes such as `14f`; rails `F-12`, `N+3`; `[name, hole]` for named legs; `pairs` for a switch; `pin1` for a chip) and `wires` (`n`, `from`, `to`, `color`, `dashed` for a fix) instead of `connect`; the script then only draws and checks. Add `"as_built": true` so a fault in it does not stop the page: the page is written with a do-not-power banner, and the errors are what you report. Dashed wires need `as_built`; the checks read the wiring as it is now and leave dashed wires out, so check that the fix is safe yourself.

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
