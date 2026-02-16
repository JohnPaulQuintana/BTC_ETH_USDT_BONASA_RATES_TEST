import gspread
from oauth2client.service_account import ServiceAccountCredentials
from utils.env_loader import get_env


def get_gspread_client():
    """Return gspread client using service account from split .env vars"""

    service_account_info = {
        "type": get_env("TYPE"),
        "project_id": get_env("PROJECT_ID"),
        "private_key_id": get_env("PRIVATE_KEY_ID"),
        "private_key": get_env("PRIVATE_KEY").replace("\\n", "\n"),  # important!
        "client_email": get_env("CLIENT_EMAIL"),
        "client_id": get_env("CLIENT_ID"),
        "auth_uri": get_env("AUTH_URI"),
        "token_uri": get_env("TOKEN_URI"),
        "auth_provider_x509_cert_url": get_env("AUTH_PROVIDER_CERT_URL"),
        "client_x509_cert_url": get_env("CLIENT_CERT_URL"),
        "universe_domain": get_env("UNIVERSE_DOMAIN"),
    }

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
    return gspread.authorize(creds)
