# `legacy/` からの移行方針

このドキュメントは、現在の `legacy/` 中心構成から [`../../../src/`](../../../src/) 配下の新規実装へどう進めるかを定義します。

## 移行原則

- `legacy/` は、挙動が再現または意図的に置換されるまで参照実装として残す
- 新しい本実装コードは、`legacy/` を肥大化させるより `src/` を優先する
- 移行はディレクトリ単位の丸ごとコピーではなく、機能単位で進める
- 各段階でテストとドキュメントを同期させる

## 推奨される移行順序

### フェーズ 1: 共通言語の安定化

- アーキテクチャ境界を文書化する
- 貢献ルールを定義する
- ADR と spec のテンプレートを整備する
- どの文書が正本かを明確にする

### フェーズ 2: domain ロジックの抽出

独立してテストしやすいロジックから始めます。

- ランキング規則
- 連合表現
- 公理判定や評価ロジック

主な移行元候補:

- [`../../../legacy/src/gamegen/rules`](../../../legacy/src/gamegen/rules)
- [`../../../legacy/src/gamegen/axioms`](../../../legacy/src/gamegen/axioms)

### フェーズ 3: `application/` でワークフロー再構築

主要ワークフローを明示的なサービスとして組み直します。

- 合成ゲーム生成
- ランキング適用
- 公理チェック
- 実データ import のオーケストレーション

### フェーズ 4: アダプタとインターフェースの移行

domain と application が安定してから進めます。

- CLI アダプタの再構築
- 設定ローダーの移行
- CSV と描画アダプタの移行

### フェーズ 5: legacy エントリポイントの段階的廃止

十分な同等性が確認できてから進めます。

- 利用者を新しい CLI に誘導する
- `legacy/` を参照または保管用途へ縮退させる

## 対応付けの目安

- `legacy/src/gamegen/rules` -> `src/srs_calculation/domain/ranking/rules`
- 連合やゲーム表現 -> `src/srs_calculation/domain/games`
- `legacy/src/gamegen/axioms` -> `src/srs_calculation/domain/axioms`
- `legacy/src/gamegen/commands` -> `src/srs_calculation/interfaces/cli`
- `legacy/src/gamegen/io` -> `src/srs_calculation/infrastructure/persistence`
- `legacy/src/realgen/commands` -> `src/srs_calculation/interfaces/cli` と `src/srs_calculation/application/`
- `legacy/config.yaml` 読み込み -> `src/srs_calculation/infrastructure/config`

## 現在の進捗

リポジトリにはすでに、`src/` 側の最初の ranking 移行スライスが入っています。

- in-memory の ranking core を担う `domain/games` と `domain/ranking`
- `CoalitionGame` に対する rule 実行を担う `application/ranking/apply_ranking_rules.py`
- legacy 互換の game CSV ワークフローを担う `application/ranking/apply_ranking_rules_to_game_csv.py`
- legacy 互換 CSV 境界を担う `infrastructure/persistence/csv_game_repository.py` と `csv_ranking_repository.py`
- 移行した ranking workflow に被せる薄い synthetic-game CLI adapter を担う `interfaces/cli/game_gen.py`
- これらをカバーする `tests/` 配下の unit / integration test
- 初回バッチの ranking rule を deterministic な fixture で比較する parity test

今後の移行は、このスライスを起点に積み上げる前提で進めます。

## ある機能が移行完了とみなせる条件

次を満たしたとき、その機能は移行済みとみなします。

- `src/` に新実装がある
- 自動テストで新実装がカバーされている
- 関連 docs が更新されている
- アーキテクチャ変更があれば ADR に記録されている
- 対応する `legacy` 挙動との関係が明確である

## 避けるべきアンチパターン

- `legacy` モジュールを境界整理なしに `src/` へ大きくコピーする
- 新しい設計概念を `legacy/` 側へ直接混ぜ込む
- 旧経路と新経路の挙動差を文書化せずに運用する
- アーキテクチャ変更を spec や ADR なしで大規模にマージする
