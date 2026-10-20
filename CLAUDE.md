# wiring-guide

A Claude Code plugin with one skill: `skills/wiring-guide/`.

## Layout
- `.claude-plugin/plugin.json`, `marketplace.json`: plugin and marketplace manifests. Bump `version` in plugin.json on each release.
- `skills/wiring-guide/SKILL.md`: the instructions Claude follows. Keep it generic: no personal paths, URLs, board placements or meter models.
- `skills/wiring-guide/template.html`: page styles (light and dark). `render_index.py` reuses it.
- `skills/wiring-guide/render_index.py`: progress Markdown to index HTML. Python 3 standard library only.
- `examples/progress.md`: sample progress file.

## Check
```
python3 skills/wiring-guide/render_index.py examples/progress.md /tmp/index.html "Example build log"
```

## Rules
- English in SKILL.md, README.md and code, except Japanese trigger phrases in the description. Japanese prose only in README.ja.md.
- Do not add dependencies.

計画・調査メモはこのリポジトリに置かない(作者の手元の別リポジトリで管理している)。
