# 世界バイラル楽曲 分析レポート（2024–2026）— Suno向け「勝ちパターン」抽出

作成日: 2026-06-18 / 用途: Suno AIで世界バイラルを狙う楽曲制作の設計指針
注意: ストリーミング数・チャート順位は出典どおり。BPM/キー/構造の数値はチャート分析サイト（Tunebat / SongBPM / SongData 等）の機械推定を含み、誤差あり。本レポートのレシピ仮説は「推定」と明記。

---

## 0. 調査した主要楽曲リスト（約45曲）

下表は2024–2026に世界的にバイラル/ヒットした代表曲。BPM/キーは推定（チャート分析サイト由来、半分/倍テンポ解釈で揺れあり）。

| # | 曲 / アーティスト | 主ジャンル | BPM(推定) | キー(推定) | バイラル根拠 |
|---|---|---|---|---|---|
| 1 | Die With A Smile / Lady Gaga & Bruno Mars | ポップ/ソウル・バラード | 約157(ハーフ約79) | G♭/F♯ | 2025年Spotifyグローバル最多(17億+)・年間Hot100 1位 |
| 2 | BIRDS OF A FEATHER / Billie Eilish | ベッドルーム・ポップ | 約105 | D♭ | 2024→2025もSpotify世界2位 |
| 3 | APT. / ROSÉ & Bruno Mars | K-pop×パワーポップ/ロック | 約149 | F♯m系 | 世界3位・「apateu」チャント大バズ |
| 4 | Ordinary / Alex Warren | フォーク・ポップ/ゴスペル | 約120 | C major | Hot100 10週1位・2025夏の世界曲1位 |
| 5 | DtMF / Bad Bunny | レゲトン/サルサ融合 | 約100前後 | - | 世界5位・アルバムDeBÍ TiRAR…世界1位 |
| 6 | luther / Kendrick Lamar & SZA | R&B/ヒップホップ | 約94 | - | 2025年間Hot100 2位 |
| 7 | Golden / HUNTR/X (KPop Demon Hunters) | K-pop（劇中） | 約130前後 | - | Global200 18週1位・歴史的現象 |
| 8 | Soda Pop / Saja Boys | K-pop（劇中・ブライト） | 約120前後 | - | Hot100 3位・TikTok最大級トレンド |
| 9 | Your Idol / Saja Boys | K-pop（劇中・ダーク） | - | - | Hot100 4位 |
| 10 | Espresso / Sabrina Carpenter | ディスコ・ポップ | 約104 | A major | 2024夏の世界曲1位 |
| 11 | Please Please Please / Sabrina Carpenter | ポップ | 約107 | - | 2024 Hot100 1位 |
| 12 | Million Dollar Baby / Tommy Richman | ファンク/オルタR&B | 約138(ハーフ約69) | F♯m | TikTok米2024年1位・10週連続 |
| 13 | Pink Pony Club / Chappell Roan | シンセ・ポップ/ディスコ | 約116 | - | 2025年間Hot100上位 |
| 14 | Good Luck, Babe! / Chappell Roan | シンセ・ポップ | 約117 | - | 2024グローバル大ヒット |
| 15 | Back to Friends / sombr | オルタ/インディーポップ | 約100前後 | - | 2025夏の世界曲5位 |
| 16 | Anxiety / Doechii | ヒップホップ（Gotyeサンプル） | 約130前後 | - | TikTok 2025大バズ |
| 17 | Not Like Us / Kendrick Lamar | ウェストコースト・ヒップホップ | 約101 | - | 2024世界的・グラミー総ナメ |
| 18 | BLACKPINK – Jump | K-pop×ハードスタイル/ユーロ | 約145 | - | 2025 EDM寄りクロスオーバー |
| 19 | Abracadabra / Lady Gaga | ダンス・ポップ/インダストリアル | 約135前後 | - | 2025バイラル(チャント) |
| 20 | Messy / Lola Young | オルタ・ポップ | 約120前後 | - | TikTok 2025大バズ |
| 21 | That's So True / Gracie Abrams | ベッドルーム/インディーポップ | 約100前後 | - | 2024–25大ヒット |
| 22 | A Bar Song (Tipsy) / Shaboozey | カントリー/ヒップホップ | 約81 | A major | 2024 Hot100超長期1位 |
| 23 | I Had Some Help / Post Malone & Morgan Wallen | カントリー・ポップ | 約128 | - | 2024 1位 |
| 24 | Beautiful Things / Benson Boone | ポップ/ロック・バラード | 約110 | - | 2024世界的 |
| 25 | Lose Control / Teddy Swims | ソウル/R&B | 約87 | - | 2024超ロングヒット |
| 26 | TEXAS HOLD 'EM / Beyoncé | カントリー・ポップ | 約110 | - | 2024 1位 |
| 27 | Si Antes Te Hubiera Conocido / KAROL G | レゲトン/グアラチャ | 約130前後 | - | 2024ラテン世界的 |
| 28 | Gata Only / FloyyMenor & Cris MJ | チリ系レゲトン | 約95前後 | - | 2024世界バイラル |
| 29 | MILLONARIO / 系レゲトン勢 | レゲトン | - | - | 2025ラテン上位 |
| 30 | Manchild / Sabrina Carpenter | ポップ | 約100前後 | - | 2025夏ヒット |
| 31 | 30 For 30 / SZA & Kendrick | R&B | 約90前後 | - | 2024–25 |
| 32 | Bandana / 系アフロビーツ | アフロビーツ | 約108前後 | - | 2025アフロ拡大例 |
| 33 | Love Me JeJe / Tems | アフロビーツ | 約105前後 | - | 2024アフロ世界化 |
| 34 | Sailor Song / Gigi Perez | インディー・フォーク | 約100前後 | - | 2024 TikTokバイラル |
| 35 | Houdini / Eminem | ヒップホップ | 約143 | - | 2024 |
| 36 | Taste / Sabrina Carpenter | ポップ/ロック | 約113 | - | 2024–25 |
| 37 | Disease / Lady Gaga | ダーク・ポップ | 約120前後 | - | 2024–25 |
| 38 | Bad Dreams / Teddy Swims | ポップ/ソウル | 約148(ハーフ約74) | - | 2024–25 |
| 39 | Timeless / The Weeknd & Playboi Carti | トラップ/R&B | 約110前後 | - | 2024–25 |
| 40 | We Can't Be Friends / Ariana Grande | シンセ・ポップ | 約108 | - | 2024 |
| 41 | Nasty / Tinashe | R&B/ダンス | 約110前後 | - | 2024 TikTokバイラル |
| 42 | Si Una Vez 系 / ラテン勢 | レゲトン/コリードス | - | - | 2025リージョナル・メキシカン拡大 |
| 43 | How It's Done / HUNTR/X | K-pop（劇中） | 約120前後 | - | 2025 |
| 44 | Free / Rumi & Jinu (KPDH) | K-popバラード | 約80前後 | - | 2025 |
| 45 | end of beginning / Djo | インディー/シンセ・ポップ | 約100前後 | - | 2024 TikTok超バイラル |

出典は各セクション末尾にまとめて記載。

---

## 1. 【ジャンル分布】今世界のバイラル上位で強いジャンル TOP7 と勢い

1. **ヒート/感情系ポップ（"heart-on-sleeve pop"・ベッドルーム/インディーポップ）— 最強で安定**
   素直で内省的な歌詞・ミドルテンポ。Billie Eilish "BIRDS OF A FEATHER"、Gracie Abrams、sombr、Gigi Perez、Djo。Spotifyも2025の柱として明言。勢い: ◎（持続）

2. **K-pop（特に劇中/ハイブリッド）— 2025最大の爆発**
   『KPop Demon Hunters』が地殻変動。HUNTR/X "Golden" がGlobal200を18週1位、サントラがHot100トップ10に4曲同時。APT.、BLACKPINK "Jump"。勢い: ◎（急上昇・物語性が燃料）

3. **ラテン（レゲトン/グアラチャ/リージョナル・メキシカン）— 構造的に拡大**
   Bad Bunny世界1位アルバム、KAROL G、コリードス勢のレゲトン/アフロ越境。Spotifyは「世界はもうラテンの音」と総括。勢い: ◎（非英語の主柱）

4. **カントリー×ポップ/ヒップホップのクロス — 米主導で世界へ**
   Shaboozey、Post Malone×Morgan Wallen、Beyoncé。Morgan Wallenが2025年間トップ・アーティスト。勢い: ○（強いが英語圏依存）

5. **R&B/ヒップホップ（メロディアス＆スロー）— 高位安定**
   Kendrick "luther"/"Not Like Us"、SZA、Teddy Swims、Tommy Richman。勢い: ○（プラトー）

6. **ダンス/ディスコ・ポップ＆ハイテンポ・クロスオーバー — 復権**
   Sabrina "Espresso"、Chappell Roan、Lady Gaga "Abracadabra"、ハードスタイル混入のK-pop。勢い: ○（チャント映え）

7. **アフロビーツ＆アフロハウス由来の音色 — 拡散・浸透**
   単独より「他ジャンルへの音色提供」で拡大（パーカッション/アフロハウス・シンセがポップ/ダンスに混入）。勢い: △→○（地味だが構造的）

出典: Spotify Wrapped 2025 trends, Billboard year-end 2025, NME非英語記事（下記）。

---

## 2. 【サウンド共通項】

- **BPM帯（推定）**: 二極化。
  - 感情系ポップ/インディー: **約95–120 BPM**（"Ordinary" 約120、Eilish 約105、Djo/sombr/Abrams 約100前後）。
  - ダンス/K-pop/チャント系: **約120–150 BPM**（APT. 約149、BLACKPINK Jump 約145、Abracadabra 約135前後）。
  - R&B/ヒップホップ/カントリー・トラップ: **約80–100 BPM**（Shaboozey 約81、luther 約94、Lose Control 約87、Tipsy系）。
  - ※ "Die With A Smile" や "Million Dollar Baby" は記譜上は高BPMだが体感ハーフタイム（約79、約69）。**「速い譜割×遅いグルーヴ」は鉄板**。
- **キー傾向（推定）**: メジャー（C/A/G♭）でアンセム性、マイナー（F♯m）で切なさ・クール。感情系はメジャー多め、R&B/ファンクはマイナー多め。
- **ボーカル処理**: ①生々しい近接ボーカル（ASMR的・ベッドルーム系）と、②加工チャント/ユニゾン（"apateu"・"Abracadabra"・Soda Popのブライトなレイヤー）の二系統。**ハモり/コーラスの厚み**が共通の武器。
- **ドロップ/サビ設計**: EDM的な無音落としより、**「歌のフックそのものがドロップ」**。チャント・反復ワード（apateu / abracadabra / espresso）でサビ＝ミーム化。
- **楽器・音色**: 生っぽいアコギ/ピアノ＋ゴスペル合唱（Ordinary）、ファンク・ベース＆クリーンギター（Million Dollar Baby/Espresso）、アフロ/ラテンのパーカッション、ハードスタイル/ユーロのシンセ刺し（K-pop）。**「生楽器の温度感」と「電子的フック」の同居**が今の手触り。

出典: Tunebat / SongBPM / SongData（推定BPM・キー）, Billboard chart-beat各記事。

---

## 3. 【構造パターン】Shorts/TikTok切り取り耐性

- **イントロ尺**: **0–8秒で歌（またはフック断片）に到達**。長尺イントロは不利。TikTokは3秒保持が分岐点（3秒超え維持で到達4倍）。
- **サビ（フック）到達**: 多くが**サビ or サビ級フックを15–30秒以内に提示**。短尺曲化が進行（APT. 2:53）。Alex Warrenは投稿前提の設計で意図的に作った。
- **ループ性**: サビの**1–2小節が単体で完結**し、繰り返しても飽きない。チャント語（apateu/abracadabra）はループ前提。
- **切り取られる箇所の特徴**:
  - ①**コール&レスポンス/チャント**（踊り・口パク用）→ APT., Soda Pop, Abracadabra
  - ②**一行で感情が刺さる歌詞**（"so true"・別れ/不安）→ 感情系ポップ、Doechii "Anxiety"の緊迫ビート
  - ③**ビートの落差/スピードアップ**（sped-up版が二次拡散）
  - ④**意外なサンプル/ジャンル混血**（Anxiety=Gotyeサンプル、カントリー×ヒップホップ）

出典: Buffer/HookMafia/Pyaar（TikTok hook論）, Variety（Alex Warren）, Billboard。

---

## 4. 【バイリンガル/非英語の台頭】

- **構造的トレンド**: 非英語ポップが世界チャートで継続拡大。Spotifyは2025を「世界はもうラテンの音」と総括。ラテン（レゲトン/グアラチャ/コリードス）、K-pop、アフロビーツ、ブラジリアン・ファンク、トルコ語等が押し上げ。
- **代表事例**:
  - **韓国語×英語**: APT.（韓国の飲みゲーム由来チャント「apateu」＋英語サビ）。KPDHは劇中曲で韓国語/英語ミックス。BLACKPINK Jump。
  - **スペイン語**: Bad Bunny（ほぼ全スペイン語で世界1位アルバム）、KAROL G、Gata Only（チリ）。
  - **英語フックの混ぜ方**: 非英語のヴァース＋**英語の短いチャント/ワンフレーズ**でグローバル接着（"apateu apateu" のように母語のキャッチ＋英語のフックを併置）。**「意味より音」で覚えられる反復ワード**が共通項。
- **示唆（日英5:5戦略への差分）**: 世界向けは「英語の比率を上げる」より、**英語の"音の良い1フレーズ"をフックに固定し、母語/世界観で差別化**するのが今の勝ち筋。日本語×英語なら、サビの掴みを英語チャント、世界観・物語を日本語で、が再現性高い。

出典: NME（非英語サージ）, Spotify Wrapped 2025, Billboard（APT./KPDH）。

---

## 5. 【再現可能な"勝ちパターン"】Suno向けレシピ仮説（すべて推定）

Sunoプロンプト基本式（推定・実務則）: **[ジャンル]＋[BPM]＋[ムード]＋[主要楽器]＋[ボーカル様式]＋[時代/レファレンス]**、構造タグ `[Intro][Verse][Chorus][Bridge]`、要素は1セクション3–4個まで。

### レシピA「チャント・アンセム」（最有望・APT./Abracadabra型）
- ジャンル: K-pop×パワーポップ/ダンスロック / BPM: **約145** / キー: F♯m or A
- 構造: イントロ4秒以内→**2小節の反復チャント・サビ**を冒頭提示→ヴァース→チャント増幅。曲長 2:30–3:00。
- 言語比率: **母語7：英語3**（サビは英語＋反復語）。
- 狙い: TikTok踊り/口パク。フック＝1語の反復ワードを必ず設計。

### レシピB「heart-on-sleeve バラード→アンセム」（Ordinary/Eilish型）
- ジャンル: フォーク・ポップ×ゴスペル合唱 / BPM: **約110–120** / キー: C major
- 構造: ピアノ/アコギ弾き語りで近接ボーカル開始→サビで合唱レイヤー爆発。15秒以内に一行刺さる歌詞。
- 言語比率: **英語5：母語5**（感情の核は母語、サビ掴みは英語）。
- 狙い: 「一行で泣ける」切り取り。Reels/Shortsの感情フック。

### レシピC「ハーフタイム・グルーヴ」（Die With A Smile/Million Dollar Baby型）
- ジャンル: ソウル/ファンク・ポップ / 記譜BPM **約138–157** だが**体感ハーフ（約69–79）** / キー: F♯m
- 構造: クリーンなファンク・ベース＆ギター、サビでデュエット/ハモり厚く。
- 言語比率: 英語6：母語4。
- 狙い: 「速い譜割×遅い揺れ」の中毒性。耳に残るメロ反復。

### レシピD「ラテン/アフロ・クロス」（Bad Bunny/KAROL G/アフロ音色型）
- ジャンル: レゲトン×アフロハウス・パーカッション / BPM: **約95–130** / キー: マイナー
- 構造: デンボウ/アフロのリズム土台＋メロディアスなフック。
- 言語比率: 母語（日本語）6：英語/スペイン語フック4。
- 狙い: 非英語の世界化トレンドに相乗り。リズムで国境越え。

### レシピE「インディー/ベッドルーム・バイラル」（Djo/sombr/Gigi Perez型）
- ジャンル: ドリーミー・インディーポップ / BPM: **約100** / キー: メジャー〜モーダル
- 構造: ローファイ近接ボーカル＋シンセ/ギターのループ。サビ前に「間」を作り、サビで開放。
- 言語比率: 英語5：日本語5。
- 狙い: sped-up二次拡散と「雰囲気」消費。短いループの完成度勝負。

出典: Medium各Sunoガイド（プロンプト式・BPM例）, Jack Righteous（Pop×Suno 2025）, 上記チャート分析。

---

## 出典URL一覧
- Spotify Wrapped 2025 trends: https://newsroom.spotify.com/2025-12-03/wrapped-music-trends/
- Spotify 2025 top artists/songs: https://newsroom.spotify.com/2025-12-03/wrapped-top-artists-songs-albums-podcasts-audiobooks/
- 非英語サージ(NME): https://www.nme.com/news/music/spotify-reports-growing-surge-of-non-english-pop-music-on-global-chart-3934169
- Billboard 年間Hot100 2025(1位): https://www.billboard.com/lists/lady-gaga-bruno-mars-2025-year-end-billboard-hot-100/
- Billboard 年間Hot100 2025データ: https://www.billboard.com/charts/year-end/2025/hot-100-songs/
- KPop Demon Hunters(Wikipedia): https://en.wikipedia.org/wiki/KPop_Demon_Hunters
- Golden Global200 18週(Billboard): https://www.billboard.com/lists/huntr-x-golden-hot-100-number-one-second-week/
- APT. BPM/キー(Tunebat): https://tunebat.com/Info/APT-ROS-Bruno-Mars/5vNRhkKd0yEAg8suGBpjeY
- Ordinary BPM/キー(SongBPM): https://songbpm.com/@alex-warren/ordinary-rezj0
- Ordinary 2025夏の世界曲1位(Billboard): https://www.billboard.com/music/chart-beat/alex-warren-ordinary-global-song-summer-2025-1236057671/
- Alex Warren 投稿前提制作(Variety): https://variety.com/2025/music/news/alex-warren-ordinary-viral-social-media-campaign-1236599119/
- Espresso 2024夏の世界曲1位(Billboard): https://www.billboard.com/music/chart-beat/sabrina-carpenter-espresso-number-one-global-song-of-the-summer-2024-1235766400/
- Million Dollar Baby BPM/キー(Tunebat): https://tunebat.com/Info/MILLION-DOLLAR-BABY-Tommy-Richman/7fzHQizxTqy8wTXwlrgPQQ
- TikTok Billboard Top 50(Wikipedia): https://en.wikipedia.org/wiki/TikTok_Billboard_Top_50
- TikTok hook論(Buffer): https://buffer.com/resources/trending-songs-tiktok/
- TikTok hook論(HookMafia): https://www.hookmafia.io/blog/i-tested-30-viral-tiktok-hooks-here-s-what-actually-works-in-2026
- Suno viralプロンプト(Medium): https://medium.com/@abhisheksd2003/best-suno-ai-prompts-for-viral-music-that-actually-work-in-2025-97d373731d8c
- Suno TikTok向け(Medium): https://travisnicholson.medium.com/50-suno-ai-prompts-for-viral-tiktok-songs-50976e23cfad
- Suno Pop 2025(Jack Righteous): https://jackrighteous.com/en-us/blogs/guides-using-suno-ai-music-creation/top-music-genres-2025-pop-suno
- ラテン2025年間(Rolling Stone): https://www.rollingstone.com/music/music-latin-lists/best-latin-songs-2025-1235477925/
- アフロポップ2025(Rolling Stone): https://www.rollingstone.com/music/music-lists/best-afropop-songs-of-2025-1235487623/
