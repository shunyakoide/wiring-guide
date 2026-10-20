---
name: wiring-guide
description: Show wiring, breadboard placement, soldering spots and multimeter probe points as an illustrated page, and keep an index of how far the build has come. Use whenever you explain how to wire or assemble something physical ("where does this go", "check my wiring", "which hole", "where do I solder", "where do I probe"), even if the user does not ask for a picture.
---

# Wiring guide

Explain wiring and assembly with **a page that has a drawing**, not with paragraphs in chat. In chat, write one or two lines on what to check and the link.

Write the page and the progress notes in the user's language.

## Steps

0. **Read the progress notes.** Look for the project's progress file (see "Progress notes"). It says what is done and which pages exist. If there is none, make one; when the Artifact tool is available, collect the existing pages with `Artifact` `list`.
1. **Confirm where things really are.** Never treat a plan (soldering plan, schematic, pinout table) as what was actually built. If the real position is not written anywhere, ask before drawing.
2. **Pick the page.** If the project has a page that is rewritten for each check, update it in place; read its current version first. Otherwise make a new page.
3. **Copy [template.html](template.html)** and replace only the content (eyebrow, title, lead, sections). Keep the colors, fonts and dark mode as they are.
4. **Draw the figure as inline SVG** (see "Drawing rules").
5. **Publish and open it.** With the Artifact tool: publish (same `url` for a page that is rewritten), then `open` it. Without it: write the HTML into the project's scratch area and open it in a browser.
6. **Update the progress notes** whenever you publish a page or the user reports a step done ("it lights up", "soldered"). Then rebuild the index page and publish it to the same URL:
   `python3 <this skill>/render_index.py <progress.md> <scratch>/index.html "<project> build log"`

## Drawing rules

- Draw **only what to check now**. Highlight the wires and parts to check with `--hl`; keep the rest faint.
- Show **both ends** of every wire: which board, which hole, inner or outer rail, + or −.
- Draw the breadboard **the way the user has it placed** (ask once, then record it in the project's memory). Label row numbers and column letters on the edges.
- Name pins in a way a person can count by hand ("3rd pin from the USB end"), not coordinates alone.
- For a multimeter, draw which jacks the leads go in, the dial position, and where the red and black probes touch. Use the user's meter model if known.
- Match real wire colors (red = +, black = −). If jumpers are limited, count long/short ones under the table.
- Steps go in `<ol>`, wires in a `.tbl` table. Number each wire the same in the table and the drawing.
- Put irreversible steps (cutting a cable, measuring voltage with the lead in the mA jack) in a `.note`.
- Narrow screens scroll the SVG sideways (`.figure` has `min-width`). No text under 12px.

## Progress notes

One Markdown file per project, **outside the repository** so build notes never end up in its history. Follow the user's own convention if they have one (for example a notes folder named in their CLAUDE.md); otherwise use `~/.wiring-guide/<repo>/progress.md`. Record its path and the index URL in the project's memory.

The file has three `##` sections, in this order. Their headings become the headings of the index page, so write them in the user's language:

1. Now / next: bullet list.
2. Pages: a table `| stage | page | url | status | updated |`. A status starting with done / decided / ✓ is shown green, ref is grey, anything else is orange (in progress).
3. Log: bullet list, newest first.

See [examples/progress.md](../../examples/progress.md).
