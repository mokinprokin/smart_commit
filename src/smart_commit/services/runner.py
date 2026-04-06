import subprocess
import sys
from .logger import logger


def run_pre_commands(commands: list[str]):
    """Запускает команды из конфига перед коммитом."""
    if not commands:
        return

    logger.info("Запуск pre-commit команд...")
    for cmd in commands:
        logger.info(f"Выполнение: {cmd}")
        result = subprocess.run(cmd, shell=True)

        if result.returncode != 0:
            logger.error(f"Команда '{cmd}' завершилась с ошибкой!")
            sys.exit(1)

    logger.success("Все pre-commit команды выполнены успешно.")
