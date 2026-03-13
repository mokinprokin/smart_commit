import subprocess
import sys
import argparse
from pathlib import Path
from typing import Any
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored output
init(autoreset=True)

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


class SmartCommitError(Exception):
    """Base class for script-related errors."""

    pass


def run_cmd(
    cmd: list[str] | str, silent: bool = False, use_shell: bool = False
) -> subprocess.CompletedProcess[str]:
    """
    Executes a shell command.
    Prefer passing a list of arguments (use_shell=False) for internal git commands.
    """
    if not silent:
        display_cmd = cmd if isinstance(cmd, str) else " ".join(cmd)
        print(f"{Fore.CYAN}🛠  Executing: {Style.BRIGHT}{display_cmd}")

    result = subprocess.run(cmd, shell=use_shell, capture_output=silent, text=True)
    return result


def ensure_gitignore() -> None:
    """Creates a standard .gitignore for Python if it doesn't exist."""
    if not Path(".gitignore").exists():
        print(f"{Fore.YELLOW}📝 .gitignore not found. Creating a standard one...")
        content = (
            "__pycache__/\n*.py[cod]\n*$py.class\n.venv/\nvenv/\n"
            ".env\n.vscode/\ndist/\nbuild/\n*.egg-info/\n"
        )
        with open(".gitignore", "w", encoding="utf-8") as f:
            f.write(content)


def get_config() -> dict[str, Any]:
    """Reads configuration from pyproject.toml."""
    path = Path("pyproject.toml")
    if not path.exists():
        raise SmartCommitError(
            "pyproject.toml not found. Please run the command in the project root."
        )

    with open(path, "rb") as f:
        data = tomllib.load(f)
        return data.get("tool", {}).get("smart_commit", {})


def ensure_git_setup(expected_url: str) -> None:
    """Checks and configures Git repository and remote."""
    if not Path(".git").exists():
        print(f"{Fore.YELLOW}📁 Git not initialized. Initializing repository...")
        run_cmd(["git", "init"])

    res = run_cmd(["git", "remote", "get-url", "origin"], silent=True)
    current_url = res.stdout.strip()

    if res.returncode != 0:
        print(f"{Fore.CYAN}🔗 Adding remote origin: {expected_url}")
        run_cmd(["git", "remote", "add", "origin", expected_url])
    elif expected_url not in current_url:
        print(f"{Fore.YELLOW}🔄 Updating repository URL to: {expected_url}")
        run_cmd(["git", "remote", "set-url", "origin", expected_url])
    else:
        print(f"{Fore.GREEN}✅ Git repository is correctly configured.")


def switch_branch(branch: str) -> None:
    """Safely switches branches, handling unborn (empty) repositories."""
    has_commits = run_cmd(["git", "rev-parse", "HEAD"], silent=True).returncode == 0

    if not has_commits:
        run_cmd(["git", "branch", "-M", branch], silent=True)
    else:
        run_cmd(["git", "checkout", "-B", branch], silent=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Smart Commit & Push Tool")
    parser.add_argument("-b", "--branch", help="Specify branch (skips prompt)")
    parser.add_argument("-m", "--message", help="Commit message (skips prompt)")
    args = parser.parse_args()

    try:
        config = get_config()
        repo_url = config.get("repository_url")
        commands: list[str] = config.get("commands", [])
        protected_branches = config.get(
            "protected_branches", ["main", "master", "prod", "production"]
        )

        if not repo_url:
            raise SmartCommitError(
                "In pyproject.toml, [tool.smart_commit].repository_url is missing."
            )

        ensure_git_setup(repo_url)
        ensure_gitignore()

        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}--- 🚀 SMART COMMIT PRE-CHECK ---")

        branch = args.branch
        if not branch:
            current_branch = run_cmd(
                ["git", "branch", "--show-current"], silent=True
            ).stdout.strip()

            if current_branch:
                user_input = input(f"{Fore.BLUE}🌿 Branch [{current_branch}]: ").strip()
                branch = user_input if user_input else current_branch
            else:
                branch = input(f"{Fore.BLUE}🌿 Branch name (e.g., main): ").strip()

        message = args.message
        if not message:
            message = input(f"{Fore.BLUE}📝 Commit message: ").strip()

        if not branch or not message:
            raise SmartCommitError("Branch and message cannot be empty.")

        if branch in protected_branches:
            print(
                f"\n{Fore.RED}{Style.BRIGHT}⚠️  WARNING: You are pushing directly to a protected branch: '{branch}'."
            )
            choice = (
                input(
                    f"{Fore.YELLOW}Continue? [y (yes) / n (cancel) / b (create new branch)]: "
                )
                .lower()
                .strip()
            )

            if choice == "n":
                raise SmartCommitError("Operation cancelled by user.")
            elif choice == "b":
                new_branch = input(f"{Fore.BLUE}Enter new branch name: ").strip()
                if not new_branch:
                    raise SmartCommitError("Branch name cannot be empty.")
                branch = new_branch
                print(f"{Fore.CYAN}🌿 Switching to new branch '{branch}'...")
            elif choice != "y":
                raise SmartCommitError("Invalid input. Operation cancelled.")

        switch_branch(branch)

        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}--- 🛠 RUNNING VALIDATIONS ---")
        for cmd in commands:
            if run_cmd(cmd, use_shell=True).returncode != 0:
                raise SmartCommitError(
                    f"Validation failed for: '{cmd}'. Please fix the issues and try again!"
                )

        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}--- ✅ ALL CHECKS PASSED. PUSHING... ---")

        if run_cmd(["git", "add", "."]).returncode != 0:
            raise SmartCommitError("Error occurred during 'git add'.")

        if run_cmd(["git", "commit", "-m", message]).returncode != 0:
            print(f"{Fore.YELLOW}ℹ️  No changes to commit or commit error occurred.")

        print(f"{Fore.CYAN}📤 Pushing changes to {Style.BRIGHT}{branch}...")
        push_res = run_cmd(["git", "push", "-u", "origin", branch], silent=True)

        if push_res.returncode == 0:
            print(
                f"\n{Fore.GREEN}{Style.BRIGHT}🎉 Success! Code validated and pushed to '{branch}'."
            )
            return

        print(f"{Fore.YELLOW}⚠️  Push rejected. Remote changes detected.")
        print(f"{Fore.CYAN}📥 Synchronizing (pull --rebase)...")

        pull_res = run_cmd(["git", "pull", "origin", branch, "--rebase"], silent=True)

        if pull_res.returncode != 0:
            raise SmartCommitError(
                "🛑 Conflict detected during pull!\n"
                "Please resolve conflicts manually (git rebase --continue) and run the script again."
            )

        print(f"{Fore.GREEN}🔄 Sync successful. Retrying push...")
        push_res_retry = run_cmd(["git", "push", "-u", "origin", branch])

        if push_res_retry.returncode == 0:
            print(
                f"\n{Fore.GREEN}{Style.BRIGHT}🎉 Success! Changes synchronized and pushed to '{branch}'."
            )
        else:
            raise SmartCommitError("Failed to push changes after rebase.")

    except SmartCommitError as e:
        print(f"\n{Fore.RED}{Style.BRIGHT}❌ Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Process interrupted by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
