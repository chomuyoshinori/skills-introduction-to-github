# Kling用 30秒PR動画 シナリオ+生成プロンプト集(ドラフト)

対象: 第25回 日本PTEG研究会 学術集会 公式PR動画(約30秒・16:9)
生成ツール: Kling(テキスト→動画/画像→動画)
ベース: `../assets/30sec-pr-video-brief.md`(既存指示書)のコンセプト・表現ルールを継承
変更点: ①Klingの生成単位(5秒クリップ)に合わせたカット割り ②**最後を「学術の説明」パート(PTEGとは+開催情報)で締める構成**に変更

> 要監修: ナレーション・テロップの医学的記述(PTEGの説明)は世話人・事務局の監修を受けること。

## 0. 全体設計
- 完成尺: 約30秒(28〜31秒に収める) / 16:9 横型 / 用途: 公式サイト・YouTube・学会広報
- コンセプト: 「北海道から、次の未来へ。」(既存指示書を継承)
- 構成: 大地(十勝)→ 札幌 → 十勝清水の恵み(小麦・じゃがいも・にんにく・十勝若牛)→ 地域医療 → **学術の説明(PTEG CG+開催情報)**
- Kling生成は**1クリップ=1場面・各5秒**で計7〜9本生成し、編集で各3〜5秒にトリムして繋ぐ(1クリップに複数場面を詰め込まない — 破綻防止)
- カット間の切り替え: 基本はカット(素早い直結)、カット2→3とカット5→6のみ0.5秒クロスディゾルブ(「都市→大地」「医療→未来」の転換点を柔らかく)
- 日本語テロップ・学会名・ポスターは**編集工程で配置**(生成AIに文字を描かせない)
- BGM: ピアノ+ストリングス(既存指示書§7の英語プロンプトをそのまま使用)
- ナレーション: 日本人女性30〜40代・落ち着き・知性・温かみ(既存指示書§5と同一指定)

## 1. Kling共通設定
- モード: 高品質(Professional)モード / 長さ: 5秒 / アスペクト比: 16:9
- 全カット共通のスタイル句(各プロンプト末尾に付いている): photorealistic, cinematic, elegant, high-end documentary film quality
- **共通ネガティブプロンプト**(全カットで入力):
  `text, letters, captions, subtitles, watermark, logo, cartoon, anime, illustration, oversaturated colors, distorted hands, distorted faces`
- カット3・4は上記に加えて必ず: `onion, onions, red onion, shallot`(表現ルール: 玉ねぎ不使用)
- 顔・手が出るカット(5)と解剖CG(6)は破綻しやすいためリテイク前提で複数回生成する

## 2. カット表(タイムライン)
| # | 時間 | 場面 | テロップ(編集で配置) | ナレーション |
|---|---|---|---|---|
| 1 | 0–4秒 | 十勝の大地(空撮) | 次回、PTEG研究会は北海道へ。 | 次回、PTEG研究会は、北海道へ。 |
| 2 | 4–8秒 | 札幌(開催地) | 2027年9月12日(日)/札幌開催 | 開催地は、札幌。世話人の想いは、十勝清水から。 |
| 3 | 8–12秒 | 十勝清水の農(小麦→じゃがいも→にんにく の3連モンタージュ) | 小麦/じゃがいも/にんにく | 小麦、じゃがいも、にんにく。 |
| 4 | 12–16秒 | 十勝若牛(放牧、任意で料理差し込み) | 十勝若牛 | そして、十勝若牛。豊かな大地が育む、地域の力。 |
| 5 | 16–20秒 | 地域医療(寄り添うチーム医療) | 地域の力を、人を支える医療へ。 | その力は、人を支える医療へ。 |
| 6 | 20–25秒 | **学術の説明①: PTEGとは(医療CG)** | PTEG(ピーテグ)=経皮経食道胃管挿入術 ※要監修 | PTEG——胃ろうが難しい患者さんを支える、日本生まれの医療技術。※要監修 |
| 7 | 25–30秒 | **学術の説明②: 開催情報+公式ポスター(元画像のまま)** | 第25回 日本PTEG研究会 学術集会/テーマ「地域・PTEG・ケアの近未来」/2027年9月12日(日) 札幌市教育文化会館 | 第25回、日本PTEG研究会学術集会。テーマは、地域・PTEG・ケアの近未来。札幌で、お会いしましょう。 |

ナレーション全文(約30秒・要タイム計測、長い場合は「世話人の想いは〜」を短縮):
「次回、PTEG研究会は、北海道へ。開催地は、札幌。世話人の想いは、十勝清水から。小麦、じゃがいも、にんにく。そして、十勝若牛。豊かな大地が育む、地域の力。その力は、人を支える医療へ。PTEG——胃ろうが難しい患者さんを支える、日本生まれの医療技術。第25回、日本PTEG研究会学術集会。テーマは、地域・PTEG・ケアの近未来。札幌で、お会いしましょう。」

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
※3cは玉ねぎに誤生成されやすい最重要チェックポイント。「皮が紙状で白い・房(クローブ)が見える」で判定し、疑わしければリテイク。

### カット4|十勝若牛(5秒生成→4秒使用)
```
Wide cinematic shot of healthy young cattle grazing calmly on a vast green pasture in Tokachi, Hokkaido, under a clear blue summer sky, gentle breeze moving the grass, majestic mountains in the far distance. Calm, proud, natural, unhurried. Photorealistic, cinematic, elegant, high-end documentary film quality, 16:9.
```
任意4b(料理カット2秒を差し込む場合):
```
Elegant close-up of a beautifully plated premium Japanese beef dish on a dark ceramic plate, thin steam gently rising, soft warm restaurant lighting, shallow depth of field, understated refined luxury, not flashy or commercial. Photorealistic, cinematic, elegant, high-end documentary film quality, 16:9.
```
ネガティブ: 共通+`onion, onions, red onion, shallot`(付け合わせに玉ねぎが出るのを防止)

### カット5|地域医療(5秒生成→4秒使用・リテイク前提)
```
Warm documentary scene inside a bright regional Japanese hospital room: a Japanese doctor and two nurses gently talking with an elderly patient sitting by a large window, soft natural daylight, sincere caring expressions, a sense of teamwork and trust, calm and respectful atmosphere. Realistic modern medical setting. Photorealistic, cinematic, elegant, high-end documentary film quality, 16:9.
```
ネガティブ: 共通+`surgery, blood, medical devices close-up, syringes`
※顔・手の破綻が出やすい。複数回生成し、表情が自然なテイクを採用。

### カット6|学術の説明①: PTEG医療CG(5秒生成→5秒使用・リテイク前提)
```
Refined 3D medical animation of a translucent human upper body rendered in glowing pale blue glass style, showing the esophagus and stomach softly illuminated, a thin gentle line of light tracing a path from the neck down along the esophagus toward the stomach, clean white and pale blue color palette, slow elegant camera orbit, futuristic yet calm, trustworthy, official medical conference visual style. Photorealistic CGI, cinematic, elegant, 16:9.
```
ネガティブ: 共通+`gore, blood, surgery, realistic organs, labels, arrows`
※公式ポスターの「半透明ブルーの人体+チューブ」ビジュアルとトーンを合わせている(世界観の一貫性)。
※解剖学的な正確さはAI生成では保証できない。象徴的表現に留め、精密な図解が必要なら既存CG素材を使用する。
※安定しない場合は「画像生成で静止画を作る→Klingの画像→動画でゆっくりカメラを回す」方式が確実。

### カット7|学術の説明②: エンディング背景(5秒生成→5秒使用)
```
Sapporo cityscape at blue hour seen from a high viewpoint, warm city lights glowing across the city, a very slow gentle zoom out, calm and hopeful mood, a large area of clean darkening sky occupying the upper half of the frame, leaving space for graphics. Photorealistic, cinematic, elegant, high-end documentary film quality, 16:9.
```
ネガティブ: 共通のまま
編集指示: この背景の上に、**公式ポスター元画像(改変禁止)**を右側に配置し、左側にテロップ「第25回 日本PTEG研究会 学術集会」「テーマ: 地域・PTEG・ケアの近未来」「2027年9月12日(日) 札幌市教育文化会館」を配置。最後の1秒でゆっくり暗転。

## 4. 編集・仕上げの手順
1. Klingで各クリップを5秒・16:9・高品質モードで生成(カット3は3本、任意4bを入れるなら計9本)。
2. 編集ソフトでカット表のとおりトリム・連結(計約30秒)。カット2→3、5→6のみ0.5秒ディゾルブ。
3. 日本語テロップを編集で配置(明朝系フォント推奨・誤字チェック必須。特に「地域・PTEG・ケアの近未来」は一字一句正確に)。
4. カット7にポスター元画像を配置(改変・トリミング・色調整をしない)。
5. ナレーション収録(既存指示書§5の声質指定)+BGM(既存指示書§7)をミックス。ナレーションとBGMの被りすぎに注意。
6. 最終チェックリスト(§5)で全項目確認 → 社長・世話人・事務局の確認 → 公開。

## 5. 最終チェックリスト(既存指示書§9を本構成に合わせて改訂)
- [ ] 約30秒以内 / 16:9 / MP4
- [ ] 札幌が開催地であることが明確(カット2・7)
- [ ] 十勝清水が「世話人の地域」として表現されている
- [ ] 小麦・じゃがいも・にんにくを使用/**玉ねぎが1フレームも映っていない**(カット3c・4bを重点確認)
- [ ] 十勝若牛を使用
- [ ] 地域医療からPTEGへ自然につながる
- [ ] **最後に学術の説明がある**(PTEGとは+第25回・テーマ・日付・会場)
- [ ] テーマ表記「地域・PTEG・ケアの近未来」が正確
- [ ] 女性ナレーション/日本語テロップの誤字なし
- [ ] ポスターを最後に元画像のまま配置
- [ ] 生成映像内にAI生成の文字・ロゴが写り込んでいない
- [ ] 観光CM化しすぎていない(医療学会公式の品格)
- [ ] PTEGの医学的説明について世話人・事務局の監修を受けた

## 6. 副社長検証
(検証待ち)
