# utils/logger.py
import sys

class Logger:
    COLORS = {
        "reset": "\033[0m",
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
    }

    LINE = "-" * 70  # horizontal separator

    @staticmethod
    def info(msg: str):
        print(f"{Logger.COLORS['blue']}[INFO]{Logger.COLORS['reset']} {msg}\n{Logger.LINE}\n")

    @staticmethod
    def success(msg: str):
        print(f"{Logger.COLORS['green']}[SUCCESS]{Logger.COLORS['reset']} {msg}\n{Logger.LINE}\n")

    @staticmethod
    def warn(msg: str):
        print(f"{Logger.COLORS['yellow']}[WARN]{Logger.COLORS['reset']} {msg}\n{Logger.LINE}\n")

    @staticmethod
    def error(msg: str):
        print(f"{Logger.COLORS['red']}[ERROR]{Logger.COLORS['reset']} {msg}\n{Logger.LINE}\n", file=sys.stderr)
