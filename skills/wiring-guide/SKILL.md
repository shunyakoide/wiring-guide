---
name: wiring-guide
description: Show wiring, breadboard placement, soldering spots and multimeter probe points as an illustrated page, and keep an index of how far the build has come. Use whenever you explain how to wire or assemble something physical ("where does this go", "check my wiring", "which hole", "where do I solder", "where do I probe"), even if the user does not ask for a picture (also 「どこに挿す」「配線を確認」「どこをハンダ付け」「テスターでどこを測る」). Do not use for schematic or PCB layout design, or for firmware-only questions.
---

# Wiring guide

Explain wiring and assembly with **a page that has a drawing**, not with paragraphs in chat. In chat, write one or two lines on what to check and the link.

Write the page and the progress notes in the user's language.

## Steps

0. **Read the progress notes.** Look for the project's progress file (see "Progress notes"). It says what is done and which pages exist. If there is none, make one; when the Artifact tool is available, collect the existing pages with `Artifact` `list`.
1. **Confirm where things really are.** When checking existing wiring, never treat a plan (soldering plan, schematic, pinout table) as what was actually built; if the real position is not written anywhere, ask before drawing. When the user asks where to put things, choose the positions yourself. Breadboards differ, so before the first drawing ask about the user's board (or read it from the project's memory) and record the answers there:
   - Size: rows per side (mini 17, half 30, full 63 are common) and whether it has power rails at all. Every hole you name must exist on that board.
   - Labels: which end row 1 is at, and which side column a is on. Some boards print them the other way round.
   - Holes per strip (5 on most boards; count them if the board looks different) and whether the rails are split in the middle.
   - Which rail is + (the red line) and which is − (the blue line), on each side.
   For a value the user did not give (LED color, supply voltage), assume the common one, say so on the page, and give the numbers for the other cases too.
2. **Pick the page.** If the project has a page that is rewritten for each check, update it in place; read its current version first. Otherwise make a new page.
3. **Copy [template.html](template.html)** and replace only the content (eyebrow, title, lead, sections). Keep the colors, fonts and dark mode as they are.
4. **Check the circuit before drawing it.** Put anything that can damage a part or the meter in a `.note`, and nothing else: a 5 V signal into a 3.3 V pin, an LED without a current-limiting resistor (R = (Vsupply − Vf) / I; aim for 5–10 mA), a motor or relay coil without a flyback diode, an output that switches something on at power-up. Pin restrictions of the board (input-only, boot strapping, flash pins) go here too. Read the board's file in [boards/](boards/) when there is one (Arduino Uno/Nano/Mega, ESP32, Raspberry Pi Pico) and check the source it links; for other boards, use the datasheet, not memory.
5. **Draw the figure as inline SVG** (see "Drawing rules").
6. **Look at it before handing it over.** Render the page at desktop and phone width, in light and dark, and fix overlapping labels. Headless screenshots can clip narrow pages; measure in a real browser before changing the layout.
7. **Publish and open it.** With the Artifact tool: publish (same `url` for a page that is rewritten), then `open` it. Without it: write the HTML into the project's scratch area and open it in a browser.
8. **Update the progress notes** whenever you publish a page or the user reports a step done ("it lights up", "soldered"). Then rebuild the index page and publish it to the same URL:
   `python3 <this skill>/render_index.py <progress.md> <scratch>/index.html "<project> build log"`

## Drawing rules

- Draw **only what to check now**. Highlight the wires and parts to check with `--hl`; keep the rest faint.
- Show **both ends** of every wire: which board, which hole, inner or outer rail, + or −.
- Draw the other boards (Arduino, Pico, a module) as a simple outline with only the pins used labelled, rotated so the headers face the breadboard. Say on the drawing which way it is rotated.
- Draw the breadboard **the way the user has it placed and at its real size** (ask once, then record it in the project's memory): the same number of rows, the rails it has, and its own numbering. If the drawing shows only part of the board, say which rows it shows. Label row numbers and column letters on the edges.
- Name pins in a way a person can count by hand ("3rd pin from the USB end"), not coordinates alone.
- For a multimeter, draw which jacks the leads go in, the dial position, and where the red and black probes touch. Use the user's meter model if known.
- **Mark the usual mistakes on the drawing** where they apply, with `--hl` on the holes concerned: both legs of a part in the same 5-hole strip, a rail that is split in the middle, LED orientation (long leg = +, flat edge = −), I2C without pull-ups, an input pin left floating.
- Match real wire colors. If the user has no habit of their own: red = + supply, black = GND, green = data, yellow = clock, orange = control. If jumpers are limited, count long/short ones under the table.
- Steps go in `<ol>`, wires and parts in one `.tbl` table. Number wires 1, 2, … and name parts R1, LED1, …, the same in the table and the drawing.
- Keep the labels that matter in the left part of the figure: on a phone the SVG scrolls sideways and the right side starts hidden.
- Draw black wires dark with a light outline, so they still read as black in dark mode.
- Narrow screens scroll the SVG sideways (`.figure` has `min-width`). No text under 12px.

## Measuring

Put the steps in this order in an `<ol>`, and give each reading an expected value in the table.

1. **Power off.** Continuity and resistance only. Between VCC and GND: if it beeps, there is a short. Stop and find it before powering up.
2. **Power on.** Voltages, black probe on GND.
3. Typical expected values: USB 5 V rail 4.75–5.25 V, 3.3 V rail 3.2–3.4 V, LED forward voltage red 1.8–2.2 V, white or blue 3.0–3.4 V. A diode reads as a voltage (about 0.6 V for silicon) in diode mode; most meters do not beep on it.

Measure resistance with the part out of the circuit when you can; parallel paths on the board change the reading.

## Trying it

End a wiring page with one sketch to run and what it should show, so the user can tell the wiring works:

- An LED: the IDE's built-in Blink (File → Examples → 01.Basics → Blink), with the pin changed if it is not the on-board LED's. Expected: on and off once a second.
- An I2C part: [sketches/i2c_scan/i2c_scan.ino](sketches/i2c_scan/i2c_scan.ino). Expected: the address from the part's datasheet (an SSD1306 OLED is usually 0x3C). "no I2C device" means check SDA/SCL, power, GND and pull-ups.

Do not hand out a sketch that drives pins as outputs unless the page shows nothing else is wired to them.

## Progress notes

One Markdown file per project, **outside the repository** so build notes never end up in its history. Follow the user's own convention if they have one (for example a notes folder named in their CLAUDE.md); otherwise use `~/.wiring-guide/<repo>/progress.md`. Record its path and the index URL in the project's memory.

The file has three `##` sections, in this order. Their headings become the headings of the index page, so write them in the user's language:

1. Now / next: bullet list. Write the next single step and what the user should see when it works ("LED blinks once a second"). Change one wire at a time between checks. Record a step as done only when the user has reported it.
2. Pages: a table `| stage | page | url | status | updated |`. A status starting with done / decided / ✓ is shown green, ref is grey, anything else is orange (in progress).
3. Log: bullet list, newest first.

See [examples/progress.md](../../examples/progress.md).
