import logging
from colorama import init, Fore, Style

init(autoreset=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("SmartCommit")


class Console:
    @staticmethod
    def info(msg: str):
        print(f"{Fore.CYAN}ℹ️  {msg}")
        logger.info(msg)

    @staticmethod
    def success(msg: str):
        print(f"{Fore.GREEN}{Style.BRIGHT}✅ {msg}")
        logger.info(f"SUCCESS: {msg}")

    @staticmethod
    def warning(msg: str):
        print(f"{Fore.YELLOW}⚠️  {msg}")
        logger.warning(msg)

    @staticmethod
    def error(msg: str):
        print(f"{Fore.RED}{Style.BRIGHT}❌ {msg}")
        logger.error(msg)
