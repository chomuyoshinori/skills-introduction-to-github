# 専門家チーム（Subagents）

このディレクトリは、**司令塔（メインの Claude）+ 専門家チーム**型エージェント構成の「専門家」部分です。
中国OEM輸入 × Amazon販売事業（個人事業主）を立ち上げ・運営するためのチームを定義しています。

事業全体の前提と司令塔の役割は、リポジトリ直下の `CLAUDE.md` を参照してください。

## チーム編成

### ビジネス専門家（司令塔が依頼を振り分ける相手）

| サブエージェント | 担当領域 |
|---|---|
| `business-strategist` | 事業戦略・全体設計（司令塔の右腕） |
| `market-researcher` | 市場・競合・需要リサーチ |
| `trend-scout` | 先進国の流行・トレンド先読み |
| `product-planner` | 商品企画・差別化・OEM仕様 |
| `creative-designer` | クリエイティブ・デザイン・撮影ディレクション |
| `china-sourcing-expert` | 中国の仕入れ・OEM交渉・品質管理 |
| `global-logistics-expert` | 国際物流・通関・関税・世界の流通 |
| `inventory-manager` | 在庫・発注・倉庫オペレーション |
| `marketing-specialist` | Amazon内マーケ・広告・ページ最適化 |
| `sns-specialist` | SNS集客・ブランディング・外部流入 |
| `sales-specialist` | 価格戦略・販路拡大・卸/B2B |
| `data-analyst` | データ分析・KPI・需要予測・A/Bテスト |
| `accountant` | 個人事業の経理・税務・資金繰り |
| `legal-advisor` | 法務（輸入規制・表示・知財・規約） |
| `ethics-compliance` | 倫理・コンプライアンス・リスク管理 |

### 運用補助（このチーム設定ファイル自体を保守する用）

| サブエージェント | 担当領域 |
|---|---|
| `code-reviewer` | 設定ファイル等の変更レビュー |
| `repo-explorer` | リポジトリ内の読み取り専用調査 |

## 使い方

司令塔（メインの Claude）に自然文で相談すると、内容に応じて適切な専門家へ自動的に振り分けます。

```
キャンプ用の大型タープを中国OEMで作ってAmazonで売りたい。いけそうか全体を検討して。
→ 司令塔が market-researcher / trend-scout / china-sourcing-expert /
   global-logistics-expert / legal-advisor などに並列で相談し、結論を統合します。
```

特定の専門家を指名することもできます。

```
legal-advisor に、PSE が必要かどうか確認して
china-sourcing-expert に、MOQ交渉の落としどころを相談して
```

## チームの動き方（司令塔モデル）

1. **分解** — オーナーの依頼を担当領域に分ける
2. **委任** — 関係する専門家サブエージェントに並列で相談
3. **統合** — 各専門家の結論を突き合わせ、矛盾や抜けを調整
4. **行動化** — 一人事業の制約を踏まえ「今やること」に落とす
5. **エスカレーション** — 断定できない／プロ確認が要る点はオーナーに明示

## 専門家を追加・編集するには

各専門家は Markdown + フロントマターで定義します。

```markdown
---
name: エージェント名（小文字・ハイフン）
description: いつ呼ばれるべきか（自動振り分けの決め手になる）
tools: 使えるツールをカンマ区切り（例: Read, Write, WebSearch, WebFetch）
model: opus / sonnet / haiku（省略可）
---

ここに専門家への指示（担当・進め方・出力フォーマット）を書く。
```

新しい業種を足したいときは、このディレクトリに `<名前>.md` を追加し、
`CLAUDE.md` のチーム一覧にも1行加えてください。

> ⚠️ `legal-advisor` / `accountant` / `ethics-compliance` の助言は一般的な情報提供であり、
> 最終判断は必ず有資格の専門家（弁護士・税理士など）に確認してください。
>
> 詳細な仕組み: https://code.claude.com/docs/en/sub-agents
