import csv
import os
import requests
import traceback, hashlib
from bs4 import BeautifulSoup
from utils.env_loader import get_env
from utils.crypto_settings import fetch_crypto_settings
from utils.crypto_utils import calculate_diff_and_save

class BOScrapperService:
    def __init__(self):
        """
        Initialize with session + BO URLs and login URLs.
        """
        self.session = requests.Session()
        self.cookies = None

        # BO URLs
        self.bo_brand = [url.strip() for url in get_env("BO_BRAND", "").split(",") if url.strip()]
        self.base_urls = [url.strip() for url in get_env("BASE_URLS", "").split(",") if url.strip()]
        self.bo_urls = [url.strip() for url in get_env("BO_URLS", "").split(",") if url.strip()]
        self.bo_login_urls = [url.strip() for url in get_env("BO_LOGIN_URLS", "").split(",") if url.strip()]

        if not (len(self.bo_urls) == len(self.base_urls) == len(self.bo_login_urls)):
            raise ValueError("BO_URLS, BASE_URLS, and BO_LOGIN_URLS must have the same length/order.")

        self.username = get_env("BO_USERNAME", "None")
        self.password = get_env("BO_PASSWORD", "None")

    def test_accessible(self, logger) -> str | None:
        """
        Test if each BO URL is reachable (VPN check).
        Returns the first accessible URL, else None.
        """
        for bo_url in self.bo_urls:
            try:
                logger.info(f"→ Testing {bo_url}")
                response = self.session.get(bo_url, timeout=5)
                if response.ok:
                    logger.success(f"→ Accessible: {bo_url}")
                    return bo_url
                else:
                    logger.error(f"→ Not accessible {bo_url}, status: {response.status_code}")
            except Exception:
                logger.warn(f"→ Error on {bo_url}:\n{traceback.format_exc()}")

        logger.error("→ None of the BO URLs are accessible (VPN required).")
        return None

    def scrappe_bo(
        self,
        logger,
        binance_usdtusd,
        xe_data,
        converted_currency_value,
        current_usd_value,
        p2p_service,
        localtime
    ) -> bool:
        """
        Attempt to login on each (bo_url, base_url) pair.
        Returns True if at least one run succeeds, else False.
        """
        logger.info("→ Authenticating user...")
        success = False

        for index, (bo_brand, bo_url, base_url, login_url) in enumerate(
            zip(self.bo_brand, self.bo_urls, self.base_urls, self.bo_login_urls), start=1
        ):
            try:
                logger.info(f"→ [{index}] → Trying {bo_brand} - {bo_url}")

                # Reset cookies
                self.session.cookies.clear()

                # 1) GET login page
                response = self.session.get(bo_url, timeout=10)
                response.raise_for_status()

                # 2) Scrape randomCode
                soup = BeautifulSoup(response.text, "html.parser")
                random_tag = soup.find("input", {"id": "randomCode"})
                if random_tag is None:
                    raise RuntimeError("randomCode input not found on login page.")

                random_code_val = random_tag["value"]
                logger.success(f"→ [{index}] RANDOM CODE: {random_code_val}")

                # 3) POST credentials
                auth_payload = {
                    "username": self.username,
                    "password": hashlib.sha1(self.password.encode()).hexdigest(),
                    "randomCode": random_code_val,
                }
                headers = {
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Accept": "*/*",
                    "Origin": base_url,
                    "Referer": bo_url,
                    "X-Requested-With": "XMLHttpRequest",
                    "User-Agent": (
                        "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36"
                    ),
                }

                login = self.session.post(login_url, data=auth_payload, headers=headers, timeout=10)
                login.raise_for_status()

                # 4) Check JSON response for errors
                resp_json = login.json()
                if "errors" in resp_json:
                    logger.error(f"→ [{index}] Login failed: {resp_json['errors']}")
                    continue
                else:
                    self.cookies = self.session.cookies.get_dict()
                    logger.success(f"→ [{index}] ✅ Authentication successful on {bo_url}")

                # 5) Load dashboard
                dashboard_url = f"{base_url}/page/manager/payment/cryptocurrencySetting.jsp"
                dashboard_response = self.session.get(dashboard_url, timeout=10)
                dashboard_response.raise_for_status()
                logger.success(f"→ Loaded dashboard, session cookies: {self.session.cookies.get_dict()}")

                # 6) Fetch crypto settings
                crypto_data = fetch_crypto_settings(self.session, logger, base_url)
                logger.success(f"→ [{index}] Crypto Settings: {crypto_data}")

                # 7) Save CSV diff
                calculate_diff_and_save(
                    base_url,self.session,binance_usdtusd, xe_data, current_usd_value, bo_brand, crypto_data, converted_currency_value, logger, p2p_service, localtime
                )
                logger.success(f"→ Differences saved")

                # 8) proceed on saving it to BO
                # Mark success
                success = True

            except Exception:
                logger.error(f"→ [{index}] ⚠️ Error on {bo_url}:\n{traceback.format_exc()}")

        if success:
            return True

        logger.error("→ All BO URLs failed.")
        return False

