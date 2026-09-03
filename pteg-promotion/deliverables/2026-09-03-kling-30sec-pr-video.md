# Kling用 30秒PR動画 シナリオ+生成プロンプト集(v1.1・副社長検証反映済み)

対象: 第25回 日本PTEG研究会 学術集会 公式PR動画(約30秒・16:9)
生成ツール: Kling(テキスト→動画/画像→動画)
ベース: `../assets/30sec-pr-video-brief.md`(既存指示書)のコンセプト・表現ルールを継承
変更点: ①Klingの生成単位(5秒クリップ)に合わせたカット割り ②**最後の10秒を「学術の説明」パート(PTEGとは+開催情報)にする構成** ③ナレーションを30秒実測適合の圧縮版に改稿(副社長検証の条件反映)

> **社長決定待ち(上申2件)**: ①本Kling版を既存公式指示書のv2として一本化するか
> ②ナレーションはA案(圧縮版・30秒維持=本書採用)かB案(全情報読み上げ・約40秒版)か
> → 詳細は§6。決定は `../PROMO_DECISION_LOG.md` に記録する。

> **要監修**: PTEGの説明文言(ナレーション・テロップ)は**ナレーション収録前に**世話人・事務局の
> 監修を完了させること(収録後の文言修正は再収録コストに直結)。監修時には「消化管減圧の適応に
> 触れない簡略化の可否」も明示的に確認する。

## 0. 全体設計
- 完成尺: 約30秒(28〜31秒) / 16:9 横型 / 用途: 公式サイト・YouTube・学会広報
- コンセプト: 「北海道から、次の未来へ。」(既存指示書を継承)
- 構成: 大地(十勝)→ 札幌 → 十勝清水の恵み(小麦・じゃがいも・にんにく・十勝若牛)→ 地域医療 → **学術の説明(PTEG CG+開催情報)**
- Kling生成は**1クリップ=1場面・各5秒**で計7〜9本生成し、編集で各3〜5秒にトリムして繋ぐ(1クリップに複数場面を詰め込まない — 破綻防止)
- カット間の切り替え: 基本はカット(直結)、カット2→3とカット5→6のみ0.5秒クロスディゾルブ(「都市→大地」「医療→未来」の転換点を柔らかく)
- 日本語テロップ・学会名・ポスターは**編集工程で配置**(生成AIに文字を描かせない)
- **ミュート視聴前提**: SNS・サイト埋め込みは無音自動再生が既定のため、地名・開催情報など要点はすべてテロップでも伝わる設計にする(十勝清水はカット3テロップで明示)
- 正式名称「第25回 日本PTEG研究会 学術集会」・会期・会場は**テロップとポスターで表示**し、読み上げからは外す(30秒に収めるための情報の委譲)
- BGM: ピアノ+ストリングス(既存指示書§7の英語プロンプトをそのまま使用)
- ナレーション: 日本人女性30〜40代・落ち着き・知性・温かみ(既存指示書§5と同一指定)

## 1. Kling共通設定
- モード: 高品質(Professional)モード / 長さ: 5秒 / アスペクト比: 16:9
- 全カット共通のスタイル句(各プロンプト末尾に付いている): photorealistic, cinematic, elegant, high-end documentary film quality
- **共通ネガティブプロンプト**(全カットで入力):
  `text, letters, captions, subtitles, watermark, logo, cartoon, anime, illustration, oversaturated colors, distorted hands, distorted faces`
- カット3・4は上記に加えて必ず: `onion, onions, red onion, shallot`(表現ルール: 玉ねぎ不使用)
- 人物が出るカット(5)と解剖CG(6)は破綻しやすい。カット5はリテイク前提、カット6は**静止画→画像→動画を主経路**にする(§3参照)

## 2. カット表(タイムライン)
| # | 時間 | 場面 | テロップ(編集で配置) | ナレーション |
|---|---|---|---|---|
| 1 | 0–4秒 | 十勝の大地(空撮) | 次回、PTEG研究会は北海道へ。 | 次回、PTEG研究会は、北海道・札幌へ。 |
| 2 | 4–8秒 | 札幌(開催地) | 2027年9月12日(日)/札幌開催 | 世話人の想いは、十勝清水から。 |
| 3 | 8–12秒 | 十勝清水の農(小麦→じゃがいも→にんにく の3連モンタージュ) | **十勝清水の恵み**——小麦/じゃがいも/にんにく | 小麦、じゃがいも、にんにく。 |
| 4 | 12–16秒 | 十勝若牛(放牧、任意で料理差し込み) | 十勝若牛 | そして、十勝若牛。大地の恵みは、 |
| 5 | 16–20秒 | 地域医療(寄り添うチーム医療) | 地域の力を、人を支える医療へ。 | 人を支える医療へ。 |
| 6 | 20–25秒 | **学術の説明①: PTEGとは(医療CG)** | PTEG(ピーテグ)=経皮経食道胃管挿入術 | PTEG——胃ろうが難しい患者さんを支える、日本発の手技。 |
| 7 | 25–30秒 | **学術の説明②: 開催情報+公式ポスター(元画像のまま)** | 第25回 日本PTEG研究会 学術集会/テーマ「地域・PTEG・ケアの近未来」/2027年9月12日(日) 札幌市教育文化会館 | 地域・PTEG・ケアの近未来。札幌で、お会いしましょう。 |

**ナレーション全文(A案・約140モーラ ≒ 28〜31秒。改稿後は必ず仮読みで実測すること)**:
「次回、PTEG研究会は、北海道・札幌へ。世話人の想いは、十勝清水から。小麦、じゃがいも、にんにく。そして、十勝若牛。大地の恵みは、人を支える医療へ。PTEG——胃ろうが難しい患者さんを支える、日本発の手技。地域・PTEG・ケアの近未来。札幌で、お会いしましょう。」

- ※「開催地=札幌」は冒頭の「北海道・札幌へ」+カット2テロップ「札幌開催」で担保。
- ※「十勝清水」は音声(カット2)とテロップ(カット3)の両方に必ず残す。**この行を短縮対象にしない**(社長指示「十勝清水の特徴を入れる」の核心のため)。
- ※カット6のナレーション・テロップは要監修(収録前に完了)。

## 3. カット別 Klingプロンプト

### カット1|十勝の大地(5秒生成→4秒使用)
```
Aerial drone shot flying slowly forward over the vast Tokachi plain in Hokkaido, Japan, in the early morning. An endless patchwork of green and golden farmland, the majestic Hidaka mountain range on the far horizon, soft golden sunrise light, thin morning mist drifting over the fields. Grand, clean, dignified northern landscape. Photorealistic, cinematic, elegant, high-end documentary film quality, 16:9.
```
ネガティブ: 共通+`buildings, cars, people`

### カット2|札幌(5秒生成→4秒使用)
```
Elegant cityscape of Sapporo, a clean modern city in northern Japan, in warm late-afternoon light shifting toward dusk. Slow aerial pan across a wide tree-lined park boulevard running through the city center, refined modern buildings on both sides, city lights just beginning to glow. Intelligent, welcoming, dignified urban atmosphere. Photorealistic, cinematic, elegant, high-end documentary film quality, 16:9.
```
ネガティブ: 共通のまま
※実在ランドマーク(時計台等)は生成AIでは形が崩れやすいため意図的に指定していない。実写素材が入手できるなら差し替え推奨。

### カット3|十勝清水の農(3クリップ生成→各約1.3秒のモンタージュ)
3a 小麦:
```
Low-angle tracking shot gliding through a golden wheat field swaying in the wind in Tokachi, Hokkaido, backlit by warm afternoon sunlight, mountains faint in the far background, ears of wheat glowing in the light. Rich, warm, abundant harvest mood. Photorealistic, cinematic, elegant, high-end documentary film quality, 16:9.
```
3b じゃがいも:
```
Slow dolly shot over neat rows of potato plants with small white flowers on a vast Hokkaido farm field, rich dark soil visible between the rows, soft natural sunlight, gentle breeze. Honest, fertile farmland mood. Photorealistic, cinematic, elegant, high-end documentary film quality, 16:9.
```
3c にんにく:
```
Close-up slow-motion shot of fresh white garlic bulbs with dry papery skin and distinct cloves, held gently in a farmer's weathered hands over a wooden crate, warm natural side light, shallow depth of field. Proud, artisanal harvest mood. Photorealistic, cinematic, elegant, high-end documentary film quality, 16:9.
```
ネガティブ(3a/3b/3c共通): 共通+`onion, onions, red onion, shallot`
※3cは玉ねぎに誤生成されやすい**最重要チェックポイント**。「皮が紙状で白い・房(クローブ)が見える」で判定し、疑わしければリテイク。

### カット4|十勝若牛(5秒生成→4秒使用)
```
Wide cinematic shot of healthy young cattle grazing calmly on a vast green pasture in Tokachi, Hokkaido, under a clear blue summer sky, gentle breeze moving the grass, majestic mountains in the far distance. Calm, proud, natural, unhurried. Photorealistic, cinematic, elegant, high-end documentary film quality, 16:9.
```
任意4b(料理カット2秒を差し込む場合):
```
Elegant close-up of a beautifully plated dish of lean, tender red beef from young cattle, lightly seared slices on a dark ceramic plate, thin steam gently rising, soft warm restaurant lighting, shallow depth of field, understated refined presentation, not flashy or commercial. Photorealistic, cinematic, elegant, high-end documentary film quality, 16:9.
```
ネガティブ: 共通+`onion, onions, red onion, shallot`(付け合わせに玉ねぎが出るのを防止)+4bは`heavily marbled wagyu, raw meat close-up`
※十勝若牛は**若齢牛の赤身が特徴**のブランド。霜降り和牛的な描写は誤り(ブランド毀損)。4bを採用する場合は肉質表現について事務局に確認。迷う場合は4bを見送り、放牧カットのみで成立させる。

### カット5|地域医療(5秒生成→4秒使用・リテイク前提)
```
Warm documentary scene inside a bright regional Japanese hospital room, calm wide shot: a Japanese doctor and two nurses gently attending to an elderly patient sitting by a large window, figures seen mostly from behind or in soft profile, soft natural daylight filling the room, a sense of teamwork, care and trust, calm and respectful atmosphere. Realistic modern medical setting. Photorealistic, cinematic, elegant, high-end documentary film quality, 16:9.
```
ネガティブ: 共通+`surgery, blood, medical devices close-up, syringes, direct eye contact with camera`
※AI生成人物の顔アップは「実在人物への酷似」「本物の患者との誤認」リスクがあるため、**引きの画・後ろ姿/横顔中心**の構図にしている。顔・手の破綻が出やすいので複数回生成し自然なテイクを採用。実写ストック素材が使えるならこのカットは差し替え推奨。

### カット6|学術の説明①: PTEG医療CG(5秒使用)
**主経路(推奨): 静止画を作ってから Kling の「画像→動画」で動かす**(解剖CGのテキスト→動画は破綻率が高いため)。
①静止画生成プロンプト(画像生成AI用):
```
Refined 3D medical illustration of a translucent human upper body in glowing pale blue glass style, esophagus and stomach softly illuminated inside the chest, a thin gentle line of light tracing a path from the neck down along the esophagus toward the stomach, clean white and pale blue palette, dark elegant background, official medical conference visual style, futuristic yet calm and trustworthy. High-detail CGI render, 16:9.
```
②Kling 画像→動画のモーションプロンプト:
```
Slow elegant camera orbit around the translucent glowing figure, the soft line of light gently pulsing as it traces down the esophagus toward the stomach, subtle particles of light drifting, calm and precise atmosphere, no text.
```
代替(テキスト→動画で直接生成する場合):
```
Refined 3D medical animation of a translucent human upper body rendered in glowing pale blue glass style, showing the esophagus and stomach softly illuminated, a thin gentle line of light tracing a path from the neck down along the esophagus toward the stomach, clean white and pale blue color palette, slow elegant camera orbit, futuristic yet calm, trustworthy, official medical conference visual style. Photorealistic CGI, cinematic, elegant, 16:9.
```
ネガティブ: 共通+`gore, blood, surgery, realistic organs, labels, arrows`
※公式ポスターの「半透明ブルーの人体+チューブ」ビジュアルとトーンを合わせている(世界観の一貫性)。
※解剖学的な正確さはAI生成では保証できない。象徴的表現に留め、精密な図解が必要なら既存CG素材を使用する。

### カット7|学術の説明②: エンディング背景(5秒生成→5秒使用)
```
Sapporo cityscape at blue hour seen from a high viewpoint, warm city lights glowing across the city, a very slow gentle zoom out, calm and hopeful mood, a large area of clean darkening sky occupying the upper half of the frame, leaving space for graphics. Photorealistic, cinematic, elegant, high-end documentary film quality, 16:9.
```
ネガティブ: 共通のまま
編集指示: この背景の上に、**公式ポスター元画像(改変・トリミング・色調整禁止)**を右側に配置し、左側にテロップ「第25回 日本PTEG研究会 学術集会」「テーマ: 地域・PTEG・ケアの近未来」「2027年9月12日(日) 札幌市教育文化会館」を配置。最後の1秒でゆっくり暗転。

## 4. 制作・仕上げの手順
0. **前提条件の確認(ここで止まる項目)**:
   - [ ] 公式ポスター**元画像**を受領し `pteg-promotion/assets/` に格納済み(カット7が組めない)
   - [ ] Klingの利用プランが**商用相当の利用(学会公式)**を許諾しているか確認
   - [ ] PTEG説明文言(ナレーション・テロップ)の**世話人・事務局監修が完了**(収録前必須)
1. Klingで各クリップを5秒・16:9・高品質モードで生成(カット3は3本、任意4bを入れるなら計9本。カット6は静止画→画像→動画の主経路で)。
2. 編集ソフトでカット表のとおりトリム・連結(計約30秒)。カット2→3、5→6のみ0.5秒ディゾルブ。
3. **統一グレーディング**: 別個生成したクリップは色味がばらつくため、全カットに共通のカラーグレーディング(上品・ややウォーム・彩度控えめ)を当てて1本のトーンに揃える。
4. 日本語テロップを編集で配置(明朝系フォント推奨・誤字チェック必須。特に「地域・PTEG・ケアの近未来」は一字一句正確に)。
5. カット7にポスター元画像を配置(改変禁止)。
6. ナレーション収録(既存指示書§5の声質指定・監修済み原稿で)+BGM(既存指示書§7)をミックス。ナレーションとBGMの被りすぎに注意。
7. クレジット(動画説明欄または最終フレーム小書き)に「映像の一部は生成AIを使用しています」の明記を推奨(公式広報としての透明性)。
8. 最終チェックリスト(§5)で全項目確認 → 社長・世話人・事務局の確認 → 公開。
9. 公開時期・掲載チャネルは広報・マーケティング部の告知カレンダーと接続する(演題募集開始等に合わせる。次回 `/pteg-plan` で計画化)。

## 5. 最終チェックリスト(既存指示書§9を本構成に合わせて改訂)
- [ ] 約30秒以内 / 16:9 / MP4
- [ ] 札幌が開催地であることが明確(カット1ナレーション・カット2/7テロップ)
- [ ] **十勝清水が音声とテロップの両方に登場**し「世話人の地域」として表現されている
- [ ] 小麦・じゃがいも・にんにくを使用/**玉ねぎが1フレームも映っていない**(カット3c・4bを重点確認)
- [ ] 十勝若牛を使用(4b採用時は赤身ブランドとして正しい肉質描写)
- [ ] 地域医療からPTEGへ自然につながる
- [ ] **最後に学術の説明がある**(PTEGとは+第25回・テーマ・日付・会場)
- [ ] テーマ表記「地域・PTEG・ケアの近未来」が正確(テロップ・ナレーションとも)
- [ ] 女性ナレーション/日本語テロップの誤字なし/「※要監修」等の下書き注記が残っていない
- [ ] ポスターを最後に元画像のまま配置
- [ ] 生成映像内にAI生成の文字・ロゴが写り込んでいない
- [ ] 全カットの色味が統一されている(グレーディング済み)
- [ ] 観光CM化しすぎていない(医療学会公式の品格)
- [ ] PTEGの医学的説明について世話人・事務局の監修を受けた(収録前)
- [ ] AI生成利用の明記(クレジット)を入れた

## 6. 副社長検証の結果(2026-09-03・Fableモデル)
**総合判定: 条件付き承認** → 以下の3条件を本書v1.1に反映済み。
1. ナレーション超過(実測約200モーラ≒34〜40秒)→ 圧縮版(約140モーラ)に改稿。正式名称・会期・会場はテロップ+ポスターに委譲。「十勝清水」行を短縮対象にする旧フォールバックは削除。
2. 「十勝清水」がテロップ不在(ミュート視聴で伝わらない)→ カット3テロップを「十勝清水の恵み——小麦/じゃがいも/にんにく」に変更。
3. 工程の前提条件(ポスター原本格納・収録前監修・注記残存チェック)→ §4手順0と§5チェックリストに組み込み。

その他反映: カット5を引き・後ろ姿構図に変更(実在人物酷似・患者誤認リスク)/カット4bの肉質表現を赤身に修正(十勝若牛ブランド保護)/カット6は静止画→画像→動画を主経路化/統一グレーディング・Kling商用ライセンス確認・AI利用クレジットを工程化。

**社長への上申(決定待ち)**:
- 上申1: 既存の「30秒公式PR動画 制作指示書」(Codex用)と本Kling版の関係を一本化すべき。推奨=本書を公式指示書の**v2**と位置づける(同尺・同コンセプトの公式動画仕様を2系統併存させない)。
- 上申2: ナレーションは**A案(圧縮版・30秒維持)を推奨**(本書採用)。全情報を読み上げたい場合はB案(約40秒版)も可能だが、その場合も「世話人の想い」行は削らない。
