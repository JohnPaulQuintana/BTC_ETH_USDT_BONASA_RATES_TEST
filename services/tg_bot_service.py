import requests
from utils.env_loader import get_env

TG_CHANNEL_ID = get_env("TG_CHANNEL_ID", "")
TB_BOT_TOKEN = get_env("TB_BOT_TOKEN", "")
TG_LOGS_ID = get_env("TG_LOGS_ID", "")
TG_LOGS_TOKEN = get_env("TG_LOGS_TOKEN", "")
INTERNAL_SECRET = "dev_secret_key"  # same as in your Vercel env
API_URL = "https://tg-alert-api.vercel.app/api/tg-alert"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TB_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHANNEL_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, json=payload)


# Logs
# def send_telegram_logs(message):
#     url = f"https://api.telegram.org/bot{TG_LOGS_TOKEN}/sendMessage"
#     payload = {
#         "chat_id": TG_LOGS_ID,
#         "text": message,
#         "parse_mode": "HTML"
#     }
#     requests.post(url, json=payload) 

def send_telegram_logs(message=None):
    """
    Sends a log message to Telegram via the Vercel API.
    Safe for automation scripts — will never raise an exception.
    """
    try:
        payload = {"message": message} if message else {}
        headers = {"x-api-key": INTERNAL_SECRET}

        response = requests.post(API_URL, json=payload, headers=headers, timeout=5)

        # Optional: print only for debugging
        if response.status_code != 200:
            print(f"[WARNING] Telegram log failed: {response.status_code} {response.text}")

    except requests.RequestException as e:
        # Catch network errors, timeouts, etc.
        print(f"[ERROR] Telegram log error: {e}")

    except Exception as e:
        # Catch all other unexpected errors
        print(f"[ERROR] Unexpected error while sending Telegram log: {e}")
