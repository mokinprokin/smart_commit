from ..logger import Console, logger
from ..exceptions import SmartCommitError
from .git import GitService
from ..constants import (
    WORKFLOW_DIR,
    WORKFLOW_FILE,
    GITHUB_ACTION_TEMPLATE,
    CI_COMMIT_MESSAGE,
)


class CIService:
    @classmethod
    def generate_github_action(cls, commands: list[str], protected_branches: list[str]):
        """Generates a GitHub Actions workflow file dynamically based on pyproject.toml commands."""
        Console.info("⚙️ Generating GitHub Actions workflow...")

        branches_yaml = ", ".join(f'"{b}"' for b in protected_branches)

        if not commands:
            commands_yaml = (
                '        - run: echo "No commands defined in pyproject.toml"'
            )
        else:
            commands_yaml = "\n".join(
                f"        - name: Run '{cmd}'\n          run: {cmd}" for cmd in commands
            )

        workflow_content = GITHUB_ACTION_TEMPLATE.replace("__BRANCHES__", branches_yaml)
        workflow_content = workflow_content.replace("__COMMANDS__", commands_yaml)

        try:
            WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
            with open(WORKFLOW_FILE, "w", encoding="utf-8") as f:
                f.write(workflow_content)

            Console.success(f"GitHub Action successfully created at: {WORKFLOW_FILE}")
            logger.info("Generated GitHub Action workflow file.")

        except Exception as e:
            raise SmartCommitError(f"Failed to generate CI workflow: {e}")

    @classmethod
    def prompt_and_push(cls):
        """Asks the user if they want to instantly commit and push the new Action."""
        ans = (
            input("🚀 Do you want to commit and push this GitHub Action now? [y/N]: ")
            .strip()
            .lower()
        )
        if ans != "y":
            Console.info("Action saved locally. You can commit it manually later.")
            return

        try:
            branch = GitService.get_current_branch()

            GitService._run(["git", "add", str(WORKFLOW_FILE)])

            GitService.commit(CI_COMMIT_MESSAGE)
            Console.info(f"Committed: '{CI_COMMIT_MESSAGE}'")

            GitService.push_with_retry(branch)

        except Exception as e:
            raise SmartCommitError(f"Failed to push CI configuration: {e}")
