# legacy decoupling runbook

このドキュメントは、`legacy/` をリポジトリから外しても root CLI が動き続ける状態に到達するまでの具体的な作業順を記録したものです。

[`migration-from-legacy.md`](migration-from-legacy.md) よりも運用寄りの文書です。現在は `legacy/` を履歴資料として保持する方針なので、削除計画ではなく decoupling の記録と検証 checklist として使います。

## 目標状態

次をすべて満たしたときにだけ、目標状態に到達したとみなします。

- root Poetry project だけがサポート対象の runtime entry point である
- サポート対象の研究 workflow がすべて `src/` 経由で動く
- root test が `legacy/src` を `sys.path` に足さなくても通る
- `legacy/` ディレクトリを消しても `srs-real-gen`、`srs-game-gen`、`srs-test` が壊れない
- 共同研究者向け docs が通常運用のために `legacy/` を要求しない

## 現在の状態

主な decoupling blocker はすでに解消しています。

- parity test は `legacy` モジュールを直接 import しない
- test bootstrap は `legacy/src` を `sys.path` に追加しない
- 共同研究者向け docs は通常運用のために `legacy/` を要求しない
- root config lookup は `legacy/config.yaml` を前提にしない
- `legacy/` を隠して root workflow が動くことを確認する verification command がある

現在残っているものは意図的なものです。

- `src/` は persistence 境界で歴史的 compatibility format を所有している
- root の synthetic CLI surface は intentionally partial であり、archive-only command は `legacy/` に残している
- `legacy/` 自体は履歴資料として保持している

## 剥がし順

### Step 1. root CLI の公開契約を固定する

目的:

- `legacy/` が消えたあとも何のコマンドをサポートし続けるかを確定する

必要作業:

- `README.md` と `src/README.md` に、root でサポートするコマンド一覧を固定する
- 未移行または保留の `legacy` コマンドを明示する
- 移行中も root script 名は安定させる

完了条件:

- root でサポートするコマンド一覧の正本が 1 つに定まっている
- 利用者が root と `legacy` のどちらを先に見るべきか曖昧でない

### Step 2. 共同研究者向け primary docs から `legacy` 依存を外す

目的:

- `docs/` と root README だけで通常利用ができる状態にする

必要作業:

- quick start から `cd legacy` 前提を外す
- 現行 workflow に必要なコマンド例を root docs へ移す
- `legacy` へのリンクは archive や数理 appendix 用に限定する

完了条件:

- 共同研究者が `legacy/README.md` を開かなくても、依存導入、root CLI 実行、test 実行までできる

### Step 3. `legacy` の直接 import を固定 fixture に置き換える

目的:

- test のコードレベル依存を `legacy/src` から外す

必要作業:

- `gamegen.*` を import している parity test を checked-in fixture 比較に置き換える
- 期待される rule 出力を `tests/fixtures/` 配下に CSV、YAML、または Python fixture として保存する
- parity の意図は維持しつつ、比較対象を live な `legacy` 実行ではなく固定期待値に切り替える

依存経路から外す対象:

- `tests/conftest.py` の `legacy/src` path injection
- `gamegen.rules.*` を import している parity test

完了条件:

- `tests/` が `legacy` を import しない
- `poetry run srs-test` が `src/` だけで通る

### Step 4. compatibility-format I/O を明示的な compatibility layer に閉じ込める

目的:

- 後方互換のファイル処理は維持しつつ、`legacy` project 自体は不要にする

必要作業:

- compatibility code を `src/srs_calculation/infrastructure/persistence/` に閉じ込める
- 歴史的な CSV support が package dependency ではなく compatibility format だと docs で明記する
- compatibility-format 前提をこれ以上 `domain/` や `application/` に広げない

完了条件:

- `src/` 内に残る `legacy` という語が compatibility format または migration note だけを意味する
- `src/` の runtime path が `legacy/` ディレクトリ内ファイルを要求しない

### Step 5. synthetic CLI の不足分を埋める

目的:

- root から公開している CLI surface だけで、サポート対象の synthetic workflow が完結するようにする

必要作業:

- 必要な `game-gen` コマンドを `src/` に移植する
- もしくは、未移行コマンドを明示的に廃止し、サポート対象 docs から外す
- 維持する root CLI workflow ごとに integration test と e2e test を足す

現在の判断:

- `rank-heatmap` と `rule-corr-heatmap` は root の `srs-game-gen` surface に復帰した
- `check-axioms`, `summarize-axioms`, `axiom-summary-heatmap`, `pipeline`, `make-figures-png` は引き続き root 契約から外し、`legacy/` 配下の archive-only command として扱う

完了条件:

- root README で告知している全コマンドが root Poetry project だけで動く
- サポート対象 workflow に `legacy/pyproject.toml` が不要である

### Step 6. `legacy/` を既定の runtime home と見なす config 前提を外す

目的:

- runtime 設定が root project と明示引数だけで解決されるようにする

必要作業:

- docs と code を見直して、`legacy/config.yaml` を既定扱いしている表現や前提を外す
- 必要な既定値は root の config 規約または code 内の built-in default に移す
- root CLI の config lookup order を明文化する

完了条件:

- 通常の root CLI 利用が `legacy/` 配下ファイルを要求しない

現在の実装メモ:

- サポート対象 root config lookup order は、明示 CLI 引数 -> 明示 `--config <path>` -> built-in default
- `legacy/config.yaml` の暗黙 lookup は行わない
- repository root の `./config.yaml` も自動探索しない

### Step 7. CI とローカルで「消せる」ことを証明する

目的:

- 実際に `legacy/` が不要になったことを検証する

必要作業:

- `legacy/` を一時的に隠すか rename する検証 job または script を追加する
- `poetry run srs-real-gen --help` を通す
- `poetry run srs-game-gen --help` を通す
- `poetry run srs-test` を通す
- e2e suite を通す

推奨検証コマンド:

```bash
poetry run srs-test
poetry run srs-test tests/e2e -q
poetry run srs-real-gen --help
poetry run srs-game-gen --help
```

完了条件:

- `legacy/` が runtime path から外れても検証が通る

### Step 8. `legacy` の公開入口を落として archive 化する

目的:

- サポート対象の root path を壊さずに移行を完了する

必要作業:

- `legacy/pyproject.toml` を runnable entry point として docs しない
- `legacy/` を archive 扱いにするか、リポジトリから削除する
- `src/` が正本になったことを migration docs に反映する

完了条件:

- リポジトリが `legacy` を通常の execution surface として扱わない
- 正本 docs が `src/` を implementation of record として説明している

現在の状態:

- docs 上は完了しており、`legacy/` は archive-only、root Poetry project は唯一のサポート対象 execution surface として記述している
- repository 判断として、`legacy/` は履歴資料として保持する
- この runbook は、サポート対象 workflow が runtime で `legacy/` を要求しないことを示す記録として維持する

## 推奨 PR 分割

これは 1 本の PR でやらない方がよいです。

推奨順:

1. docs と CLI contract の明確化
2. parity fixture 化と test bootstrap cleanup
3. synthetic CLI の残差移行または廃止
4. removability verification の CI 追加
5. `legacy/` の最終的な archive 化位置づけの確定

## レビュー checklist

次のどれかが残っている removal PR は reject します。

- root test がまだ `legacy` を import している
- サポート対象コマンドがまだ `legacy/README.md` にしか書かれていない
- `legacy/` を隠すと root CLI が落ちる
- compatibility-format cleanup と無関係な大規模 refactor が混ざっている

## Non-goal

この runbook は、legacy 互換の CSV 列名をただちに捨てることまでは要求しません。

`legacy/` を消したあとでも、その命名は `src/` 実装が所有する compatibility format として残して構いません。
