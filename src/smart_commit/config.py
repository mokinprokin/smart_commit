import sys
from .exceptions import SmartCommitError
from .logger import Console, logger
from .constants import PYPROJECT_FILE, DEFAULT_TOML_CONFIG

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


class ConfigService:
    @classmethod
    def load_or_create(cls) -> dict:
        """Reads configuration. If the section is missing, appends default settings."""
        if not PYPROJECT_FILE.exists():
            Console.warning(f"{PYPROJECT_FILE.name} not found. Creating a base file...")
            PYPROJECT_FILE.touch()

        try:
            with open(PYPROJECT_FILE, "rb") as f:
                data = tomllib.load(f)
        except Exception as e:
            raise SmartCommitError(f"Failed to parse {PYPROJECT_FILE.name}: {e}")

        config = data.get("tool", {}).get("smart_commit")

        if config is None:
            Console.info(
                "Section [tool.smart_commit] not found. Generating default pipeline..."
            )
            logger.info(f"Appending default tool.smart_commit to {PYPROJECT_FILE.name}")

            with open(PYPROJECT_FILE, "a", encoding="utf-8") as f:
                f.write(DEFAULT_TOML_CONFIG)

            with open(PYPROJECT_FILE, "rb") as f:
                data = tomllib.load(f)
            config = data.get("tool", {}).get("smart_commit", {})

        return config
