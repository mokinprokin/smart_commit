import subprocess
from pathlib import Path
from ..logger import Console, logger
from ..constants import GITIGNORE_FILE, BASE_GITIGNORE, EXCLUDED_SCAN_DIRS


class SecurityService:
    @classmethod
    def ensure_gitignore(cls):
        """Ensures .gitignore exists or creates a secure default."""
        if not GITIGNORE_FILE.exists():
            Console.warning(
                f"{GITIGNORE_FILE.name} not found. Creating a secure default configuration..."
            )
            with open(GITIGNORE_FILE, "w", encoding="utf-8") as f:
                f.write(BASE_GITIGNORE.lstrip())
            logger.info("Created default .gitignore")

    @classmethod
    def check_env_leaks(cls):
        """
        Scans for .env files (e.g. .env.local, .test.env, prod.env)
        and uses Git to check if they are ignored.
        Prevents accidental leaks of secrets.
        """
        Console.info("🛡️ Scanning for potential secret leaks (.env files)...")

        raw_files = set(Path(".").rglob(".env*")) | set(Path(".").rglob("*.env"))

        env_files = [
            f
            for f in raw_files
            if f.is_file() and not any(part in EXCLUDED_SCAN_DIRS for part in f.parts)
        ]

        leaked_files = []

        for env_file in env_files:
            res = subprocess.run(
                ["git", "check-ignore", "-q", str(env_file)], capture_output=True
            )
            if res.returncode == 1:
                leaked_files.append(str(env_file))

        if leaked_files:
            Console.error(
                f"CRITICAL SECURITY RISK: .env files found that are NOT in {GITIGNORE_FILE.name}!"
            )
            for lf in leaked_files:
                print(f"  👉 {lf}")

            ans = (
                input(
                    f"🛑 Add these files to {GITIGNORE_FILE.name} automatically? [Y/n]: "
                )
                .strip()
                .lower()
            )
            if ans != "n":
                with open(GITIGNORE_FILE, "a", encoding="utf-8") as f:
                    f.write("\n# Auto-added by Smart Commit to prevent leaks\n")
                    for lf in leaked_files:
                        f.write(f"{lf}\n")
                Console.success(f"Files successfully added to {GITIGNORE_FILE.name}.")
            else:
                Console.warning(
                    "Action declined. Please be careful: secrets might be pushed!"
                )
