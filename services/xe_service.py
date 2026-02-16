import httpx
from utils.env_loader import get_env
import logging

XE_URL = get_env("XE_URL", "https://www.xe.com/api/protected/midmarket-converter/")
XE_AUTH = get_env("XE_AUTH", "Basic bG9kZXN0YXI6cHVnc25heA==")
XE_CURRENCIES = get_env("XE_CURRENCIES", "BDT,PKR,INR,NPR").split(",")

logger = logging.getLogger(__name__)

async def fetch_xe_rates() -> dict:
    """
    Fetch filtered XE mid-market rates (USD → selected currencies).
    Returns a dict with:
        - status: "success" or "error"
        - data: filtered rates dict on success
        - error: error message on failure
    """
    headers = {
        "Authorization": XE_AUTH,
        "Referer": "https://www.xe.com/currencyconverter/convert/",
        "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "user-agent": (
            "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/139.0.0.0 Mobile Safari/537.36"
        ),
        "accept": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(XE_URL, headers=headers)
            response.raise_for_status()
            data = response.json()

            # Filter only requested currencies
            rates = data.get("rates", {})
            filtered = {cur: rates.get(cur) for cur in XE_CURRENCIES if cur in rates}

            logger.info("Fetched XE rates successfully")
            return {"status": "success", "data": {"rates": filtered}, "error": None}

    except httpx.ConnectError as e:
        logger.error(f"Connection error fetching XE rates: {e}")
        return {"status": "error", "data": None, "error": str(e)}
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching XE rates: {e.response.status_code} - {e.response.text}")
        return {"status": "error", "data": None, "error": f"{e.response.status_code} - {e.response.text}"}
    except httpx.RequestError as e:
        logger.error(f"Request error fetching XE rates: {e}")
        return {"status": "error", "data": None, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error fetching XE rates: {e}")
        return {"status": "error", "data": None, "error": str(e)}
