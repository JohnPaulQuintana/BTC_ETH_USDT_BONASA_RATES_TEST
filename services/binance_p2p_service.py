import json
import traceback
from utils.env_loader import get_env
from datetime import datetime
import asyncio
import nest_asyncio
from playwright.async_api import async_playwright

nest_asyncio.apply()  # <-- allow nested event loops

class BinanceP2PService:
    def __init__(self):
        self.base_url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"

    # async def _fetch_all_pages_async(self, fiat: str, max_pages: int = 3):
    #     async with async_playwright() as p:
    #         browser = await p.chromium.launch(headless=True)
    #         context = await browser.new_context()
    #         page = await context.new_page()

    #         captured_request = {}

    #         async def handle_request(request):
    #             if "bapi/c2c/v2/friendly/c2c/adv/search" in request.url and request.method == "POST":
    #                 if not captured_request:
    #                     captured_request["url"] = request.url
    #                     captured_request["headers"] = dict(request.headers)
    #                     try:
    #                         captured_request["post_data"] = request.post_data_json
    #                     except:
    #                         captured_request["post_data"] = json.loads(request.post_data or "{}")

    #         page.on("request", handle_request)
    #         await page.goto(f"https://p2p.binance.com/en/trade/sell/USDT?fiat={fiat}&payment=all-payments")
    #         await page.wait_for_load_state("networkidle")

    #         if not captured_request:
    #             raise RuntimeError("Could not capture the search request.")

    #         all_pages_raw = []
    #         for page_number in range(1, max_pages + 1):
    #             captured_request["post_data"]["page"] = page_number
    #             response = await context.request.post(
    #                 captured_request["url"],
    #                 data=json.dumps(captured_request["post_data"]),
    #                 headers=captured_request["headers"]
    #             )
    #             all_pages_raw.append(await response.json())

    #         await browser.close()
    #         return all_pages_raw

    # Improved Request
    async def _fetch_all_pages_async(self, fiat: str, max_pages: int = 3):
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-dev-shm-usage"]
            )

            context = await browser.new_context(
                java_script_enabled=True,
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
                )
            )

            page = await context.new_page()

            captured_request = {}

            async def handle_request(request):
                if (
                    "bapi/c2c/v2/friendly/c2c/adv/search" in request.url
                    and request.method == "POST"
                    and not captured_request
                ):
                    captured_request["url"] = request.url
                    captured_request["headers"] = dict(request.headers)
                    try:
                        captured_request["post_data"] = request.post_data_json
                    except Exception:
                        captured_request["post_data"] = json.loads(request.post_data or "{}")

            page.on("request", handle_request)

            # Controlled navigation
            try:
                await page.goto(
                    f"https://p2p.binance.com/en/trade/sell/USDT?fiat={fiat}&payment=all-payments",
                    wait_until="domcontentloaded",
                    timeout=60_000,  # 30s hard timeout
                )
            except Exception as e:
                await browser.close()
                raise RuntimeError(f"Page load timeout for {fiat}") from e

            # Soft wait for JS-triggered POST
            try:
                await page.wait_for_event("request", timeout=15_000)
            except:
                pass  # allow fallback

            # Fallback wait
            for _ in range(30):
                if captured_request:
                    break
                await page.wait_for_timeout(500)

            if not captured_request:
                await browser.close()
                raise RuntimeError("Failed to capture Binance P2P POST request")

            # API calls with timeout
            all_pages_raw = []
            for page_number in range(1, max_pages + 1):
                captured_request["post_data"]["page"] = page_number

                response = await context.request.post(
                    captured_request["url"],
                    data=json.dumps(captured_request["post_data"]),
                    headers=captured_request["headers"],
                    timeout=20_000
                )

            all_pages_raw.append(await response.json())

        await browser.close()
        return all_pages_raw


    def fetch_top5_completed_order_rates(self, fiat: str, max_retries: int = 5) -> dict:
        """Sync wrapper for async Playwright fetch with retry logic and raw JSON save."""
        attempt = 0
        while attempt < max_retries:
            try:
                # Safe sync call even if already inside an event loop
                loop = asyncio.get_event_loop()
                all_pages_raw = loop.run_until_complete(self._fetch_all_pages_async(fiat, max_pages=3))

                all_ads = []
                for page_data in all_pages_raw:
                    data = page_data.get("data", [])
                    for entry in data:
                        adv = entry.get("adv", {})
                        advertiser = entry.get("advertiser", {})
                        trade_methods = adv.get("tradeMethods", [])
                        featured_ad = entry.get("privilegeDesc", None)
                        trade_method_names = [method.get("tradeMethodName") for method in trade_methods]

                        if featured_ad not in (None, ""):
                            continue

                        # if "Bank Transfer" in trade_method_names:
                        #     continue

                        all_ads.append({
                            "price": float(adv.get("price")),
                            "asset": adv.get("asset"),
                            "fiat": fiat,
                            "minAmount": adv.get("minSingleTransAmount"),
                            "maxAmount": adv.get("dynamicMaxSingleTransAmount"),
                            "available": adv.get("surplusAmount"),
                            "tradeType": "SELL",
                            "nick": advertiser.get("nickName"),
                            "completionRate": advertiser.get("monthFinishRate"),
                            "orders": advertiser.get("monthOrderCount", 0),
                            "tradeMethods": trade_method_names,
                        })

                # Save all raw pages (commented, you can uncomment if needed)
                # timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                # with open(f"binance_{fiat}_pages_{timestamp}.json", "w", encoding="utf-8") as f:
                #     json.dump({"pages": all_pages_raw}, f, indent=4, ensure_ascii=False)

                top_ads = sorted(all_ads, key=lambda x: x["orders"], reverse=True)[:5]

                # Retry if top_ads is empty
                # if not top_ads:
                #     attempt += 1
                #     wait_time = 2 ** (attempt - 1)  # exponential backoff: 1s, 2s, 4s
                #     print(f"No top ads found, retrying in {wait_time}s (attempt {attempt}/{max_retries})...")
                #     import time; time.sleep(wait_time)
                #     continue

                avg_rate = sum(ad["price"] for ad in top_ads) / len(top_ads)
                return {
                    "status": "success",
                    "fiat": fiat,
                    "asset": "USDT",
                    "binance_rate": avg_rate,
                    "sign": "Positive" if avg_rate >= 0 else "Negative",
                    "top_ads": top_ads,
                }

            except Exception:
                attempt += 1
                wait_time = 3 ** (attempt - 1)
                print(f"Attempt {attempt} failed, retrying in {wait_time}s...")
                import time; time.sleep(wait_time)
                if attempt >= max_retries:
                    # Return minimal info without breaking automation
                    return {
                        "status": "error",
                        "fiat": fiat,
                        "asset": "USDT",
                        "binance_rate": None,
                        "sign": None,
                        "top_ads": [],
                        "message": f"Failed after {attempt} attempts:\n{traceback.format_exc()}",
                    }



# class BinanceP2PService:
    # def __init__(self):
    #     self.base_url = get_env(
    #         "P2P_URL", "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    #     )
    #     self.session = requests.Session()

    # def _build_payload(self, fiat: str, page: int) -> dict:
    #     return {
    #         "fiat": fiat,
    #         "page": page,
    #         "rows": 10,
    #         "tradeType": "SELL",
    #         "asset": "USDT",
    #         "countries": [],
    #         "proMerchantAds": False,
    #         "shieldMerchantAds": False,
    #         "filterType": "all",
    #         "periods": [],
    #         "additionalKycVerifyFilter": 0,
    #         "publisherType": "merchant",
    #         "payTypes": [],
    #         "classifies": ["mass", "profession", "fiat_trade"],
    #         "tradedWith": False,
    #         "followed": False,
    #     }

    # def fetch_top5_completed_order_rates(self, fiat: str) -> dict:
    #     all_ads = []
    #     all_pages_raw = []  # <-- store full raw responses here

    #     try:
    #         for page in range(1, 4):  # first 3 pages
    #             payload = self._build_payload(fiat, page)
    #             print("---------------------------------------------")
    #             print(payload)
    #             print("---------------------------------------------")
    #             resp = self.session.post(self.base_url, json=payload, timeout=10)
    #             resp.raise_for_status()

    #             page_data = resp.json()
    #             all_pages_raw.append(page_data)  # store full raw response

    #             data = page_data.get("data", [])

    #             for entry in data:
    #                 adv = entry.get("adv", {})
    #                 advertiser = entry.get("advertiser", {})
    #                 trade_methods = adv.get("tradeMethods", [])
    #                 featured_ad = entry.get("privilegeDesc", None)
    #                 trade_method_names = [
    #                     method.get("tradeMethodName") for method in trade_methods
    #                 ]

    #                 # Accept only ads with privilegeDesc == None or ""
    #                 if featured_ad not in (None, ""):
    #                     continue

    #                 # Skip if Bank Transfer is one of the trade methods
                    
    #                 if "Bank Transfer" in trade_method_names:
    #                     print("----------------SKIPPING-----------------")
    #                     print(trade_method_names)
    #                     print(advertiser.get("nickName"))
    #                     print("------------------------------------------------")
    #                     continue

    #                 all_ads.append(
    #                     {
    #                         "price": float(adv.get("price")),
    #                         "asset": adv.get("asset"),
    #                         "fiat": payload["fiat"],
    #                         "minAmount": adv.get("minSingleTransAmount"),
    #                         "maxAmount": adv.get("dynamicMaxSingleTransAmount"),
    #                         "available": adv.get("surplusAmount"),
    #                         "tradeType": payload["tradeType"],
    #                         "nick": advertiser.get("nickName"),
    #                         "completionRate": advertiser.get("monthFinishRate"),
    #                         "orders": advertiser.get("monthOrderCount", 0),
    #                         "tradeMethods": trade_method_names,
    #                     }
    #                 )

    #         # ✅ Save all raw pages to a single JSON file
    #         with open(f"binance_{fiat}_pages.json", "w", encoding="utf-8") as f:
    #             json.dump({"pages": all_pages_raw}, f, indent=4, ensure_ascii=False)

    #         # Sort by highest orders
    #         top_ads = sorted(all_ads, key=lambda x: x["orders"], reverse=True)[:5]

    #         if not top_ads:
    #             return {"status": "error", "message": "No ads found"}

    #         avg_rate = sum(ad["price"] for ad in top_ads) / len(top_ads)

    #         return {
    #             "status": "success",
    #             "fiat": fiat,
    #             "asset": "USDT",
    #             "binance_rate": avg_rate,
    #             "sign": "Positive" if avg_rate >= 0 else "Negative",
    #             "top_ads": top_ads,
    #         }

    #     except Exception:
    #         return {"status": "error", "message": traceback.format_exc()}
