# 「BLOOM — 咲け」 — 制作パッケージ

> ⚠️ オリジナル歌詞(既存曲の盗用なし)。情報整理・制作補助であり、再生数を保証するものではない。
> Sunoのスタイル欄・歌詞欄に**コピペでそのまま使える**完成形。日英比率 ≒ **日5:英5**。

## 1. コンセプト
- **狙うジャンル**: エモーショナル・アンセミック・ポップ(静→動/ゴスペル感)。三番手レシピC。
- **テーマ**: 生きづらさ・不器用さの肯定 → 「君は咲く」。**結婚式・卒業・人生の節目**に貼り付くアンセム。
- **ターゲット/バズ仮説**: 「Golden」「Ordinary」「晩餐歌」型。コメント最頻の**「エモい/泣ける」**を直撃。frisson(鳥肌)設計で**保存・シェア・ロングテール**を狙う。

## 2. スペック
- **BPM**: 88(サビでビート増)/ **キー**: マイナー(バース)→ メジャー解放(サビ)・推定 / **尺**: フル 3:20
- **言語比率**: 日5 : 英5 / **フォーマット**: フル(節目ソング)+ Shorts(サビの泣ける20秒)

## 3. スタイルプロンプト(コピペ用)

**▼ フル尺用(Suno スタイル欄)**
```
emotional anthemic pop ballad, 88 BPM, quiet-to-powerful female vocal, intimate piano building into full band with gospel-tinged harmonies and warm strings, soft verse exploding into a soaring belted chorus, cinematic and uplifting, wide warm mix, short piano intro
```

**▼ Shorts用(サビの climax 切り取り)**
```
emotional pop anthem, soaring belted female chorus with gospel harmonies, quiet-to-loud dynamic lift, tear-jerking climax, cinematic strings, powerful 20-second moment
```

## 4. 歌詞(構造タグ入り・コピペ用)
```
[Intro]

[Verse 1]
枯れたと思った 心の隅で
小さな芽が ふるえて待ってた
誰にも言えない 夜の涙が
明日の根っこに なるなんてね

[Pre-Chorus]
顔を上げて ほら
風が 君を呼んでる

[Chorus]
You're gonna bloom, bloom, bloom
どんな冬も 超えて
You're gonna shine through the rain
君は咲く その色で

[Verse 2]
比べなくていい 誰かの花と
咲く季節は みんな違うから
遅くてもいい 不器用でもいい
君のままで 空を見上げて

[Pre-Chorus]
震える手のひら
ひとりじゃないよ さあ

[Chorus]
You're gonna bloom, bloom, bloom
どんな冬も 超えて
You're gonna shine through the rain
君は咲く その色で

[Bridge]
Even if you fall, even if you break,
every scar is part of the bloom you'll make.
Hold my hand, we'll find the light —
you were never meant to hide.

[Chorus]
You're gonna bloom, bloom, bloom
涙の数 抱いて
You're gonna shine through the rain
君は咲く 誇らしく

[Outro]
咲け 君のままで
```

## 5. バイラル設計
- **Shorts切り取り**: サビの climax "You're gonna bloom... / 君は咲く" を20秒で。静→動の落差を頭に凝縮した別カットも作る。
- **保存トリガー**: 結婚式・卒業・「頑張る友達へ」など**用途**が想像できる歌詞→ プレイリスト保存・贈る共有。
- **frisson設計**: Pre-Chorusの溜め → サビでハモり+高音解放 + ビート増。鳥肌コメントを狙う。
- **フル構成**: 静かな1番→2番で要素追加→ブリッジで一旦落とす→ラストサビ最大化。コメントCTA「誰に届けたい?」。

## 6. レッドチームの指摘と対応
- **お涙頂戴・説教臭(萎え要因)**: 直球の応援歌は寒くなりやすい。→ 抽象論を避け、具体(夜の涙/震える手/枯れた芽)で見せる。「君は咲く」を断定しすぎず情景で支える。
- **既視感(Golden/Ordinary 量産フォロワー)**: → 日本語の繊細な比喩で差別化。英語サビは普遍フレーズに留め、物語は日本語側に持たせる。
- **AI slop 批判**: 感情系はAI感が一番嫌われる領域。→ 歌詞の具体性と、ボーカルの"溜め/かすれ"指定で人間味を出す。生成後に手を入れる前提。
- **炎上地雷**: なし(普遍テーマ)。ただし"頑張れ"の押し付けに読ませない。

## 7. 確信度と反証条件
- **確信度: 中**。コメント最頻の「泣ける」を直撃する反面、**差別化が最難関**(類似曲が多い)。
- **滑るとしたら**: ①既視感を超えられず埋もれる ②サビが凡庸で鳥肌が出ない ③Suno生成が感情の起伏を出せず平坦。→ 保存率・フル視聴維持率・「泣いた/鳥肌」コメント比率で検証。

## 8. 生成のコツ(この曲固有)
- 静→動の落差が命。スタイルに "soft verse exploding into soaring chorus" を明記し、サビは `[Chorus: belted, full band, gospel harmonies]` 指定。
- バラードは Suno が間延びしがち→ 尺を欲張らず、3〜5テイクで"サビの鳥肌"が出た版を採用。
- 日本語の伸ばす母音(咲け/超えて)を活かす。崩れたら別ボイス試行。
