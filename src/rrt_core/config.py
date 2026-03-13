from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CDE_CONFIG_PATH = ROOT / "config" / "crisis_thresholds.yaml"
DEFAULT_TOI_CONFIG_PATH = ROOT / "config" / "toi_otoi.yaml"


def load_yaml(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping config in {config_path}")
    return data
