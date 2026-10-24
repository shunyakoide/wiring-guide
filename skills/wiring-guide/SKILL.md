---
name: wiring-guide
description: Show wiring, breadboard placement, soldering spots and multimeter probe points as an illustrated page, and keep an index of how far the build has come. Use whenever you explain how to wire or assemble something physical ("where does this go", "check my wiring", "which hole", "where do I solder", "where do I probe"), even if the user does not ask for a picture (also 「どこに挿す」「配線を確認」「どこをハンダ付け」「テスターでどこを測る」). Do not use for schematic or PCB layout design, or for firmware-only questions.
license: MIT. Complete terms in LICENSE.txt
---

# Wiring guide

Explain wiring and assembly with **a page that has a drawing**, not with paragraphs in chat. In chat, write one or two lines on what to check and the link, then a short list of what you assumed without asking, then the sketch to try (see "Trying it"). Keep the page compact and visual, about how to wire only: the drawing, steps, table and warnings, with no sections of assumptions, code or troubleshooting.

Write the page and the progress notes in the user's language.

## Steps

0. **Read the progress notes.** Look for the project's progress file (see "Progress notes"). It says what is done and which pages exist. If there is none, make one; when the Artifact tool is available, collect the existing pages with `Artifact` `list`.
1. **Confirm where things really are.** When checking existing wiring, never treat a plan (soldering plan, schematic, pinout table) as what was actually built; if the real position is not written anywhere, ask before drawing. When the user asks where to put things, choose the positions yourself. Breadboards differ, so before the first drawing ask about the user's board (or read it from where you keep notes for this project: your memory, the project's CLAUDE.md or AGENTS.md, or the progress notes) and record the answers there:
   - Size: rows per side (mini 17, half 30, full 63 are common) and whether it has power rails at all. Every hole you name must exist on that board.
   - Labels: which end row 1 is at, and which side column a is on. Some boards print them the other way round.
   - Holes per strip (5 on most boards; count them if the board looks different), whether the rails are split in the middle, and whether a rail skips a hole every few rows.
   - For a board that straddles the centre gap (Nano, Pico): which rows its pins are in and which column letter each pin row sits in, since that decides which holes are left free.
   - Which rail is + (the red line) and which is − (the blue line), on each side.
   - How it sits: which long edge faces the user, and where the other board (Arduino, Pico) sits next to it.
   For a value the user did not give (LED color, supply voltage), assume the common one, list it in chat with the numbers for the other cases, and ask the user to say if it differs.
2. **Pick the page.** If the project has a page that is rewritten for each check, update it in place; read its current version first. Otherwise make a new page.
3. **Copy [template.html](template.html)** and replace only the content (eyebrow, title, lead, sections). Keep the colors, fonts and dark mode as they are.
4. **Check the circuit before drawing it.** Put anything that can damage a part or the meter in a `.note`, and nothing else (a page with nothing of that kind has no `.note`): a 5 V signal into a 3.3 V pin, an LED without a current-limiting resistor (R = (Vsupply − Vf) / I; stay within the pin's limit in the board's file: 5–15 mA on a 5 V Arduino, a few mA on a Pico; more than that is a note), a motor or relay coil without a flyback diode, a servo or motor powered from the board's 5 V pin (USB gives about 500 mA in total; a separate supply needs its ground joined to the board's), a "buzzer" that is a magnetic coil (tens of ohms) driven straight from a pin, an output that switches something on at power-up. Modules with the same chip differ in pin order (some SSD1306 OLED boards swap VCC and GND): go by the printing on the user's module and say so on the page. Pin restrictions of the board (input-only, boot strapping, flash pins) go here too. Read the board's file in [boards/](boards/) when there is one (Arduino Uno/Nano/Mega, ESP32, Raspberry Pi Pico) and check the source it links; for other boards, use the datasheet, not memory.
5. **Draw the figure as inline SVG** (see "Drawing rules").
6. **Look at it before handing it over.** Render the page at desktop and phone width, in light and dark, and fix overlapping labels. Set `data-theme="light"` or `"dark"` on `<html>` in a copy to force a theme. Headless Chrome does not lay out narrower than about 500px, so its phone screenshots look clipped: check phone width in a real browser, or measure that `document.documentElement.scrollWidth` is not wider than the window.
7. **Publish and open it.** With the Artifact tool: publish (same `url` for a page that is rewritten), then `open` it. Without it: write the HTML where the project keeps such files (its scratch area if it names none), open it in a browser, and put the file's path in the progress table's `url` column.
8. **Update the progress notes** whenever you publish a page or the user reports a step done ("it lights up", "soldered"). Then rebuild the index page and publish it to the same URL:
   `python3 <this skill>/render_index.py <progress.md> <scratch>/index.html "<project> build log" <lang>` (lang as in `<html lang>`, such as `ja`; default `en`)

## Drawing rules

- Draw **only what to check now**. On a page without `data-step`, highlight the wires and parts to check with `--hl` and keep the rest faint; when everything on it is new, draw it all at normal weight and keep `--hl` for the mistake spots. On a stepped page, `--hl` marks mistake spots only (see "When a page has several steps").
- **On a step that adds to earlier ones**, show what is already on the board so the user can find their place: draw it faint (about 40% opacity) at the holes recorded in the progress notes, with both ends of every wire, and never move it. Draw this step's parts and wires at full strength, ring their holes with `--hl`, and highlight their row numbers. (This is for a page per step; on a page stepped with `data-step`, see below.) In the table, list this step's rows first, then the earlier ones faint, marked as already in.
- Show **both ends** of every wire: which board, which hole, inner or outer rail, + or −.
- Draw the other boards (Arduino, Pico, a module) as a simple outline with only the pins used labelled, rotated so the header with the most used pins faces the breadboard. Say on the drawing which way it is rotated. They need not be to scale, but their pins must stay countable: draw every position of a header, unlabelled ones too, and before handing the page over, count each used pin's position in the SVG against the board's file (a wire one pin off still looks right).
- Draw the breadboard **the way the user has it placed and at its real size** (ask once, then record it where you keep notes for this project: your memory, or the project's instructions file such as CLAUDE.md or AGENTS.md): the same number of rows, the rails it has, and its own numbering. If the drawing shows only part of the board, say which rows it shows. Label row numbers and column letters on the edges.
- Name holes as number + letter (14f) and say once on the page which is which; words like row and column (行・列) are read both ways, so do not use them for holes at all: say "number 14, letter f", and in other languages the words for number and letter. Name a rail hole by the numbered row it lines up with. Many rails have a gap after every 5 holes: if you know where the gaps are and no rail hole lines up with that row, use the next one and say so; if you do not know, draw a hole at every row and tell the user to use the next hole on the same rail half if one is missing.
- Name pins in a way a person can count by hand ("3rd pin from the USB end"), not coordinates alone.
- For a multimeter, draw which jacks the leads go in, the dial position, and where the red and black probes touch. Use the user's meter model if known.
- **Mark the usual mistakes on the drawing** where they apply, with `--hl` on the holes concerned: both legs of a part in the same 5-hole strip, a rail that is split in the middle, LED orientation (long leg = +, flat edge = −), I2C without pull-ups, an input pin left floating, a 4-leg tactile switch turned 90° (always closed), a potentiometer's middle leg (wiper) on a supply rail, an electrolytic capacitor's striped leg (−) on +. On a stepped page, put each ring inside the step that places that part.
- Draw a resistor as its body (`--res`) with its color bands (`--b0`…`--b9`, `--b-gold`, `--b-silver`), the tolerance band set apart at one end. Color names alone are hard to match, so for each resistor value on the page add a close-up figure: the resistor drawn large, each band led out to its meaning (digit, digit, multiplier, tolerance), the reading direction, and the sum (3 3 × 10 = 330 Ω). In the table, show a small picture of the bands next to the value instead of color names.
- Leave at least 3 holes between the legs of a 1/4 W resistor (4 is easier to bend), and keep other parts off the holes a standing part covers (a capacitor's body, a big module such as an HC-SR04).
- Match real wire colors, with the wire tokens in the template. If the user has no habit of their own: red = + supply (`--red`), black = GND (`--w-blk`), green = data (`--w-grn`), yellow = clock (`--w-yel`), orange = control (`--w-org`), blue = other signals (`--w-blu`). If jumpers are limited, count long/short ones under the table.
- **When a page has several steps** (more than two or three wires to place), give each step's SVG group, `<li>` and table row the same `data-step="n"`. The template then adds ‹ › buttons (and the arrow keys). The page opens on "All"; stepping through, earlier steps fade, the current one is highlighted, later ones hide, and "All" shows everything. The drawing also glides in on the current step's parts, and that step's `<li>` text appears right under the drawing, so write each `<li>` to stand on its own and keep each step's SVG group to what that step places. Translate the `UI` labels at the top of the template's script, the `<html lang>` and the `<title>` into the page's language. On a stepped page the stepper does the highlighting (the current step glows), so draw holes and wires in their normal colors and keep `--hl` for the mistake spots only; otherwise "All" turns every hole orange. Put the other board's pin labels inside the step that first uses that pin. One step = what the user places before looking back at the page, usually one part or one wire.
- Steps go in `<ol>`, wires and parts in one `.tbl` table. Number wires 1, 2, … and name parts R1, LED1, …, the same in the table and the drawing. Keep the numbers across steps: a new wire takes the next number after the highest one used so far, even if a lower number is missing. Wire numbers and step numbers differ (placing a part is a step too): the `<ol>` numbers the steps, so in a step write "wire 3" and use the `.step` badge in the table only. A step that places nothing (unplug USB, a continuity check) goes before the stepped ones without `data-step`.
- Keep the labels that matter in the left part of the figure as drawn: on a phone the SVG scrolls sideways and the right side starts hidden.
- Draw black wires with `--w-blk` over a slightly wider `--w-edge` stroke, so they still read as black in dark mode. Wire tokens do not change with the theme; `--blk` does, so do not use it for wires.
- Size the SVG with its viewBox only: the template's script pins it to the viewBox width, so 12px text stays 12px and narrow screens scroll it sideways. Make the viewBox as wide as the board needs (a 63-row board is about 1140 wide). Keep the template's zoom script: it adds −, Fit, 100%, + buttons above each figure, and Ctrl/⌘ + wheel or a pinch zooms. No text under 12px. A long board that does not fit may be drawn in part (see above).
- A board or module with male pins (Nano, Pico, ESP32 DevKit, most sensor modules) that sits outside the breadboard needs female–male jumpers; count them separately from male–male ones. An Uno or Mega has female headers and takes male–male.
- When the user has fixed where the other board sits and its pins are on both headers, keep their placement, choose pins on the header nearer the breadboard where the function allows, and route the rest over the board with a label at each end.
- A 4-leg tactile switch: the two legs about 6.5 mm apart are always connected inside. Put that pair across the centre gap; the switched pair then lies along the row.
- A module that stands in the breadboard covers the holes under its board. Put its pins in column f (or e) facing the user and run its wires from the free holes behind it.
- **Diagnosing the user's wiring**: draw it as it is now with solid lines, the fix as a dashed line with an arrow to the new hole, and ring the fault with `--hl`. Put the checks that confirm the fault (power off) before the fix, and the checks that confirm it works (power on) after.
- Do not step a measuring page with `data-step`; show each probe position with its measurement number in the drawing and the table.

## Measuring

Put the steps in this order in an `<ol>`, and give each reading an expected value in the table.

1. **Power off.** Continuity and resistance only. Between VCC and GND: if it beeps, there is a short. Stop and find it before powering up.
2. **Power on.** Voltages, black probe on GND.
3. Typical expected values: USB 5 V rail 4.75–5.25 V, 3.3 V rail 3.2–3.4 V, LED forward voltage red 1.8–2.2 V, white or blue 3.0–3.4 V. A diode reads as a voltage (about 0.6 V for silicon) in diode mode; most meters do not beep on it.

Measure resistance with the part out of the circuit when you can; parallel paths on the board change the reading.

## Trying it

The page shows how to wire; the sketch goes in chat. After the link, give a sketch to run, what it should show and where to look if it does not, so the user can tell the wiring works. With several parts, one sketch may test them all; say what each part should do:

- An LED: the IDE's built-in Blink (File → Examples → 01.Basics → Blink), with the pin changed if it is not the on-board LED's. Expected: on and off once a second.
- A button: check `boards/` first (some pins have no internal pull-up, such as ESP32 GPIO34–39; use an external resistor and `INPUT`). Otherwise `pinMode(pin, INPUT_PULLUP)` and print `digitalRead(pin)`, or light the LED while it is pressed. Expected: 1 released, 0 pressed.
- An I2C part: [sketches/i2c_scan/i2c_scan.ino](sketches/i2c_scan/i2c_scan.ino). Expected: the address from the part's datasheet (an SSD1306 OLED is usually 0x3C). "no I2C device" means check SDA/SCL, power, GND and pull-ups.
- Anything else (a potentiometer, a light sensor, a servo, a distance sensor): print the raw reading, or sweep the output slowly, and give the range to expect at each end ("0 turned fully left, 1023 fully right").

Do not hand out a sketch that drives pins as outputs unless the page shows nothing else is wired to them.

## Progress notes

One Markdown file per project, **outside the repository** so build notes never end up in its history. Follow the user's own convention if they have one (for example a notes folder named in their CLAUDE.md or AGENTS.md); otherwise use `~/.wiring-guide/<repo>/progress.md`. Record its path and the index URL in the same place you keep the board placement.

The file has three `##` sections, in this order. Their headings become the headings of the index page, so write them in the user's language:

1. Now / next: bullet list. Write the next single step and what the user should see when it works ("LED blinks once a second"). Change one wire at a time between checks. Record a step as done only when the user has reported it. When a page plans positions, add them as "planned, not yet placed"; when the user reports the step done, change them to what it put on the board: each wire with its number, both ends and color, and each part pin with its hole, one top-level bullet each (the index shows no nested bullets). Later pages draw the board from this record.
2. Pages: a table `| stage | page | url | status | updated |`. A status starting with done / decided / ✓ is shown green, ref is grey, anything else is orange (in progress).
3. Log: bullet list, newest first.

See [progress.example.md](progress.example.md).
