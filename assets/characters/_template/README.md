# アセットテンプレート

新しいキャラ／小物を始めるときは、このフォルダをコピーします。

```bash
cp -r assets/characters/_template assets/characters/<your-asset-name>
```

その後:

1. `asset.yaml` を編集（name / type / prefix / height_m）
2. `concept/` に参照を集める
3. `docs/pipeline.md` の工程に沿って進める

各サブフォルダの役割は [`docs/conventions.md`](../../../docs/conventions.md) を参照。
