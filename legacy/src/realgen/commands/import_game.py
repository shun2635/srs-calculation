"""Import a real dataset into canonical game CSV format."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import click
import yaml

from gamegen.config import load_config
from ..io.feature_labels import write_feature_labels_yaml
from ..datasets import resolve_dataset_dir, resolve_dataset_out_base


@dataclass(frozen=True)
class ImportedGame:
    n: int
    scores_by_mask: dict[int, float]
    ranks_by_mask: dict[int, int] | None
    feature_columns: list[str]
    feature_descriptions: dict[str, str]


def _load_schema_yaml(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {}
    return {str(k): v for k, v in raw.items()}


def _dense_rank_by_score(scores_by_mask: Mapping[int, float]) -> dict[int, int]:
    order = sorted(scores_by_mask.keys(), key=lambda m: (-float(scores_by_mask[m]), int(m)))
    ranks: dict[int, int] = {}
    last: float | None = None
    current = 0
    for mask in order:
        s = float(scores_by_mask[mask])
        if last is None or s != last:
            current += 1
            last = s
        ranks[int(mask)] = current
    return ranks


def _transform_score(value: float, transform: str) -> float:
    t = str(transform or "identity").strip().lower()
    if t in {"identity", "none", ""}:
        return float(value)
    if t == "negate":
        return -float(value)
    raise ValueError(f"Unsupported score_transform: {transform!r} (supported: identity, negate)")


def _binned_rank_by_score(
    scores_by_mask: Mapping[int, float],
    *,
    bins: int,
    exclude_mask_from_range: int | None = 0,
) -> dict[int, int]:
    """Assign ordinal ranks by equal-width binning over [min(score), max(score)].

    Higher score -> better (smaller) rank.
    """
    b = int(bins)
    if b <= 0:
        raise ValueError("bins must be >= 1")
    if not scores_by_mask:
        return {}
    if exclude_mask_from_range is not None:
        values = [float(v) for m, v in scores_by_mask.items() if int(m) != int(exclude_mask_from_range)]
    else:
        values = [float(v) for v in scores_by_mask.values()]
    if not values:
        values = [float(v) for v in scores_by_mask.values()]
    vmin = min(values)
    vmax = max(values)
    if vmax == vmin:
        return {int(mask): 1 for mask in scores_by_mask.keys()}

    width = (vmax - vmin) / float(b)
    out: dict[int, int] = {}
    for mask, score in scores_by_mask.items():
        s = float(score)
        if s >= vmax:
            r = 1
        elif s <= vmin:
            r = b
        else:
            # Top bin => rank 1, bottom bin => rank b
            r = int((vmax - s) / width) + 1
            if r < 1:
                r = 1
            elif r > b:
                r = b
        out[int(mask)] = int(r)
    return out


def _write_game_csv(
    *,
    out_path: Path,
    n: int,
    scores_by_mask: Mapping[int, float],
    ranks_by_mask: Mapping[int, int],
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    header = [f"player{i+1}" for i in range(n)] + ["score", "rank"]

    def membership(mask: int) -> list[str]:
        return ["1" if (mask >> i) & 1 else "0" for i in range(n)]

    order = sorted(scores_by_mask.keys(), key=lambda m: (-float(scores_by_mask[m]), int(m)))
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        for mask in order:
            writer.writerow(membership(int(mask)) + [str(float(scores_by_mask[mask])), str(int(ranks_by_mask[int(mask)]))])


def import_feature_mask_csv(
    *,
    raw_csv: Path,
    score_column: str,
    score_transform: str,
    rank_column: str | None,
    feature_columns: list[str],
    filters: Mapping[str, str],
    empty_score: float | None,
    empty_rank: int | None,
    feature_descriptions: Mapping[str, str],
    allow_incomplete: bool = False,
) -> ImportedGame:
    with raw_csv.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError("CSV is empty.") from exc
        rows = [r for r in reader if r]

    col_index = {str(name): i for i, name in enumerate(header)}
    if score_column not in col_index:
        raise ValueError(f"score_column not found: {score_column}")
    if rank_column is not None and str(rank_column) not in col_index:
        raise ValueError(f"rank_column not found: {rank_column}")
    missing = [c for c in feature_columns if c not in col_index]
    if missing:
        raise ValueError(f"feature_columns not found: {missing}")

    n = len(feature_columns)
    if n <= 0:
        raise ValueError("feature_columns is empty.")

    def row_ok(row: list[str]) -> bool:
        for k, want in filters.items():
            j = col_index.get(k)
            if j is None:
                return False
            got = row[j] if j < len(row) else ""
            if str(got) != str(want):
                return False
        return True

    scores_by_mask: dict[int, float] = {}
    ranks_by_mask: dict[int, int] | None = {} if rank_column is not None else None
    for row in rows:
        if filters and not row_ok(row):
            continue

        mask = 0
        for i, col in enumerate(feature_columns):
            j = col_index[col]
            raw = row[j] if j < len(row) else "0"
            try:
                bit = int(raw)
            except Exception as exc:
                raise ValueError(f"Invalid 0/1 cell in feature column {col!r}: {raw!r}") from exc
            if bit not in (0, 1):
                raise ValueError(f"Invalid 0/1 cell in feature column {col!r}: {raw!r}")
            if bit:
                mask |= 1 << i

        raw_score = row[col_index[score_column]] if col_index[score_column] < len(row) else ""
        try:
            score_raw = float(raw_score)
        except Exception as exc:
            raise ValueError(f"Invalid score cell: {raw_score!r}") from exc
        score = _transform_score(score_raw, score_transform)

        if rank_column is not None:
            raw_rank = row[col_index[str(rank_column)]] if col_index[str(rank_column)] < len(row) else ""
            s = str(raw_rank).strip()
            if s == "":
                raise ValueError(f"Missing rank cell for mask={mask}: column={rank_column}")
            try:
                rank = int(float(s))
            except Exception as exc:
                raise ValueError(f"Invalid rank cell: {raw_rank!r}") from exc
            if rank <= 0:
                raise ValueError(f"Invalid rank (must be >=1): {rank} (mask={mask})")

        if mask in scores_by_mask and scores_by_mask[mask] != score:
            raise ValueError(f"Duplicate mask with conflicting score: mask={mask} {scores_by_mask[mask]} != {score}")
        scores_by_mask[mask] = score
        if ranks_by_mask is not None:
            if mask in ranks_by_mask and ranks_by_mask[mask] != rank:
                raise ValueError(f"Duplicate mask with conflicting rank: mask={mask} {ranks_by_mask[mask]} != {rank}")
            ranks_by_mask[mask] = int(rank)

    expected = 1 << n
    if 0 not in scores_by_mask and empty_score is not None:
        scores_by_mask[0] = _transform_score(float(empty_score), score_transform)
        if ranks_by_mask is not None:
            if empty_rank is None:
                raise ValueError(
                    "rank_column is set but empty coalition row is missing; provide empty_rank or include the empty row in the CSV."
                )
            ranks_by_mask[0] = int(empty_rank)

    if not allow_incomplete:
        if 0 not in scores_by_mask:
            raise ValueError(
                f"Missing empty coalition row (all-zero mask). Provide it in the CSV or set empty_score. "
                f"(observed rows={len(scores_by_mask)}, expected={expected})"
            )
        missing_masks = [m for m in range(expected) if m not in scores_by_mask]
        if missing_masks:
            raise ValueError(f"Missing coalitions: {len(missing_masks)} (expected={expected}, found={len(scores_by_mask)})")
        if ranks_by_mask is not None:
            missing_ranks = [m for m in range(expected) if m not in ranks_by_mask]
            if missing_ranks:
                raise ValueError(f"Missing ranks for coalitions: {len(missing_ranks)} (expected={expected}, found={len(ranks_by_mask)})")

    return ImportedGame(
        n=n,
        scores_by_mask=scores_by_mask,
        ranks_by_mask=ranks_by_mask,
        feature_columns=list(feature_columns),
        feature_descriptions={str(k): str(v) for k, v in dict(feature_descriptions).items()},
    )


def detect_feature_columns_from_csv(
    *,
    raw_csv: Path,
    score_column: str,
    filters: Mapping[str, str],
    feature_exclude: set[str],
) -> list[str]:
    """Detect 0/1 feature columns from a raw feature-mask table CSV.

    Keeps CSV column order and excludes known non-feature columns.
    """
    with raw_csv.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError("CSV is empty.") from exc
        rows = [r for r in reader if r]

    col_index = {str(name): i for i, name in enumerate(header)}
    if score_column not in col_index:
        raise ValueError(f"score_column not found: {score_column}")

    def row_ok(row: list[str]) -> bool:
        for k, want in filters.items():
            j = col_index.get(k)
            if j is None:
                return False
            got = row[j] if j < len(row) else ""
            if str(got) != str(want):
                return False
        return True

    # Candidate columns: everything except explicitly excluded and known meta columns.
    excluded = set(feature_exclude)
    excluded |= {"score", "rank", "abs_value", "metric", "n_train", "n_test", "seed", "order"}
    excluded |= {str(score_column)}

    candidates = [str(c) for c in header if str(c) not in excluded]
    if not candidates:
        raise ValueError("No candidate feature columns after exclusions.")

    # Filter rows before inspecting values.
    use_rows = [r for r in rows if (not filters or row_ok(r))]
    if not use_rows:
        raise ValueError("No rows left after applying filters.")

    features: list[str] = []
    for col in candidates:
        j = col_index.get(col)
        if j is None:
            continue
        seen: set[int] = set()
        ok = True
        for row in use_rows:
            raw = row[j] if j < len(row) else ""
            s = str(raw).strip()
            if s == "":
                continue
            try:
                v = int(s)
            except Exception:
                ok = False
                break
            if v not in (0, 1):
                ok = False
                break
            seen.add(v)
        if ok and seen:
            features.append(col)

    if not features:
        raise ValueError("No binary (0/1) feature columns detected.")
    return features


@click.command(name="import-game")
@click.argument("dataset_id", type=str)
@click.option("--inputs-root", type=click.Path(path_type=Path), default=None, help="Inputs root (default: inputs/feature_mask_tables).")
@click.option("--out", "out_root", type=click.Path(path_type=Path), default=None, help="Output root (default: outputs/real/<dataset_id>).")
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=None, help="Path to config.yaml.")
def import_game(dataset_id: str, inputs_root: Path | None, out_root: Path | None, config_path: Path | None) -> None:
    """Import inputs/feature_mask_tables/<dataset_id> into outputs/real/<dataset_id>/games/."""
    dataset_dir = resolve_dataset_dir(dataset_id, inputs_root=inputs_root)
    if not dataset_dir.exists():
        raise click.ClickException(f"dataset dir not found: {dataset_dir}")

    schema_path = dataset_dir / "schema.yaml"
    if not schema_path.exists():
        raise click.ClickException(f"schema.yaml not found: {schema_path}")

    try:
        schema = _load_schema_yaml(schema_path)
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    raw_name = str(schema.get("raw_csv", "raw.csv"))
    raw_csv = dataset_dir / raw_name
    if not raw_csv.exists():
        raise click.ClickException(f"raw CSV not found: {raw_csv}")

    score_column = str(schema.get("score_column", "value"))
    score_transform = str(schema.get("score_transform", "identity"))
    rank_column = schema.get("rank_column")
    rank_column_str = str(rank_column) if rank_column is not None else None
    rank_method = str(schema.get("rank_method", "binned"))
    feature_columns = schema.get("feature_columns")
    feature_exclude_raw = schema.get("feature_exclude", [])
    feature_exclude: set[str] = set()
    if isinstance(feature_exclude_raw, list):
        feature_exclude = {str(x) for x in feature_exclude_raw}
    if rank_column_str is not None:
        feature_exclude.add(rank_column_str)

    filters_raw = schema.get("filters", {})
    filters: dict[str, str] = {}
    if isinstance(filters_raw, dict):
        filters = {str(k): str(v) for k, v in filters_raw.items()}

    empty_score = None
    if "empty_score" in schema:
        try:
            empty_score = float(schema["empty_score"])
        except Exception as exc:
            raise click.ClickException(f"Invalid schema.yaml empty_score: {schema['empty_score']!r}") from exc

    empty_rank = None
    if "empty_rank" in schema:
        try:
            empty_rank = int(schema["empty_rank"])
        except Exception as exc:
            raise click.ClickException(f"Invalid schema.yaml empty_rank: {schema['empty_rank']!r}") from exc

    feature_desc_raw = schema.get("feature_descriptions", {})
    feature_desc: dict[str, str] = {}
    if isinstance(feature_desc_raw, dict):
        feature_desc = {str(k): str(v) for k, v in feature_desc_raw.items()}

    feature_labels_raw = schema.get("feature_labels", {})
    feature_labels: dict[str, str] = {}
    if isinstance(feature_labels_raw, dict):
        feature_labels = {str(k): str(v) for k, v in feature_labels_raw.items()}

    allow_incomplete = bool(schema.get("allow_incomplete", False))

    base_out = resolve_dataset_out_base(dataset_id, out_root=out_root, config_path=config_path)

    if isinstance(feature_columns, list) and feature_columns:
        feature_columns_list = [str(x) for x in feature_columns]
    else:
        try:
            feature_columns_list = detect_feature_columns_from_csv(
                raw_csv=raw_csv,
                score_column=score_column,
                filters=filters,
                feature_exclude=feature_exclude,
            )
        except Exception as exc:
            raise click.ClickException(str(exc)) from exc

    try:
        imported = import_feature_mask_csv(
            raw_csv=raw_csv,
            score_column=score_column,
            score_transform=score_transform,
            rank_column=rank_column_str,
            feature_columns=feature_columns_list,
            filters=filters,
            empty_score=empty_score,
            empty_rank=empty_rank,
            feature_descriptions=feature_desc,
            allow_incomplete=allow_incomplete,
        )
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    if imported.ranks_by_mask is not None:
        ranks = imported.ranks_by_mask
    else:
        method = str(rank_method or "binned").strip().lower()
        if method == "dense":
            ranks = _dense_rank_by_score(imported.scores_by_mask)
        elif method == "binned":
            cfg = load_config(config_path)
            bins = 5
            if isinstance(cfg, dict):
                real_cfg = cfg.get("realgen", {})
                if isinstance(real_cfg, dict) and "import_rank_bins" in real_cfg:
                    try:
                        bins = int(real_cfg.get("import_rank_bins", bins))
                    except Exception:
                        bins = 5
            ranks = _binned_rank_by_score(imported.scores_by_mask, bins=bins)
        else:
            raise click.ClickException(f"Unsupported rank_method: {rank_method!r} (supported: dense, binned)")
    out_path = base_out / "games" / f"game_{dataset_id}.csv"
    _write_game_csv(out_path=out_path, n=imported.n, scores_by_mask=imported.scores_by_mask, ranks_by_mask=ranks)
    write_feature_labels_yaml(
        out_path.with_suffix(".features.yaml"),
        feature_columns=imported.feature_columns,
        feature_descriptions=imported.feature_descriptions,
        feature_labels=feature_labels,
    )
    # Keep a copy of the import schema for traceability and as input to apply-rules defaults.
    try:
        (base_out / "schema.yaml").write_text(schema_path.read_text(encoding="utf-8"), encoding="utf-8")
    except Exception:
        pass
    click.echo(f"wrote game CSV to {out_path}")


__all__ = ["import_game", "import_feature_mask_csv"]
