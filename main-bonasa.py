import asyncio
import random
from datetime import datetime
from services.bonasa_service import BonasaService
from utils.logger import Logger
from utils.spreadsheet import read_and_calculate_bonasa_sheet_tab, save_effective_conversion
from services.tg_bot_service import send_telegram_alert
async def retry_async(func, *args, retries=5, min_wait=1, max_wait=5, logger=None, **kwargs):
    """
    Retry an async function until it succeeds or max retries is reached.
    Expects the function to return a dict with 'status' key.
    """
    attempt = 0
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
        logger.error(f"→ All {retries} attempts failed for {func.__name__}.")
    return result

async def main():
    logger = Logger()
    #test flow
    # rows = read_and_calculate_bonasa_sheet_tab(logger)
    # print("=================AGT ROWS TODAY=================")
    # # print(rows)
    # if rows[0]['Purchase Rate'] is not None:
    #     print("Purchase Rate exists")
    # else:
    #     print("Purchase Rate is None")

    #     # send alert on tg channel
    #     send_telegram_alert(
    #         "<b>BONASA NOT UPDATED</b>\n"
    #         f"Date: {rows[0]['Date']}\n"
    #         "Rate not yet updated."
    #     )

    # print("=================END AGT ROWS TODAY=================")

    # deployed
    bonasa_service = BonasaService()
    auth_status = bonasa_service.authenticate(logger)
    if auth_status:
        rows = read_and_calculate_bonasa_sheet_tab(logger)
        if rows:
            # print(rows)
            # effective_conversion_rate = save_effective_conversion(logger, rows) or 0
            # bonasa_service.update_conversion_rate(
            #     setting_id="S008",
            #     currency="BDT",
            #     conversion_rate=effective_conversion_rate,
            #     logger=logger
            # )
            print("=================AGT ROWS TODAY=================")
            # print(rows)
            if rows[0]['Purchase Rate'] is not None:
                print("Purchase Rate exists")
                effective_conversion_rate = save_effective_conversion(logger, rows) or 0
                bonasa_service.update_conversion_rate(
                    setting_id="S008",
                    currency="BDT",
                    conversion_rate=effective_conversion_rate,
                    logger=logger
                )
            else:
                print("Purchase Rate is None")

                # send alert on tg channel
                send_telegram_alert(
                    "<b>BONASA NOT UPDATED</b>\n"
                    f"Date: {rows[0]['Date']}\n"
                    "Rate not yet updated."
                )

            print("=================END AGT ROWS TODAY=================")

        else:
            logger.warning("⚠️ No rows to process")
    else:
        logger.error()
    
   

    

if __name__ == "__main__":
    asyncio.run(main())
