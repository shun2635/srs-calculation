# feature_mask_tables

実データ由来の「特徴量をマスクした時の予測精度テーブル」を置く場所です。

推奨構成:

```
inputs/feature_mask_tables/<dataset_id>/
  raw.csv
  schema.yaml
  README.md   (任意)
```

設計の詳細は `docs/design/real_data.md` を参照してください。

