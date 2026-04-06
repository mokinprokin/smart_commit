import os
import re
import sys
from .logger import logger

SECRET_PATTERNS = [
    re.compile(
        r'(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*["\'][a-zA-Z0-9\-_]{10,}["\']'
    ),
    re.compile(r"-----BEGIN (RSA|OPENSSH|PRIVATE) KEY-----"),
]

SUSPICIOUS_FILES = [".env", ".env.local", "secrets.json"]


def check_secrets(staged_files: list[str]) -> bool:
    """
    Проверяет файлы на наличие секретов.
    Возвращает True, если был изменен .gitignore (требуется повторный git add).
    """
    secrets_found = []

    for file_path in staged_files:
        if not os.path.exists(file_path):
            continue

        file_name = os.path.basename(file_path)

        if file_name in SUSPICIOUS_FILES:
            secrets_found.append(file_path)
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if any(pattern.search(content) for pattern in SECRET_PATTERNS):
                    secrets_found.append(file_path)
        except UnicodeDecodeError:
            pass

    if not secrets_found:
        return False

    logger.warning("ОБНАРУЖЕНЫ ВОЗМОЖНЫЕ УТЕЧКИ СЕКРЕТОВ!")
    for s in secrets_found:
        logger.warning(f" -> {s}")

    answer = input("Добавить эти файлы в .gitignore? [y/N]: ").strip().lower()
    if answer == "y":
        with open(".gitignore", "a", encoding="utf-8") as f:
            f.write("\n# Auto-added by Smart Commit\n")
            for s in secrets_found:
                f.write(f"{s}\n")

        logger.success("Файлы добавлены в .gitignore.")
        return True

    logger.error("Коммит прерван из-за угрозы безопасности. Очистите секреты вручную.")
    sys.exit(1)
