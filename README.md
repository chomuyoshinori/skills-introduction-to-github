# プロジェクト索引

このリポジトリは、Claude Code を使った複数の AI 実験プロジェクトを収めています。
各プロジェクトはディレクトリが分かれており、独立して動作します。

## 🐺 Character & Prop Studio（Blender 3Dモデリング）
キャラクター／ゲーム小物を一点物で作り込む、Blender + AI エージェント支援の制作システム。
試行錯誤の最適化、批判的専門家(critic)との反復改善、web参照の接地、解剖学リグを備え、
人型ゴブリンと四足オオカミを critic スコア 9.5 まで仕上げた実績があります。

- 入口: [`docs/pipeline.md`](docs/pipeline.md)
- 学習ループ: [`docs/learning.md`](docs/learning.md) / エージェント: [`docs/agents.md`](docs/agents.md)
- セキュリティ・安全設計: [`docs/security.md`](docs/security.md)
- 成果物: `assets/characters/`（goblin-warrior, dire-wolf）

## 🇯🇵 日本株 リサーチ・分析チーム
毎日の日本投資情報を中期・成長重視(中リスク)で分析し、レッドチーム検証と学習ループ付きで
レポートを生成する Claude Code エージェントチーム。

> ⚠️ レポート・分析は情報整理および教育目的であり、投資助言ではありません。

- 入口: [`CLAUDE.md`](./CLAUDE.md)
- プロファイル: `INVESTMENT_PROFILE.md` / 記録: `DECISION_LOG.md` / 教訓: `LESSONS.md`
- レポート: `reports/`
- コマンド: `/daily-report`, `/retrospective`, `/us-report`, `/crypto-report`

---

> どちらのプロジェクトも「批判的検証 + 継続的な学習・改善ループ」という共通の設計思想で
> 作られています。詳細は各プロジェクトの入口ドキュメントを参照してください。
