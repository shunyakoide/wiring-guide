"""Build the index page from a progress file (see SKILL.md, "Progress notes").

Usage: python3 render_index.py <progress.md> <out.html> <page title> [lang]

lang is the page language for <html lang> (default en), e.g. ja.

The file's three ## sections are read by position (now, pages, log), and their
headings are reused on the page, so the notes can be in any language.
"""
import html
import re
import sys
from pathlib import Path

TEMPLATE = Path(__file__).with_name("template.html")
DONE = ("done", "decided", "✓", "済", "決定")
REF = ("ref", "参考")

EXTRA_CSS = """.nowbox { background: var(--hl-soft); border-radius: 10px; padding: 14px 16px; }
.nowbox ul, .log { margin: 0; padding-left: 1.2em; display: grid; gap: 4px; }
.pages { list-style: none; margin: 0; padding: 0; border: 1px solid var(--line); border-radius: 10px; background: var(--surface); }
.pages li { display: flex; flex-wrap: wrap; gap: 4px 12px; align-items: baseline; padding: 10px 12px; border-bottom: 1px solid var(--line); }
.pages li:last-child { border-bottom: 0; }
.pages a { color: var(--fg); font-weight: 500; flex: 1 1 12em; }
.st { font-size: 13px; padding: 0 8px; border-radius: 999px; }
.st.done { color: var(--accent); border: 1px solid var(--accent); }
.st.now { color: var(--hl); border: 1px solid var(--hl); font-weight: 700; }
.st.ref { color: var(--muted); border: 1px solid var(--line); }
.d { font-family: var(--font-mono); font-size: 12px; color: var(--muted); }
.log { color: var(--muted); font-size: 14px; }
</style>"""


def parse(md):
    sections = []
    for line in md.splitlines():
        if line.startswith("## "):
            sections.append((line[3:].strip(), []))
        elif sections and line.strip():
            sections[-1][1].append(line)
    if len(sections) != 3:
        sys.exit(f"expected 3 ## sections (now, pages, log), found {len(sections)}")
    bullets = lambda lines: [l[2:] for l in lines if l.startswith("- ")]
    cells = [[c.strip() for c in l.strip().strip("|").split("|")] for l in sections[1][1] if l.startswith("|")]
    rows = [r for r in cells[2:] if len(r) == 5]  # skip header and --- rows
    return [
        (sections[0][0], bullets(sections[0][1])),
        (sections[1][0], rows),
        (sections[2][0], bullets(sections[2][1])),
    ]


def state_class(state):
    s = state.lower()
    return "done" if s.startswith(DONE) else "ref" if s.startswith(REF) else "now"


def render(md, title, lang="en"):
    (now_h, now), (_, rows), (log_h, log) = parse(md)
    e = html.escape
    groups = {}
    for stage, name, url, state, date in rows:
        groups.setdefault(stage, []).append((name, url, state, date))
    cards = "".join(
        f'<section><h2>{e(stage)}</h2><ul class="pages">'
        + "".join(
            f'<li><a href="{e(url)}" target="_blank" rel="noopener">{e(name)}</a>'
            f'<span class="st {state_class(state)}">{e(state)}</span><span class="d">{e(date)}</span></li>'
            for name, url, state, date in items)
        + "</ul></section>"
        for stage, items in groups.items())
    li = lambda items: "".join(f"<li>{e(i)}</li>" for i in items)
    body = f"""<div class="wrap">
  <header><h1>{e(title)}</h1></header>
  <section class="nowbox"><h2>{e(now_h)}</h2><ul>{li(now)}</ul></section>
  {cards}
  <section><h2>{e(log_h)}</h2><ul class="log">{li(log)}</ul></section>
</div>"""
    page = TEMPLATE.read_text().replace("</style>", EXTRA_CSS, 1)
    page = page.replace('<html lang="en"', f'<html lang="{e(lang)}"', 1)
    page = re.sub(r"<title>.*?</title>", lambda _: f"<title>{e(title)}</title>", page)
    return re.sub(r'<div class="wrap">.*</div>', lambda _: body, page, flags=re.S)


if __name__ == "__main__":
    if len(sys.argv) not in (4, 5):
        sys.exit(__doc__)
    src, out, title, *lang = sys.argv[1:]
    md = Path(src).read_text(encoding="utf-8")
    page = render(md, title, *lang)
    assert '<html lang="' + html.escape(lang[0] if lang else "en") + '"' in page, "lang not set"
    rows = parse(md)[1][1]
    assert rows and all(html.escape(r[2]) in page for r in rows), "a page URL is missing from the output"
    Path(out).write_text(page, encoding="utf-8")
    print(f"{len(rows)} pages -> {out}")
