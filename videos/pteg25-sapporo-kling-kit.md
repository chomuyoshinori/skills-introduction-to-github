# 第25回 日本PTEG研究会 学術集会 次年度開催地紹介動画
# Kling 制作キット(カット別プロンプト集+編集手順)

元資料: 「次年度開催地紹介動画 制作指示書」(30秒 / 16:9 /「北海道から、次の未来へ。」)

- トーン: 壮大・上品・医療・北海道・未来への期待
- 質感: 実写映画・ドキュメンタリー風(過度なSF・近未来表現は避ける)
- ストーリー: 北海道の大自然 → 札幌 → 十勝清水 → 地域の力 → 地域医療 → 札幌・学会

---

## 1. 制作フローの全体像

Klingは1回の生成で **5秒または10秒** のクリップしか作れないため、30秒を1本で生成するのではなく、
**カットごとにクリップを生成 → 編集ソフトで結合** するのが正しい進め方です。

```
① Klingで各カットのクリップを生成(計11クリップ、各5秒で生成して編集でトリム)
② 各カット2〜4テイク生成し、ベストテイクを選定
③ 編集ソフト(Premiere / DaVinci Resolve / CapCut等)で結合・トリム
④ テロップを編集で合成(★AIに文字を生成させない — 指示書の必須要件)
⑤ ナレーション録音・BGM・カラーグレーディング
⑥ ラストは学会ポスターの元画像をそのまま配置してフィナーレ
```

## 2. Kling 共通設定

| 項目 | 設定 |
|---|---|
| モデル | Kling 2.1 / 2.5系の最新モデル |
| モード | Professional(高品質)モード |
| 画角 | **16:9** |
| クリップ長 | 5秒(編集で必要尺にトリム) |
| プロンプト言語 | 英語推奨(精度が安定。日本語版も併記) |

**共通ネガティブプロンプト**(全カットに毎回入れる):

```
text, letters, words, subtitles, captions, watermark, logo, readable signage,
distorted faces, deformed hands, extra limbs, cartoon, anime, illustration,
oversaturated colors, sci-fi, futuristic neon, cyberpunk, glitch, low quality, blurry
```

**共通スタイル文**(各プロンプトの末尾に付ける):

```
Cinematic live-action documentary style, photorealistic, shot on 35mm film,
natural color grading, high detail. No text or logos anywhere in the frame.
```

**カット間の連続性のコツ**: 前カットのラストフレームを書き出し、次カットを
「画像から動画(Image to Video)」の開始フレームに使うと、つながりが滑らかになります。

---

## 3. カット別 生成シート

### CUT 1｜0〜4秒｜北海道へ(クリップ①)

- 生成方法: テキストから動画(T2V)
- 演出: 派手にしない。壮大で静かな導入。「北海道に来た」と感じさせる。

**English prompt:**
```
Aerial shot slowly descending through soft morning clouds, revealing the vast
landscape of Hokkaido, Japan at sunrise: rolling green plains, distant mountain
ranges, golden morning light spreading quietly across the land. Slow majestic
camera descent, calm and serene mood, epic but quiet opening.
```

**日本語プロンプト:**
```
柔らかな朝の雲を抜けて、ゆっくりと降下する空撮。眼下に北海道の雄大な大地、
連なる山々、朝日の光が静かに広がる。壮大だが静かで上品な導入。
実写映画・ドキュメンタリー風、文字やロゴは一切入れない。
```

- テロップ(編集で合成): **次回、PTEG研究会は北海道へ。**

### CUT 2｜4〜8秒｜札幌(クリップ②〜④の短カットつなぎ)

テンポよく複数の顔を見せるカットなので、1クリップに詰め込まず **3クリップ生成して編集で約1.3秒ずつつなぐ**。

**②-a 大通公園(空撮):**
```
Aerial dolly-forward shot over Odori Park in Sapporo, Japan on a clear day:
a long green park boulevard cutting through the modern city center, tree-lined
promenade, people strolling far below, bright daylight.
```

**②-b 札幌市時計台:**
```
Ground-level cinematic shot of a historic white wooden western-style clock tower
building in Sapporo, Japan, surrounded by modern buildings, soft daylight,
gentle slow push-in.
```

**②-c 札幌の夜景(空撮):**
```
Sweeping aerial night view of Sapporo city, Japan: a grid of warm city lights
stretching to the horizon, elegant and calm, slow aerial glide.
```

- 注意: 実在ランドマーク(時計台・テレビ塔)は形が崩れやすい。**形状が破綻したテイクは不採用**。
  安定しない場合は実写ストック素材への差し替えも検討する。
- テロップ(編集で合成): **2027年9月12日（日）／札幌開催**

### CUT 3｜8〜12秒｜札幌から十勝清水へ(クリップ⑤)

- 生成方法: **画像から動画(I2V)を強く推奨**。ポスター上部の北海道地図の構図を静止画として用意し、
  それを開始フレームにして動きを付ける。
- 光のラインの経路(札幌→十勝清水)を正確に出したい場合は、KlingではなくAfter Effects等の
  モーショングラフィックスで作る方が確実。Klingを使う場合は以下。

**English prompt (I2V):**
```
A beautiful stylized map of Hokkaido floating elegantly. A thin glowing line of
warm light slowly extends across the map from the west (Sapporo area) toward the
southeast (Tokachi region), soft particles of light drifting, gentle slow camera
push-in, dignified and hopeful mood. The map has no text or place names.
```

- 地名・文字は地図に入れない(テロップとして編集で合成)。
- テロップ(編集で合成): **開催地は札幌。**(一拍置いて)**世話人の想いは、十勝清水から。**

### CUT 4｜12〜17秒|十勝清水(クリップ⑥)

- 生成方法: T2V
- 「豊かな大地」の印象を最優先。

**English prompt:**
```
Wide cinematic shot of the vast Tokachi plain in Hokkaido, Japan: wind rippling
across green pasture, young black-and-white Holstein cattle grazing calmly,
farm fields stretching to the horizon, the Hidaka mountain range faint in the far
distance, warm afternoon sunlight, slow lateral drone glide, documentary realism.
```

**日本語プロンプト:**
```
広大な十勝平野のワイドショット。牧草地を風が渡り、ホルスタインの若牛が
ゆったりと草を食む。畑が地平線まで広がり、遠景にうっすらと日高山脈。
暖かい午後の光。ゆっくりとした横移動のドローン撮影。ドキュメンタリー風の実写質感。
```

- ナレーション: **「豊かな大地に育まれた、地域の力。」**

### CUT 5｜17〜20秒｜十勝の恵み(クリップ⑦〜⑨の短カットつなぎ)

3秒に3要素なので **3クリップ生成して約1秒ずつつなぐ**。自然で温かみのある映像に。

**⑦ 若牛(寄り):**
```
Gentle close-up of young Holstein cattle in a sunny Hokkaido pasture, soft warm
light on their coats, calm and peaceful, shallow depth of field.
```

**⑧ 畑:**
```
Low aerial glide over vast farm fields in Tokachi, Hokkaido: neat rows of potato
plants and golden wheat swaying in the wind, late afternoon sun, warm tones.
```

**⑨ 収穫物(ジャガイモ・小麦・ニンニク):**
```
Macro slow dolly across freshly harvested potatoes, golden ears of wheat, and
white garlic bulbs arranged naturally on a rustic wooden surface, warm sunlight,
appetizing and wholesome, shallow depth of field.
```

- ⚠️ このカットのネガティブプロンプトに **`onions`** を追加(指示書:玉ねぎを名産として強調しない)。
- 表現の中心は指示書どおり **若牛・ジャガイモ・小麦・ニンニク**。

### CUT 6｜20〜24秒｜地域の暮らしから、医療へ(クリップ⑩〜⑪)

2クリップ生成して各約2秒でつなぐ。

**⑩ 地域の暮らし:**
```
Warm documentary scene of everyday life in a small rural Hokkaido town: a family
walking together along a quiet street, elderly neighbors chatting and smiling,
gentle natural light, medium-wide shots, warm and nostalgic mood.
```

**⑪ 地域医療:**
```
Warm scene of community healthcare in rural Japan: a nurse in soft-colored
uniform gently talking with a smiling elderly patient in a bright clinic room,
soft window light, compassionate caring atmosphere, shallow depth of field,
medium shot, documentary realism.
```

- ⚠️ **最重要(指示書)**: PTEGの解剖学的CG・PTEGそのもの(チューブ・内視鏡・処置シーン)は
  絶対に映像化しない。このカットのネガティブプロンプトに
  **`surgery, blood, endoscope, medical tubes, operating room, cold blue lighting`** を追加。
- 医療は「冷たい専門性」ではなく「人と地域を支える温かさ」で描く。
- ナレーション: **「この大地で暮らす人々を、医療が支える。」**

### CUT 7｜24〜30秒｜札幌で、お会いしましょう(クリップ⑫〜⑬+ポスター静止画)

構成: ⑫雄大な風景(約1.5秒) → ⑬札幌夜景に温かな光(約1.5秒) → 白フェード → **ポスター元画像**(約3秒)。

**⑫ 夕暮れの北海道(戻り):**
```
Sweeping aerial shot of vast Hokkaido landscape at dusk: mountains and plains
bathed in soft golden-purple twilight, majestic and calm, slow forward glide.
```

**⑬ 札幌の夜景に広がる温かな光:**
```
Aerial night view of Sapporo city, warm golden lights gradually glowing brighter
and spreading across the city like a gentle wave of warmth, hopeful and
welcoming mood, slow rising camera, soft bloom, gradually brightening toward
a soft white glow.
```

- 白フェードは編集で確実にかける(Klingの明転は不安定なため)。
- **学会ポスターは元画像をそのまま配置**(文字の崩れ防止。AI生成・AI加工は不可)。
- ナレーション: **「北海道・札幌で、お会いしましょう。」**
- 最終テロップ(編集で合成):
  **第25回 日本PTEG研究会 学術集会／2027年9月12日（日）／札幌市教育文化会館／北海道・札幌で、お会いしましょう。**

---

## 4. テロップ・ナレーション一覧(すべて編集工程で合成)

| タイム | 種別 | 内容 |
|---|---|---|
| 0〜4秒 | テロップ | 次回、PTEG研究会は北海道へ。 |
| 4〜8秒 | テロップ | 2027年9月12日（日）／札幌開催 |
| 8〜12秒 | テロップ | 開催地は札幌。／(一拍)／世話人の想いは、十勝清水から。 |
| 12〜17秒 | ナレーション | 「豊かな大地に育まれた、地域の力。」 |
| 20〜24秒 | ナレーション | 「この大地で暮らす人々を、医療が支える。」 |
| 24〜30秒 | ナレーション | 「北海道・札幌で、お会いしましょう。」 |
| ラスト | テロップ | 第25回 日本PTEG研究会 学術集会／2027年9月12日（日）／札幌市教育文化会館／北海道・札幌で、お会いしましょう。 |

## 5. 最終チェックリスト(指示書の必須要件)

- [ ] 全体が「大自然→札幌→十勝清水→地域の力→地域医療→札幌・学会」のストーリーになっている
- [ ] 実写映画・ドキュメンタリーの質感。SF・近未来表現が混入していない
- [ ] 医療シーンが温かい印象になっている(冷たい・怖い印象のテイクは不採用)
- [ ] PTEGの解剖学的CG・処置・チューブ類が一切映っていない
- [ ] AI生成映像内に文字・ロゴ・看板文字が出ていない(出たテイクは不採用 or 該当部分をトリム)
- [ ] テロップ・開催情報・学会名はすべて編集で正確に合成した
- [ ] ラストのポスターは元画像をそのまま配置した
- [ ] 十勝清水の表現は若牛・ジャガイモ・小麦・ニンニク中心。玉ねぎを強調していない
- [ ] 単なる観光紹介ではなく「地域から学会へ」の流れで30秒にまとまっている

## 6. 生成のコツ・リテイク基準

- 各クリップは **2〜4テイク** 生成し、ベストを選ぶ(Klingは同一プロンプトでも出来にばらつきあり)。
- 顔のアップは崩れやすいため、人物はミディアム〜ワイドショット中心にする(CUT6は特に)。
- 実在ランドマークが不自然なら、そのカットだけ実写ストック素材に差し替えるのが安全。
- カットのつなぎが硬い場合は、前クリップのラストフレームを次クリップのI2V開始フレームに使う。
- 納品解像度が足りない場合は、Topaz Video AI等で4Kアップスケールする。
