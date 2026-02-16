import requests
from utils.env_loader import get_env

TG_CHANNEL_ID = get_env("TG_CHANNEL_ID", "")
TB_BOT_TOKEN = get_env("TB_BOT_TOKEN", "")
TG_LOGS_ID = get_env("TG_LOGS_ID", "")
TG_LOGS_TOKEN = get_env("TG_LOGS_TOKEN", "")

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TB_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHANNEL_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, json=payload)


# Logs
def send_telegram_logs(message):
    url = f"https://api.telegram.org/bot{TG_LOGS_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_LOGS_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, json=payload) 