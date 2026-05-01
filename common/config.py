from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

import yaml

DEFAULT_CONFIG_PATHS = [Path("config.yaml")]


def find_config_file() -> Path:
    explicit = os.getenv("CONFIG_FILE_PATH")
    print(f"Explicit config path? : {explicit}")

    if explicit:
        explicit_path = Path(explicit)
        if explicit_path.exists():
            return explicit_path
        raise FileNotFoundError(
            f"Config file path set by CONFIG_FILE_PATH does not exist: {explicit_path}"
        )

    for candidate in DEFAULT_CONFIG_PATHS:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "Config file not found. Checked: "
        + ", ".join(str(p) for p in DEFAULT_CONFIG_PATHS)
    )


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    config_path = Path(path) if path else find_config_file()
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_bootstrap_servers(
    config: Mapping[str, Any], default: str = "localhost:9092"
) -> str:
    return os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS", config.get("KAFKA_BOOTSTRAP_SERVERS", default)
    )
