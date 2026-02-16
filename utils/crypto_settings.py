import requests
def fetch_crypto_settings(session: requests.Session, LoggerClass, base_url):
    url = f"{base_url}/manager/payment/searchAllCryptocurrencySetting"
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": f"{base_url}/page/manager/payment/cryptocurrencySetting.jsp",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    }

    # cookies are already in session
    try:
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Debug: print raw response if JSON fails
        try:
            LoggerClass.success("→ Collected Successfully...")
            return response.json()
        except Exception:
            LoggerClass.error(f"→ Raw response:, {response.text[:500]}")
            return None

    except Exception:
        import traceback
        LoggerClass.error("→ Failed to fetch crypto settings:")
        traceback.print_exc()
        return None
