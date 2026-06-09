# 技術設計（ARCHITECTURE）

蔵書RAGの技術的な設計と、各コンポーネントの選定理由をまとめる。
全体像は [../PROJECT.md](../PROJECT.md) を参照。

---

## パイプライン詳細

```
PDF ──⓪識別──▶ カタログ整備 ──①OCR──▶ ページ単位テキスト ──②分割──▶ チャンク ──③埋め込み──▶ Chroma ──④検索+生成──▶ 回答
```

> ⓪は本番OCRの前に走らせる「整理フェーズ」。安く済み、これで優先順位が決まる。

中間生成物はすべて `work_dir`（SSD上）に置く。Gitには載せない。

```
work_dir/
  text/<book-slug>/0001.txt, 0002.txt, ...   # ページごとのOCRテキスト
  text/<book-slug>.jsonl                      # {page, text} を1行1ページで集約
db_dir/                                       # Chroma の永続化ディレクトリ
```

---

## ⓪ 識別・分類（`00_identify.py`）— 非破壊

蔵書の名前・分類がバラバラな状態を整理するための前処理。**実ファイルは移動・リネームしない**
（原本そのまま方針）。各PDFの**表紙・標題紙・奥付など数ページだけ**読んで書誌情報を抽出し、
`knowledge/catalog.csv` に「書名・著者・出版社・刊行年・ジャンル」を整備する。

- 安く済ませる: まず**埋め込みテキストを無料で抽出**。取れなければ先頭2p＋最終1pだけ画像化してClaude visionで読む。
- 全ページは読まない（識別に必要なページだけ）。
- 出力後、人がカタログを開いて誤判定を直し、`priority`(high/mid/low) を記入 → これで本番OCRの優先順位が決まる。
- レジューム対応（`identify_status=done` はスキップ、`--force` で再実行）。

> なぜ先にやるか: 名前も分類も不明だと「どの本を優先OCRするか」を決められない。
> ⓪で全体像を把握 → 高優先から①OCR、という順番にする。

## ① OCR（`01_ocr.py`）

縦書き和書に強いエンジンで取り直す。インターフェースは「ページ画像 → テキスト」で統一し、
**バックエンドを差し替え可能**にしてある（`config.yaml` の `ocr.backend`）。

| バックエンド | 値 | 特徴 | 向き |
|-------------|-----|------|------|
| Claude vision | `claude` | 精度は最高クラス。縦書き・ルビ・旧字に強い | 重要本・難しい本。コストは高め |
| Google Document AI | `documentai` | 縦書き対応・大量処理で安価 | 全冊のざっくりOCR |

- PDF→画像のレンダリングは **PyMuPDF（fitz）** を使用（poppler不要）。`ocr.dpi` で解像度調整。
- **二段構え運用**（PROJECT.md の方針）: まず `documentai` で全冊 → 深く読む本だけ `claude` で再OCR。
- **レジューム対応**: ページ単位でファイル出力するので、途中で止まっても続きから再開できる。

> Document AI バックエンドは `google-cloud-documentai` の標準的な呼び出しで実装しているが、
> Google SDKのAPIは変わりうるので、本番投入前に最新ドキュメントで確認すること。
> Claude バックエンドは検証済み（サンプルでほぼ100%）。

---

## ② チャンク分割（`02_index.py` 内）

- ページ本文を `chunk.size` 文字ごと、`chunk.overlap` 文字の重なりを持たせて分割。
- 各チャンクに **メタデータ（書名 / ページ番号 / チャンク連番）** を付与 → 出典提示に使う。
- 日本語は文字数ベースで十分（トークナイズ不要）。長すぎず短すぎずの目安: 600〜1000文字。

## ③ 埋め込み・インデックス（`02_index.py`）

- ベクトルDB: **Chroma**（ファイルベース・個人利用に最適・サーバ不要）。
- 埋め込みモデルは差し替え可能（`embedding.provider`）:

| provider | モデル例 | 特徴 |
|----------|---------|------|
| `local` | `intfloat/multilingual-e5-large` | 無料・日本語に強い。CPUでも動くが500冊は時間がかかる（夜間バッチ向き） |
| `openai` | `text-embedding-3-large` | API課金・速い・セットアップが楽 |

- e5系は仕様上、文書側に `passage: `、質問側に `query: ` の接頭辞を付ける（スクリプトで自動処理）。
- **レジューム対応**: 登録済みの本はスキップ。

## ④ 検索・回答生成（`03_query.py`）

1. 質問を埋め込み → Chromaで関連チャンクを `query.top_k` 件検索
2. ヒットしたチャンク本文＋出典（書名・ページ）をプロンプトに詰める
3. **Claude（`claude-opus-4-8`）** が、渡された本文だけを根拠に**出典付きで回答**
4. ストリーミング表示。adaptive thinking 有効。

- ハルシネーション防止のため、システムプロンプトで「渡された抜粋に無いことは答えない／出典を必ず示す」を指示。
- 回答末尾に、使った抜粋の「書名 p.XX」を一覧表示。

---

## 依存パッケージ

`scripts/requirements.txt` 参照。主要なもの:

- `anthropic` … Claude API（OCR・回答生成）
- `pymupdf` … PDF→画像
- `chromadb` … ベクトルDB
- `sentence-transformers` … ローカル埋め込み（`embedding.provider: local` の場合）
- `pyyaml` … 設定読込
- `google-cloud-documentai` … Document AI OCR（任意）

---

## 設定（`config/config.example.yaml`）

`config.example.yaml` を `config/config.yaml` にコピーして、SSDのパスやAPIキー関連を埋める。
APIキーは設定ファイルに直書きせず、環境変数で渡す:

- `ANTHROPIC_API_KEY` … Claude
- `GOOGLE_APPLICATION_CREDENTIALS` … Document AI（サービスアカウントJSONのパス）
- `OPENAI_API_KEY` … OpenAI埋め込みを使う場合

> `config.yaml` と認証情報は **Gitに載せない**（`.gitignore` 済み）。
