# QUICKSTART — まず数冊で識別を試す（フェーズ1）

蔵書RAGの最初の一歩。**ローカルのMac**（SSDを触れる環境）で、`00_identify.py` を数冊に対して走らせ、
書誌情報の抽出精度を確かめる。実ファイルは一切変更しない（非破壊）。

> 全体像は [../PROJECT.md](../PROJECT.md)、技術詳細は [ARCHITECTURE.md](ARCHITECTURE.md) 参照。
> このページは「識別を数冊で試す」ところまで。OCR本番・索引・検索は疎通後に進める。

---

## 0. 前提
- macOS、Python 3.10+ が入っている（`python3 --version` で確認）
- 蔵書PDFが外付けSSDにある（例: `/Volumes/SSD/claude-lab/books/`）
- Anthropic の APIキーがある

---

## 1. このリポジトリをローカルに取得

レシピ抽出とは別プロジェクトなので、好きな場所に clone する。

```bash
cd ~/projects   # 任意の作業場所
git clone <このリポジトリのURL> books-rag
cd books-rag
```

> すでに clone 済みなら `git pull` で最新化するだけ。

---

## 2. Python環境と依存（識別テストに必要な最小限だけ）

識別フェーズは軽い3つだけでOK（重い sentence-transformers/torch は索引段で入れる）。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U anthropic pymupdf pyyaml
```

---

## 3. 設定ファイルを作る

```bash
cp config/config.example.yaml config/config.yaml
```

`config/config.yaml` を開き、**`paths.books_dir` を自分のSSDの本フォルダに**書き換える。
（識別テストだけなら `work_dir` / `db_dir` は後回しでよいが、一応それっぽいパスにしておく）

```yaml
paths:
  books_dir: "/Volumes/あなたのSSD名/claude-lab/books"
```

コスト重視なら識別モデルを下げてもよい（任意）:

```yaml
ocr:
  identify_model: "claude-haiku-4-5"   # 既定は claude-opus-4-8
```

---

## 4. APIキーを環境変数で渡す

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

> キーは config.yaml に直書きしない（環境変数で渡す）。

---

## 5. まず “数冊だけ” 走らせる

フォルダ全体ではなく、**ファイルを明示**して3〜5冊試す。状態の違う本を混ぜると判定材料になる
（きれいな本／古い本／縦書き／横書き 等）。

```bash
python scripts/00_identify.py \
  "/Volumes/SSD/claude-lab/books/本A.pdf" \
  "/Volumes/SSD/claude-lab/books/本B.pdf" \
  "/Volumes/SSD/claude-lab/books/本C.pdf"
```

実行すると各本について、こう表示される:

```
▶ 本A.pdf  (埋め込みテキスト, 248p)        ← ここが「埋め込みテキスト」か「画像N枚」かに注目
  ✓ 『書名』 / 著者 ／ジャンル [確信度 high]
```

- `埋め込みテキスト` … PDFに文字データがある＝**無料で識別できた**
- `画像N枚` … 文字データが無く、表紙・奥付を画像OCRした

結果は `knowledge/catalog.csv` に書き込まれる（原本PDFは無傷）。

---

## 6. 結果を確認

```bash
open knowledge/catalog.csv     # 表計算アプリで開く（またはエディタで）
```

- 書名・著者・ジャンルが正しく取れているか
- `confidence` が low の本はどれか
- 誤判定があれば、その場でCSVを直してよい（非破壊なので安全）

---

## うまくいったら

- 良ければフォルダ全体へ: `python scripts/00_identify.py`（`--force` で再実行）
- カタログを開いて誤判定を直し、`priority`（high/mid/low）を記入 → これでOCRの優先順位が決まる
- その後、高優先の本から `01_ocr.py → 02_index.py → 03_query.py` の疎通へ

---

## 持ち帰ってほしいもの（このリポジトリ用セッションで調整するため）

次回このリポジトリ側で改善するために、以下を共有してもらえると助かる:

1. **コンソール出力**（各本が「埋め込みテキスト」か「画像」か、確信度）
2. **catalog.csv の中身**（数冊ぶん）
3. **誤判定の例**（取り違えた書名・著者など）
4. つまずいたエラーがあればそのメッセージ

→ これを見て、しきい値（`TEXT_THRESHOLD`）や抽出プロンプトを調整する。

---

## つまずきポイント

| 症状 | 対処 |
|------|------|
| `設定ファイルがありません` | 手順3を実施（example をコピー） |
| `環境変数 ANTHROPIC_API_KEY が未設定` | 手順4を実施 |
| `output_config` 関連のエラー | `pip install -U anthropic` でSDKを最新に |
| 縦書きで埋め込みテキストが文字化け | しきい値を上げて画像OCRに倒す（持ち帰ってくれれば調整） |
| パスにスペース/日本語でエラー | パスを `"..."` で囲む |
| レシピ抽出と同時でAPIが遅い | 数冊なら影響軽微。気になれば抽出が落ち着いてから |
