"""Loads and deep-merges the YAML config layers (config/default.yaml + config/<env>.yaml)."""
import os
import re
from pathlib import Path
from typing import Any, Dict

import yaml

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"

_ENV_VAR_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _interpolate_env(value: Any) -> Any:
    """Recursively replaces ${VAR_NAME} placeholders in strings with env var values."""
    if isinstance(value, str):
        return _ENV_VAR_PATTERN.sub(lambda m: os.getenv(m.group(1), m.group(0)), value)
    if isinstance(value, dict):
        return {k: _interpolate_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_interpolate_env(v) for v in value]
    return value


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Merges `override` into `base`, recursing into nested dicts. Lists/scalars are replaced."""
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_yaml_file(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open("r") as f:
        data = yaml.safe_load(f) or {}
    return data


def load_yaml_config(env: str = "development", config_dir: Path = CONFIG_DIR) -> Dict[str, Any]:
    """
    Loads config/default.yaml, deep-merges config/<env>.yaml on top (if present),
    then interpolates ${ENV_VAR} placeholders. Returns the merged dict.
    """
    base = _load_yaml_file(config_dir / "default.yaml")
    override = _load_yaml_file(config_dir / f"{env}.yaml")
    merged = _deep_merge(base, override)
    return _interpolate_env(merged)
