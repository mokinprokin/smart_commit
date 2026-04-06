import os
from pathlib import Path
from .logger import logger

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def load_config() -> dict:
    """Загружает секцию [tool.smart_commit] из pyproject.toml."""
    config_path = Path(os.getcwd()) / "pyproject.toml"

    default_config = {
        "repository_url": "",
        "commands": [],
        "protected_branches": ["main", "master"],
    }

    if not config_path.exists():
        logger.warning("pyproject.toml не найден. Используются настройки по умолчанию.")
        return default_config

    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
            return data.get("tool", {}).get("smart_commit", default_config)
    except Exception as e:
        logger.error(f"Ошибка чтения конфига: {e}")
        return default_config
