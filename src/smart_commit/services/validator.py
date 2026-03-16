import subprocess
import re
from ..exceptions import ValidationError
from ..logger import Console, logger


class ValidatorService:
    @classmethod
    def check_conventional_commit(cls, message: str):
        """Validates message against Conventional Commits standard."""
        pattern = r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?:\s.+"
        if not re.match(pattern, message):
            logger.warning(f"Non-conventional commit message: {message}")
            Console.warning(
                "Commit message does not follow Conventional Commits (e.g., 'feat: add auth')."
            )

    @classmethod
    def run_commands(cls, commands: list[str]):
        """Runs pre-commit pipeline commands (linters, tests)."""
        for cmd in commands:
            Console.info(f"Executing: {cmd}")
            logger.info(f"Running validation command: {cmd}")
            res = subprocess.run(cmd, shell=True)
            if res.returncode != 0:
                raise ValidationError(
                    f"Pipeline failed at: '{cmd}'. Please fix the issues!"
                )
