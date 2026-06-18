# 「MESS — ちゃんとしてなくて何が悪い」 — 制作パッケージ

> ⚠️ オリジナル歌詞(既存曲の盗用なし)。情報整理・制作補助であり、再生数を保証するものではない。
> Sunoのスタイル欄・歌詞欄に**コピペでそのまま使える**完成形。日英比率 ≒ **日5:英5**。

## 1. コンセプト
- **狙うジャンル**: J-POP × ジャージークラブ(アニメOP的疾走感)。本命レシピA。
- **テーマ**: **自己肯定**(=日本バズの最大公約数)。「痛み・弱さの肯定」と「前向き宣言」の両極を1曲に。完璧を演じて疲れた人へ。
- **ターゲット/バズ仮説**: 世界は**英語チャント("I'm a mess, but I'm the best")で合唱・ダンス**、日本は**問いかけ型の決め台詞「ちゃんとしてなくて何が悪い」で共感**。コードスイッチ型(VIRAL_PLAYBOOK §4-#4)で越境を狙う。

## 2. スペック
- **BPM**: 150(体感ハーフタイム75)/ **キー**: F# minor(推定)/ **尺**: フル 2:50 / Shorts 0–20秒
- **言語比率**: 日5 : 英5(セクション単位で切替)/ **フォーマット**: Shorts起点 → フル

## 3. スタイルプロンプト(コピペ用)

**▼ フル尺用(Suno スタイル欄)**
```
J-pop crossed with jersey club, 150 BPM with a half-time bounce, energetic female lead with gang-vocal chants, sparse 808 bass, bed-squeak kicks, bright Showa-retro synth stabs, anthemic and defiant, polished modern mix, catchy chantable hook in the first 5 seconds, no long intro
```

**▼ Shorts用(15〜20秒の切り取り生成)**
```
J-pop jersey club anthem, 150 BPM half-time, explosive female chant hook, punchy 808 bounce, bright synth stabs, defiant and addictive, seamless 15-second loop, starts on the hook, no intro
```

## 4. 歌詞(構造タグ入り・コピペ用)
```
[Intro]
Mess, mess — I'm a mess, but I'm the best!

[Verse 1]
鏡の前で 完璧を演じて
笑顔のメッキ もう剥がれかけてる
「ちゃんとしなさい」の 声に溺れて
息ができないまま 朝が来る

[Pre-Chorus]
もういいや 全部さらけ出して
傷も連れて 飛ぶよ

[Chorus]
I'm a mess, but I'm the best
転んだ数が わたしの勲章
Louder, louder, say it loud
ちゃんとしてなくて 何が悪い

[Verse 2]
タイムラインの海で 比べて沈んで
「いいね」の数に 値踏みされて
でも わたしの価値 誰が決めんの
鳴らすの 不協和音のままで

[Pre-Chorus]
怖くたって いい さあ
心の音 上げて

[Chorus]
I'm a mess, but I'm the best
転んだ数が わたしの勲章
Louder, louder, say it loud
ちゃんとしてなくて 何が悪い

[Bridge]
When the lights go down and the world feels loud,
I'll be my own, I'll be loud and proud.
No more hiding, no more lies —
this is me, and I'm alive.

[Chorus]
I'm a mess, but I'm the best
転んだ数が わたしの勲章
Louder, louder, say it loud
これでいいんだ 何が悪い

[Outro]
Mess, mess — I'm a mess, but I'm the best!
```

## 5. バイラル設計
- **Shorts切り取り**: 0秒の `[Intro - Chant]` → サビ頭まで(約15〜20秒)。"I'm a mess, but I'm the best" を冒頭3秒に置きスクロール停止。
- **UGC化**: チャント部で手を上げる/胸を叩く簡単な振り。「#何が悪いチャレンジ」(自分の"不完全"を見せる)で参加型に。
- **フル構成**: 三分割(即チャント→2番で展開→ラストサビで最大化)。2番は歌詞を変え"使い回し感"を回避。
- **リリース**: タイトル/サムネA/Bテスト3案(「ちゃんとしてなくて何が悪い」/「I'm a mess but I'm the best」/顔アップ版)。コメントCTA「あなたの"mess"は?」。

## 6. レッドチームの指摘と対応
- **既視感(BBBBの劣化コピー化リスク)**: ジャージークラブ+アニメ感は擦られ気味。→ **自己肯定の"問いかけ型"日本語パンチライン**と昭和レトロ・シンセで差別化。チャントは破裂音(m/b/s)主体でBBBBと語感を変える。
- **英語が陳腐("but I'm the best"の凡庸さ)**: → サビ内で必ず日本語の決め台詞とセットにし、英語単独で勝負しない。
- **AI slop 批判リスク**: Suno製と分かると評価反転の恐れ。→ 歌詞の手触り(具体情景=鏡/タイムライン)で"人の体温"を出す。量産せず1曲の完成度に振る。
- **炎上地雷**: 自己肯定テーマは安全だが「ちゃんとしてない」を他者攻撃に読ませない(主語は常に"わたし")。

## 7. 確信度と反証条件
- **確信度: 中〜高**。自己肯定×チャント×コードスイッチは実証済みの勝ち筋の掛け合わせ。
- **滑るとしたら(反証条件)**: ①チャントがBBBB/APT.の既視感を超えられず埋もれる ②日本語パンチラインが説教臭く聞こえる ③Suno生成で日英の繋ぎ目の発音が破綻。→ 公開後、頭3秒維持率・サビ合唱コメント・"何が悪い"の引用数で検証。

## 8. 生成のコツ(この曲固有)
- **3〜5テイク**生成して選ぶ。チャントは大文字で強調すると勢いが出やすい。
- 日本語が崩れる場合のみ助詞を発音表記に(例「わたしは」→「わたしわ」)。基本はかな/漢字のままで可。
- サビは `[Chorus: belted female + gang vocals]` のper-section指定を試すと合唱感が増す。
