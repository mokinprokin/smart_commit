import subprocess
import sys
from .logger import logger


def run_cmd(cmd: list[str], check=True) -> str:
    """Выполняет bash-команду и возвращает вывод."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        logger.error(f"Ошибка Git: {result.stderr.strip()}")
        sys.exit(1)
    return result.stdout.strip()


def check_protected(branch: str, protected_branches: list[str]):
    """Блокирует пуш в защищенные ветки."""
    if branch in protected_branches:
        logger.error(f"Прямой коммит в защищенную ветку '{branch}' запрещен!")
        sys.exit(1)


def ensure_branch(branch: str):
    """Проверяет наличие ветки. Если нет - создает."""
    result = subprocess.run(["git", "checkout", branch], capture_output=True, text=True)
    if result.returncode != 0:
        logger.info(f"Ветка '{branch}' не найдена. Создаю новую...")
        run_cmd(["git", "checkout", "-b", branch])
    else:
        logger.info(f"Переключено на ветку '{branch}'.")


def add_all():
    run_cmd(["git", "add", "."])
    logger.info("Файлы добавлены в индекс (git add).")


def get_staged_files() -> list[str]:
    """Возвращает список файлов, готовых к коммиту."""
    output = run_cmd(["git", "diff", "--cached", "--name-only"])
    return [f for f in output.split("\n") if f]


def commit(message: str):
    run_cmd(
        ["git", "commit", "-m", message], check=False
    )  # check=False, чтобы обработать "nothing to commit"
    logger.info(f"Коммит создан: '{message}'")


def push(remote: str, branch: str):
    logger.info(f"Отправка изменений в {remote}/{branch}...")
    run_cmd(["git", "push", "-u", remote, branch])
    logger.success("Push успешно завершен!")
