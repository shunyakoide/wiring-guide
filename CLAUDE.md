# wiring-guide

A Claude Code plugin with one skill: `skills/wiring-guide/`.

## Layout
- `.claude-plugin/plugin.json`, `marketplace.json`: plugin and marketplace manifests. Bump `version` in plugin.json on each release.
- `skills/wiring-guide/SKILL.md`: the instructions Claude follows. Keep it generic: no personal paths, URLs, board placements or meter models.
- `skills/wiring-guide/LICENSE.txt`: copy of the root LICENSE, so the folder keeps it when used alone. Update both together.
- `skills/wiring-guide/template.html`: page styles (light and dark). `render_index.py` reuses it.
- `skills/wiring-guide/render_index.py`: progress Markdown to index HTML. Python 3 standard library only.
- `skills/wiring-guide/boards/`: pin notes per board. Every fact needs a source link (datasheet or official docs).
- `skills/wiring-guide/sketches/`: small Arduino sketches to try after wiring. Arduino core libraries only.
- `skills/wiring-guide/progress.example.md`: sample progress file.
- README Acknowledgements: credit any idea taken from another project there, in both READMEs.

## Check
```
python3 skills/wiring-guide/render_index.py skills/wiring-guide/progress.example.md /tmp/index.html "Example build log"
```

## Rules
- English in SKILL.md, README.md and code, except Japanese trigger phrases in the description. Japanese prose only in README.ja.md.
- Do not add dependencies.

計画・調査メモはこのリポジトリに置かない(作者の手元の別リポジトリで管理している)。
