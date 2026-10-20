# wiring-guide

[日本語](README.ja.md)

A Claude Code skill for hardware builds. When you ask where a wire goes, which hole to use, where to solder or where to probe with a multimeter, Claude answers with an illustrated page instead of paragraphs of hole numbers, and keeps an index page of every guide and how far the build has come.

## Install

```
/plugin marketplace add shunyakoide/wiring-guide
/plugin install wiring-guide@wiring-guide
```

Or copy `skills/wiring-guide/` into `~/.claude/skills/`.

## Usage

Talk about your build as usual ("where does the LED's resistor go?", "check my encoder wiring"). The skill triggers on its own.

- Each guide draws only what to check now, with both ends of every wire, numbered to match a wire table.
- Progress lives in one Markdown file outside your repository (default `~/.wiring-guide/<repo>/progress.md`). See [examples/progress.md](examples/progress.md).
- `render_index.py` turns that file into the index page. It needs only Python 3.

Pages are published with Claude's Artifact tool when it is available; otherwise they are written as local HTML files.

## License

[MIT](LICENSE)
