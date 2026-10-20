# wiring-guide

[English](README.md)

電子工作のための Claude Code の skill です。「この線はどこへ」「どの穴に挿す」「どこをハンダ付けする」「テスターでどこを測る」と聞くと、穴の番号を並べた文章ではなく、絵の入ったページで答えます。作ったページの一覧と、どこまで進んだかを目次のページにまとめます。

## 入れ方

```
/plugin marketplace add shunyakoide/wiring-guide
/plugin install wiring-guide@wiring-guide
```

または `skills/wiring-guide/` を `~/.claude/skills/` にコピーします。

## 使い方

いつもどおり組み立ての話をすれば（「LED の抵抗はどこ？」「エンコーダの配線を確認して」）、skill が自分で動きます。

- 1 枚のページには、今確かめる所だけを描きます。線の両端を描き、線の表と同じ番号を振ります。
- 進み具合はリポジトリの外の Markdown 1 つに書きます（既定は `~/.wiring-guide/<repo>/progress.md`）。見本は [examples/progress.md](examples/progress.md)。見出しは日本語でも構いません。
- `render_index.py` がその Markdown から目次のページを作ります。Python 3 だけで動きます。

Artifact の機能があるときはアーティファクトで出し、無いときはローカルの HTML に書きます。

## 参考にしたもの

skill の確認項目の一部は、MIT ライセンスの次の skill を参考にしました。文章はそのまま写さずに書き直し、ボードの情報は `boards/` の各ファイルに載せたデータシートで確かめています。

- [embedded-engineering-skills](https://github.com/wedsamuel1230/embedded-engineering-skills)（Samuel F.、MIT、© 2026 Samuel F.）
  - [circuit-debugger](https://github.com/wedsamuel1230/embedded-engineering-skills/tree/main/skills/circuit-debugger): 測る順番（電源を切って測り、そのあと入れて測る）、電圧の目安、ブレッドボードのよくある間違い、配線のあとに試すスケッチ
  - [wiring-safety-check](https://github.com/wedsamuel1230/embedded-engineering-skills/tree/main/skills/wiring-safety-check): 描く前に回路を確かめること
  - [board-support](https://github.com/wedsamuel1230/embedded-engineering-skills/tree/main/skills/board-support): ボードごとのピンの注意と、事実ごとに出典を付ける書き方
  - [embedded-project-loop](https://github.com/wedsamuel1230/embedded-engineering-skills/tree/main/skills/embedded-project-loop): 1 回に 1 手ずつ、期待する結果と一緒に進めること
- github/awesome-copilot の [legacy-circuit-mockups](https://github.com/github/awesome-copilot/tree/main/skills/legacy-circuit-mockups)（MIT、© GitHub, Inc.）: 途中で切れている電源レール、信号線の色

## ライセンス

[MIT](LICENSE)
