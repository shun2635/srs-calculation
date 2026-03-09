from __future__ import annotations

from srs_calculation.infrastructure.config import get_realgen_import_rank_bins, load_yaml_config


def test_load_yaml_config_returns_empty_mapping_without_explicit_path(tmp_path, monkeypatch) -> None:
    (tmp_path / "config.yaml").write_text("output_base: ignored\n", encoding="utf-8")
    legacy_dir = tmp_path / "legacy"
    legacy_dir.mkdir(parents=True, exist_ok=True)
    (legacy_dir / "config.yaml").write_text("output_base: ignored-legacy\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    config = load_yaml_config(None)

    assert config == {}


def test_load_yaml_config_reads_explicit_path_only(tmp_path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("output_base: configured\nfigures:\n  png_dpi: 123\n", encoding="utf-8")

    config = load_yaml_config(config_path)

    assert config["output_base"] == "configured"
    assert config["figures"] == {"png_dpi": 123}


def test_get_realgen_import_rank_bins_uses_default_without_explicit_path(tmp_path, monkeypatch) -> None:
    (tmp_path / "config.yaml").write_text("realgen:\n  import_rank_bins: 99\n", encoding="utf-8")
    legacy_dir = tmp_path / "legacy"
    legacy_dir.mkdir(parents=True, exist_ok=True)
    (legacy_dir / "config.yaml").write_text("realgen:\n  import_rank_bins: 77\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    value = get_realgen_import_rank_bins(None, default=5)

    assert value == 5


def test_get_realgen_import_rank_bins_reads_explicit_path(tmp_path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("realgen:\n  import_rank_bins: 7\n", encoding="utf-8")

    value = get_realgen_import_rank_bins(config_path, default=5)

    assert value == 7
