import subprocess
import sys
from pathlib import Path

# Поддержка TOML
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def run_shell(command, silent=False):
    """Выполняет консольную команду."""
    if not silent:
        print(f"🛠  Выполняю: {command}")
    result = subprocess.run(command, shell=True, capture_output=silent, text=True)
    return result


def ensure_gitignore():
    """Создает стандартный .gitignore для Python, если он отсутствует."""
    if not Path(".gitignore").exists():
        print("📝 .gitignore не найден. Создаю стандартный для Python...")
        content = "__pycache__/\n*.py[cod]\n*$py.class\n.venv/\nvenv/\n.env\n.vscode/\ndist/\nbuild/\n*.egg-info/\n"
        with open(".gitignore", "w", encoding="utf-8") as f:
            f.write(content)


def get_config():
    path = Path("pyproject.toml")
    if not path.exists():
        print("❌ Ошибка: pyproject.toml не найден. Запустите команду в корне проекта.")
        sys.exit(1)

    with open(path, "rb") as f:
        data = tomllib.load(f)
        return data.get("tool", {}).get("smart_commit", {})


def ensure_git_setup(expected_url):
    """Проверяет наличие Git и настраивает remote, если нужно."""
    if not Path(".git").exists():
        print("📁 Git не найден. Инициализирую репозиторий...")
        run_shell("git init")

    res = run_shell("git remote get-url origin", silent=True)
    current_url = res.stdout.strip()

    if res.returncode != 0:
        print(f"🔗 Добавляю remote origin: {expected_url}")
        run_shell(f"git remote add origin {expected_url}")
    elif expected_url not in current_url:
        print(f"🔄 Обновляю URL репозитория на: {expected_url}")
        run_shell(f"git remote set-url origin {expected_url}")
    else:
        print("✅ Git репозиторий и remote настроены корректно.")


def main():
    config = get_config()
    repo_url = config.get("repository_url")
    commands = config.get("commands", [])

    if not repo_url:
        print(
            "❌ Ошибка: В pyproject.toml не указан [tool.smart_commit].repository_url"
        )
        sys.exit(1)

    ensure_git_setup(repo_url)
    ensure_gitignore()

    print("\n--- 🚀 SMART COMMIT PRE-CHECK ---")
    branch = input("🌿 Название ветки (например, main): ").strip()
    message = input("📝 Сообщение коммита: ").strip()

    if not branch or not message:
        print("❌ Ошибка: Ветка и сообщение не могут быть пустыми.")
        sys.exit(1)

    run_shell(f"git checkout -B {branch}", silent=True)

    print("\n--- 🛠 ЗАПУСК ПРОВЕРОК ---")
    for cmd in commands:
        if run_shell(cmd).returncode != 0:
            print(f"\n🛑 Проверка '{cmd}' провалена. Исправь ошибки!")
            sys.exit(1)

    print("\n--- ✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ. ПУШИМ... ---")

    success = (
        run_shell("git add .").returncode == 0
        and run_shell(f'git commit -m "{message}"').returncode == 0
        and run_shell(f"git push -u origin {branch}").returncode == 0
    )

    if success:
        print(f"\n🎉 Победа! Код проверен и улетел в ветку '{branch}'.")
    else:
        print("\n❌ Упс! Что-то пошло не так при отправке в Git.")


if __name__ == "__main__":
    main()
