# wiring-guide

[English](README.md)

電子工作のための Claude Code の skill です。「この線はどこへ」「どの穴に挿す」「どこをハンダ付けする」「テスターでどこを測る」と聞くと、穴の番号を並べた文章ではなく、絵の入ったページで答えます。作ったページの一覧と、どこまで進んだかを目次のページにまとめます。

## 入れ方

```
/plugin marketplace add shunyagithub/wiring-guide
/plugin install wiring-guide@wiring-guide
```

または `skills/wiring-guide/` を `~/.claude/skills/` にコピーします。

## 使い方

いつもどおり組み立ての話をすれば（「LED の抵抗はどこ？」「エンコーダの配線を確認して」）、skill が自分で動きます。

- 1 枚のページには、今確かめる所だけを描きます。線の両端を描き、線の表と同じ番号を振ります。
- 進み具合はリポジトリの外の Markdown 1 つに書きます（既定は `~/.wiring-guide/<repo>/progress.md`）。見本は [examples/progress.md](examples/progress.md)。見出しは日本語でも構いません。
- `render_index.py` がその Markdown から目次のページを作ります。Python 3 だけで動きます。

Artifact の機能があるときはアーティファクトで出し、無いときはローカルの HTML に書きます。

## ライセンス

[MIT](LICENSE)
