import asyncio
import random
from datetime import datetime

from services.binance_service import get_btc_eth_prices, get_usdt_to_usd
# from services.bonasa_service import BonasaService
from services.xe_service import fetch_xe_rates
from services.converter_service import convert_crypto_prices
from services.bo_scrapper_service import BOScrapperService
from services.binance_p2p_service import BinanceP2PService
from utils.logger import Logger
from utils.spreadsheet import (
    read_and_calculate_bonasa_sheet_tab,
    save_effective_conversion
)
from services.tg_bot_service import send_telegram_alert, send_telegram_logs

BONASA_UPDATED_TODAY = False
BONASA_ALERT_SENT = False  # new flag to avoid multiple alerts per 5-min block
current_date_readable = None

# =========================================================
# TIME RULES
# =========================================================

def is_bonasa_window(now: datetime) -> bool:
    """Check Bonasa between 10:30 and 10:50 inclusive"""
    return now.hour == 11 and 0 <= now.minute <= 20 and not BONASA_UPDATED_TODAY

def is_coin_time(now: datetime) -> bool:
    """Run coin tasks hourly starting at 11:00 AM"""
    return now.hour >= 11 and now.minute == 30
# =========================================================
# RETRY HELPER
# =========================================================

async def retry_async(func, *args, retries=5, min_wait=1, max_wait=5, logger=None, **kwargs):
    attempt = 0
    result = None

    while attempt < retries:
        result = await func(*args, **kwargs)

        if isinstance(result, dict) and result.get("status") == "success":
            return result

        attempt += 1
        wait_time = random.uniform(min_wait, max_wait)

        if logger:
            logger.warn(f"→ Attempt {attempt} failed for {func.__name__}. Retrying in {wait_time:.2f}s...")

        await asyncio.sleep(wait_time)

    if logger:
        logger.error(f"→ All {retries} attempts failed for {func.__name__}")

    return result

# =========================================================
# MAIN TASK EXECUTION (ONE CYCLE)
# =========================================================

async def run_tasks():
    global BONASA_UPDATED_TODAY, BONASA_ALERT_SENT, current_date_readable
    logger = Logger()
    now = datetime.now()
    logger.info(f"Current Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # --- LOG NETWORK SPEED ---
    # await log_network_speed(logger)
    
    # =====================================================
    # BONASA — CHECK EVERY MINUTE FROM 10:00–10:30
    # =====================================================
    if is_bonasa_window(now):
        logger.info("Checking BONASA window (10:00–10:30)")

        rows = read_and_calculate_bonasa_sheet_tab(logger)
        print(rows)
        if not rows:
            logger.warning("No Bonasa rows to process")
        else:
            print("=================AGT ROWS TODAY=================")
            purchase_rate = rows[0]['Purchase Rate']

            if purchase_rate is not None:
                # DATA AVAILABLE → UPDATE IMMEDIATELY
                effective_conversion_rate = save_effective_conversion(logger, rows) or 0

                BONASA_UPDATED_TODAY = True
                BONASA_ALERT_SENT = False  # reset alert flag if updated
                logger.success(f"(SHEET UPDATED) - Bonasa RATE: {effective_conversion_rate} updated successfully")

                send_telegram_logs(
                    "<b>(SERVER)Automation Success</b>\n"
                    f"Date: {now.strftime("%B %d, %Y %I:%M %p")}\n"
                    "Bonasa automation completed successfully."
                )
                    
            else:
                # DATA MISSING → send alert every 5 minutes
                if now.minute % 5 == 0 and not BONASA_ALERT_SENT:
                    # current_time = now.strftime("%H:%M")
                    # send_telegram_alert(
                    #     "<b>(SERVER)BONASA NOT UPDATED</b>\n"
                    #     f"Date: {rows[0]['Date']} {current_time}\n"
                    #     "Purchase Rate not yet updated."
                    # )
                    logger.warn("Telegram alert sent")
                    BONASA_ALERT_SENT = True
                elif now.minute % 5 != 0:
                    # reset alert flag after each 5-minute block
                    BONASA_ALERT_SENT = False

            print("=================END AGT ROWS TODAY=================")
            
    else:
        logger.info("Bonasa skipped (outside window)")

    # =====================================================
    # COINS — HOURLY FROM 11:00 AM
    # =====================================================
    if not is_coin_time(now):
        logger.info("Coin automation skipped")
        return

    logger.info("Running COIN automation")
    BONASA_UPDATED_TODAY = False
    # USDT → USD
    binance_usdtusd = await retry_async(get_usdt_to_usd, retries=5, min_wait=2, max_wait=5, logger=logger)

    # Binance BTC / ETH
    binance_data = await retry_async(get_btc_eth_prices, retries=5, min_wait=2, max_wait=5, logger=logger)
    if binance_data.get("status") != "success":
        logger.error("Binance price fetch failed")
        send_telegram_logs(
            "<b>(SERVER)Automation Failed</b>\n"
            f"Date: {now.strftime("%B %d, %Y %I:%M %p")}\n"
            "Binance price fetch failed.\n"
        )
        return

    logger.success(f"→ Binance Data: {binance_data['data']}")

    # XE Rates
    xe_data = await retry_async(fetch_xe_rates, retries=5, min_wait=2, max_wait=5, logger=logger)
    if xe_data.get("status") != "success":
        logger.error("XE rate fetch failed")
        send_telegram_logs(
            "<b>(SERVER)Automation Failed</b>\n"
            f"Date: {now.strftime("%B %d, %Y %I:%M %p")}\n"
            "XE rate fetch failed.\n"
        )
        return

    logger.success("→ XE Rates fetched")

    # Conversion
    converted = convert_crypto_prices(binance_data.get("data", {}), xe_data.get("data", {}))
    logger.info("→ Converted Prices Ready")

    # BO Scrapper
    service = BOScrapperService()
    if not service.test_accessible(logger):
        logger.warn("VPN REQUIRED TO ACCESS BO")
        send_telegram_logs(
            "<b>(SERVER)Automation Failed</b>\n"
            f"Date: {now.strftime("%B %d, %Y %I:%M %p")}\n"
            "VPN REQUIRED TO ACCESS BO.\n"
        )
        return

    p2p_service = BinanceP2PService()
    localtime = now.strftime("%Y-%m-%d %H:%M:%S")

    scrapper_response = service.scrappe_bo(
        logger,
        binance_usdtusd,
        xe_data.get("data", {}),
        converted.items(),
        binance_data.get("data", {}),
        p2p_service,
        localtime
    )

    if scrapper_response:
        logger.success("Coin automation completed successfully")
        send_telegram_logs(
            "<b>(SERVER)Automation Success</b>\n"
            f"Date: {now.strftime("%B %d, %Y %I:%M %p")}\n"
            "Coin automation completed successfully.\n"
        )
    else:
        send_telegram_logs(
            "<b>(SERVER)Automation Failed</b>\n"
            f"Date: {now.strftime("%B %d, %Y %I:%M %p")}\n"
            "Coin automation Failed.\n"
        )
        logger.error("Coin automation failed")

# =========================================================
# SCHEDULER LOOP (KEEPS TERMINAL OPEN)
# =========================================================

async def scheduler_loop():
    logger = Logger()
    logger.info("Scheduler started (checks every 60 seconds)")
    now = datetime.now()
    while True:
        try:
            await run_tasks()
        except Exception as e:
            send_telegram_logs(
                "<b>(SERVER)Automation Failed</b>\n"
                f"Date: {now.strftime("%B %d, %Y %I:%M %p")}\n"
                "Scheduler runtime error."
            )
            logger.error(f"❌ Scheduler error: {e}")

        await asyncio.sleep(60)

# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    asyncio.run(scheduler_loop())
