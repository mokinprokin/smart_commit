import argparse
import sys
from .services import (
    config as config_service,
    git as git_service,
    security as security_service,
    runner as runner_service,
)
from .services.logger import logger


def interactive_input(prompt: str, default: str = "") -> str:
    """Запрашивает ввод у пользователя, если флаг не передан."""
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value if value else default


def main():
    parser = argparse.ArgumentParser(description="Smart Git Commit Tool")
    parser.add_argument("-b", "--branch", help="Имя ветки")
    parser.add_argument("-m", "--message", help="Сообщение коммита")
    parser.add_argument("-r", "--remote", help="Remote (например, origin)")

    args = parser.parse_args()

    logger.info("Инициализация Smart Commit...")

    # 1. Сбор параметров (Fallback на интерактивный ввод)
    branch = args.branch or interactive_input("Введите имя ветки")
    message = args.message or interactive_input("Введите сообщение коммита")
    remote = args.remote or interactive_input("Введите remote", default="origin")

    if not branch or not message:
        logger.error("Ветка и сообщение коммита обязательны!")
        sys.exit(1)

    # 2. Загрузка конфига
    config = config_service.load_config()

    # 3. Валидация ветки
    git_service.check_protected(branch, config.get("protected_branches", []))
    git_service.ensure_branch(branch)

    # 4. Добавление файлов в индекс (чтобы сканер секретов увидел их)
    git_service.add_all()

    # 5. Секьюрити чек
    staged_files = git_service.get_staged_files()
    if not staged_files:
        logger.warning("Нет изменений для коммита.")
        sys.exit(0)

    if security_service.check_secrets(staged_files):
        # Удаляем из индекса файлы, которые только что попали в gitignore
        git_service.run_cmd(["git", "rm", "-r", "--cached", "."])
        git_service.add_all()

    # 6. Запуск кастомных команд (ruff, тесты и т.д.)
    runner_service.run_pre_commands(config.get("commands", []))

    # 7. Финализация (Commit & Push)
    git_service.commit(message)
    git_service.push(remote, branch)

    logger.success("Smart Commit завершил работу!")


if __name__ == "__main__":
    main()
