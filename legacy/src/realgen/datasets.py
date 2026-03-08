"""Dataset path resolution for realgen."""

from __future__ import annotations

from pathlib import Path

from gamegen.config import Defaults, load_config


def default_inputs_root() -> Path:
    return Path("inputs") / "feature_mask_tables"


def resolve_dataset_dir(dataset_id: str, *, inputs_root: Path | None = None) -> Path:
    root = Path(inputs_root) if inputs_root is not None else default_inputs_root()
    return root / str(dataset_id)


def resolve_dataset_out_base(dataset_id: str, *, out_root: Path | None, config_path: Path | None) -> Path:
    cfg = load_config(config_path)
    defaults = Defaults()
    base_outputs = Path(str(cfg.get("output_base", defaults.output_base))) / "real"
    root = Path(out_root) if out_root is not None else base_outputs
    # If user points directly to a dataset directory, keep it; otherwise append dataset_id.
    return root if root.name == str(dataset_id) else root / str(dataset_id)


__all__ = ["resolve_dataset_dir", "resolve_dataset_out_base"]

