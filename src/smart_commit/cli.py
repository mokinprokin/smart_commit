import argparse
import sys
from .exceptions import SmartCommitError
from .config import ConfigService
from .services.security import SecurityService
from .services.git import GitService
from .services.validator import ValidatorService
from .services.ci import CIService
from .logger import Console, logger
from .constants import TOOL_NAME, DEFAULT_PROTECTED_BRANCHES


def run_ci_generation_flow():
    """Dedicated flow for 'smart-commit generate-action' command."""
    logger.info("=== CI Generation Flow Started ===")
    config = ConfigService.load_or_create()
    commands = config.get("commands", [])
    protected_branches = config.get("protected_branches", DEFAULT_PROTECTED_BRANCHES)

    GitService.ensure_repo()

    CIService.generate_github_action(commands, protected_branches)
    CIService.prompt_and_push()

    sys.exit(0)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "generate-action":
        try:
            run_ci_generation_flow()
        except SmartCommitError as e:
            Console.error(str(e))
            sys.exit(1)
        except KeyboardInterrupt:
            Console.warning("\nProcess interrupted by user.")
            sys.exit(0)

    parser = argparse.ArgumentParser(description=TOOL_NAME)
    parser.add_argument("-b", "--branch", help="Specify target branch")
    parser.add_argument("-m", "--message", help="Commit message")
    args = parser.parse_args()

    try:
        logger.info("=== Smart Commit Process Started ===")

        config = ConfigService.load_or_create()
        protected_branches = config.get(
            "protected_branches", DEFAULT_PROTECTED_BRANCHES
        )
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

        has_changes = GitService.has_any_changes()
        message = args.message

        if has_changes:
            if not message:
                message = input("📝 Enter commit message: ").strip()
            if not message:
                raise SmartCommitError("Commit message cannot be empty.")

            ValidatorService.check_conventional_commit(message)

        if commands:
            Console.info("--- 🛠 RUNNING PIPELINE (from pyproject.toml) ---")
            ValidatorService.run_commands(commands)

        Console.info("--- 🚀 FINALIZING WORKFLOW ---")

        if has_changes:
            GitService.smart_stage()
            GitService.commit(message)
        else:
            Console.info(
                "Working directory is clean. Skipping commit phase and proceeding to push."
            )

        GitService.push_with_retry(branch)

    except SmartCommitError as e:
        Console.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        Console.warning("\nProcess interrupted by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
