import argparse
import sys
from .exceptions import SmartCommitError
from .config import ConfigService
from .services.security import SecurityService
from .services.git import GitService
from .services.validator import ValidatorService
from .logger import Console, logger


def main():
    parser = argparse.ArgumentParser(description="Smart Commit & Push Tool")
    parser.add_argument("-b", "--branch", help="Specify target branch")
    parser.add_argument("-m", "--message", help="Commit message")
    args = parser.parse_args()

    try:
        logger.info("=== Smart Commit Process Started ===")

        config = ConfigService.load_or_create()
        protected_branches = config.get("protected_branches", ["main", "master"])
        commands = config.get("commands", [])

        GitService.ensure_repo()
        SecurityService.ensure_gitignore()
        SecurityService.check_env_leaks()

        current_branch = GitService.get_current_branch()
        branch = args.branch or current_branch
        GitService.switch_branch(branch)
        if branch in protected_branches:
            Console.warning(
                f"You are pushing directly to a protected branch: '{branch}'."
            )
            ans = input("Are you sure you want to continue? [y/N]: ").strip().lower()
            if ans != "y":
                raise SmartCommitError("Operation cancelled by user.")

        message = args.message
        if not message:
            message = input("📝 Enter commit message: ").strip()

        if not message:
            raise SmartCommitError("Commit message cannot be empty.")

        ValidatorService.check_conventional_commit(message)
        if commands:
            Console.info("--- 🛠 RUNNING PIPELINE (from pyproject.toml) ---")
            ValidatorService.run_commands(commands)

        Console.info("--- 🚀 FINALIZING COMMIT ---")
        GitService.smart_stage()
        GitService.commit(message)
        GitService.push_with_retry(branch)

    except SmartCommitError as e:
        Console.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        Console.warning("\nProcess interrupted by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
