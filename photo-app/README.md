# スマホ写真管理システム — 作り方の推奨と全体像

個人利用を前提とした「スマホ写真の母艦(Mac mini)管理+選別・削除支援」システムの
構成推奨ガイドです。詳細な機能・UX/UI仕様は [SPEC.md](./SPEC.md) を参照してください。

> **Phase 1〜3 すべて実装済み**: 選別アプリが [sift/](./sift/) にあります(セットアップ手順も同ディレクトリの README に記載)。
> スクショ/メモ写真/ぼやけ検出、重複・連写・類似のグループ比較、スワイプ選別、統計、PWA(ホーム画面に追加)、
> 夜間自動スキャン、キーボード高速選別まで動作します。あとは Mac mini に Immich を立てて繋ぐだけ(Phase 0)。
>
> **iCloud写真から乗り換える場合**は [ICLOUD_MIGRATION.md](./ICLOUD_MIGRATION.md) の手順で(検証前に iCloud を切らないこと)。

---

## 結論(TL;DR)

1. **ゼロから全部は作らない。** 「スマホから自動バックアップ → Mac miniに保存 → スマホ容量を解放 → どこからでも閲覧」は、オープンソースの **[Immich](https://immich.app/)**(自宅版Googleフォト)がすでに完成度高く実現している。特に *スマホ側のバックグラウンド自動アップロードアプリ* は個人開発の最難関で、ここを自作するのは割に合わない。
2. **Claude Codeで作るのは「選別(トリアージ)アプリ」。** あなたの要望の核心 — 「重複・スクショ・メモ写真を自動で見つけ、比較しながら、考えずにポンポン削除できるUI」 — には既存アプリに決定版がない(SlideboxやGeminiはスマホ内の写真しか扱えず、サーバー上の写真に使えない)。Immich の API の上に載せる Web アプリとして自作するのが最適で、規模的にも Claude Code に非常に向いている。
3. **外出先からの閲覧は [Tailscale](https://tailscale.com/)。** ポート開放不要・個人無料・安全。自宅のMac miniにどこからでもVPN的に届く。
4. **バックアップは必須。** この構成ではMac miniが写真の「唯一のコピー」になる瞬間が生まれる。外付けSSD+Time Machine(できればクラウドに第3コピー)を Phase 0 に含める。

## 全体像

```
┌─ スマホ ─────────────┐         ┌─ Mac mini Pro(常時稼働の母艦)──────────────┐
│ Immich公式アプリ      │  Wi-Fi  │  OrbStack (Docker)                          │
│  ・撮影→自動アップロード │ ──────▶ │   ├ Immich Server(保存・閲覧・検索・ML)     │
│  ・アップ済みを端末から削除│        │   ├ PostgreSQL / ML コンテナ               │
│  (=容量解放)          │         │   └ ★選別アプリ「Sift」(Claude Codeで自作)  │
└──────────────────┘         │  写真実体: 外付けSSD                         │
        ▲                        │  バックアップ: Time Machine → 別の外付けHDD   │
        │ Tailscale(外出先から閲覧・選別)                                       │
        └────────────────────┴───────────────────────────┘
```

- **Immich が担当**: 自動バックアップ、スマホ容量解放、タイムライン閲覧、被写体検索(AI)、顔認識、完全重複の検出、RAW対応、ゴミ箱(30日復元)
- **自作アプリ「Sift(仮称)」が担当**: スクショ/メモ写真/類似写真の候補抽出、スワイプ選別UI、類似グループの比較・ベストショット提案、解放容量の見える化

## なぜこの構成か(3案比較)

| | 案A: フルスクラッチ自作 | **案B: Immich + 自作トリアージ(推奨)** | 案C: 既製品のみ |
|---|---|---|---|
| スマホ自動バックアップ | ◎作れれば理想だが、iOS/Androidのバックグラウンド制約との戦いで個人開発の最難関 | ◎ Immich公式アプリが解決済み | ◎ |
| 要望の実現度(スクショ・重複掃除UI) | ◎(作れば) | ◎ 核心部分だけ自作するので思い通りにできる | △ Immich標準の重複検出のみ。スクショ/メモ掃除の「流れ作業UI」は存在しない |
| 開発量 | 数ヶ月〜(挫折リスク大) | **数日〜数週間**(Web アプリ1本) | ゼロ |
| 保守 | 全部自分 | 重い部分(同期・保存・ML)はImmichコミュニティが保守 | — |
| 費用 | 0円 | 0円(全てOSS/個人無料枠) | 0円 |

## ロードマップ

### Phase 0 — 開発なしで土台を作る(半日)
1. Mac mini に [OrbStack](https://orbstack.dev/)(個人無料のDocker環境。Docker Desktopより軽い)を入れ、Immich を起動:
   ```bash
   mkdir -p ~/immich && cd ~/immich
   curl -LO https://github.com/immich-app/immich/releases/latest/download/docker-compose.yml
   curl -L -o .env https://github.com/immich-app/immich/releases/latest/download/example.env
   # .env を編集: UPLOAD_LOCATION=/Volumes/<外付けSSD名>/immich-photos / DB_PASSWORD を変更
   docker compose up -d   # → http://localhost:2283
   ```
2. スマホに Immich アプリを入れ、自動バックアップを設定 → 完了後「アップロード済みをデバイスから削除」で容量解放。
3. Mac mini とスマホに Tailscale を入れ、外出先からも Immich が開けることを確認。
4. Time Machine(またはrsync)で写真実体+ImmichのDBを別ディスクへ自動バックアップ。**これを飛ばすと Mac mini 故障=写真全損**。
5. (RAWが一眼カメラ由来なら)Immich の外部ライブラリ機能で取り込みフォルダを登録。
6. Mac のスリープを無効化(システム設定 → エネルギー、または `sudo pmset -c sleep 0`)。

**→ この時点で「スマホ容量がいっぱいになる」問題はほぼ解決する。**

### Phase 1 — 選別アプリ MVP(Claude Codeで開発)
- 候補抽出: スクリーンショット検出+完全重複(Immich API利用)
- スワイプ選別画面(←削除予定 / →残す / ↑お気に入り)+ Undo
- 「削除予定」→ 確認画面 → Immichのゴミ箱へ(即時完全削除はしない)

### Phase 2 — 賢くする
- 類似写真・連写のグループ化と比較ビュー、ベストショット自動提案
- メモ写真検出(OCR文字量・CLIP検索)、ぼやけ写真検出
- 統計画面(解放した容量、レビュー枚数)

### Phase 3 — 磨き込み
- PWA化(スマホのホーム画面から起動、外出先のスキマ時間に選別)
- 自動ルール(例: 30日過ぎたスクショを自動で候補入り)
- Macのキーボード操作対応(J/K/F/Zで高速選別)

## Claude Code での進め方

**Claude Code で作るのは適切か? → はい、最適です。** ただし進め方に2点推奨があります。

1. **専用の新リポジトリを作る。** このリポジトリ(skills-introduction-to-github)は投資リサーチチーム用に構成されているため、`photo-sift` のような新リポジトリを作り、この `photo-app/` 2ファイルをコピーして開発を始めるのがよい。
2. **Claude Code は Mac mini 上で動かす。** 開発対象(選別アプリ)が Immich API を `localhost` で叩けるため、実物のデータで動作確認しながら進められる。

最初のプロンプト例:

> SPEC.md を読んで、Phase 1 の MVP を実装して。技術スタックは仕様書の通り
> (React + Vite + TypeScript + Tailwind / Hono + SQLite)。
> Immich は http://localhost:2283 で稼働中、APIキーは .env に置いた。
> まずスクリーンショット候補の抽出ジョブと、スワイプ選別画面から。

## 運用コスト

- ソフトウェア: **0円**(Immich・OrbStack個人利用・Tailscale個人プランすべて無料)
- ハードウェア: 外付けSSD(写真本体用)+バックアップ用HDDの2台推奨
- ランニング: Mac mini の電気代程度。クラウド第3コピーを持つ場合のみ Backblaze B2 等が数百円/月
