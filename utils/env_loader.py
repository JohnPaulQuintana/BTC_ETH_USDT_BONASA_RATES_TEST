import os
from dotenv import load_dotenv

load_dotenv()

def get_env(key: str, default: str = None) -> str:
    return os.getenv(key, default)
