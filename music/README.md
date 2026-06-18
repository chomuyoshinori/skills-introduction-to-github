# 🎵 音楽制作チーム(Suno × YouTube/SNS バイラル)

Suno AI で **YouTube/TikTok/Shorts でバズる**楽曲を、AIエージェントチームで継続的に制作する仕組みです。
世界・日本のトレンドとリスナーコメントを分析し、**日本語5割・英語5割**のスタイルプロンプトと歌詞を作ります。

> ⚠️ 本チームの制作物は **オリジナル**であること(既存曲の盗用をしない)。AI生成物・著作権・各プラットフォーム規約は公開前に必ず自分で確認してください。

## チーム構成(`.claude/agents/`)
| エージェント | 役割 |
|---|---|
| `music-trend-analyst` | 世界・日本のチャート/バイラル傾向と楽曲特徴(ジャンル/BPM/構造/フック)を分析 |
| `comment-insight-analyst` | リスナーのコメントを分析し「何が刺さるか」を抽出 |
| `viral-strategist` | Shorts/TikTok/YouTube でバズる構造(フック・尺・ループ・UGC化)とリリース戦略を設計 |
| `lyricist` | 日本語5割・英語5割のバイリンガル歌詞(口ずさめるフック重視)を作詞 |
| `suno-prompt-engineer` | Suno用スタイルプロンプト+構造タグを作成(日英混在の崩れ対策込み) |
| `music-red-team-critic` | **批判的検証ゲート**。「これはバズらない」理由を突き、修正案を出す |
| `music-producer` | プロデューサー(編集長)。全出力を統合し1曲の制作パッケージに仕上げる司令塔 |
| `release-retrospective-reviewer` | **学習ループ**。公開後の実績と照合し `LESSONS.md` / `VIRAL_PLAYBOOK.md` を更新 |

## ワークフロー
```
MUSIC_PROFILE.md + VIRAL_PLAYBOOK.md + LESSONS.md を踏まえる
        │
        ▼
 トレンド分析 + コメント分析(並行)
        │
        ▼
 バイラル設計 → 作詞(日英5:5) → Sunoプロンプト化
        │
        ▼
 music-red-team-critic が批判的検証(必須ゲート)
        │
        ▼
 music-producer が統合 → music/songs/ に制作パッケージ
        │              → SONG_LOG.md に企画を記録
        ▼
 (公開後)release-retrospective-reviewer が実績照合 → LESSONS.md / VIRAL_PLAYBOOK.md 更新
```

## 使い方(スラッシュコマンド)
- `/music-trend-analysis` — 世界・日本のバイラル傾向とコメント、バズ構造を分析し `music/analysis/` に保存、勝ち筋を `VIRAL_PLAYBOOK.md` に蓄積。
- `/make-song` — チーム総出で楽曲(Sunoスタイルプロンプト+日英5:5歌詞)を制作。`/make-song シティポップ 失恋` のようにジャンル/テーマ指定も可。
- `/music-retrospective` — 公開済み楽曲の実績を企画時仮説と照合し、教訓を蓄積。

## 主要ファイル
- `MUSIC_PROFILE.md` — 制作方針の中心(ターゲット・言語比率・ジャンル方針)。**ここを更新すると曲の方向が変わる。**
- `VIRAL_PLAYBOOK.md` — 再現性のある勝ち筋(分析で随時更新)。
- `SONG_LOG.md` — 出した曲企画の記録(後で実績照合)。
- `LESSONS.md` — 蓄積された教訓(全担当が制作前に参照)。
- `analysis/` — トレンド・コメント分析レポート。
- `songs/` — 制作パッケージ(コピペで使えるスタイルプロンプト+歌詞)。
```
