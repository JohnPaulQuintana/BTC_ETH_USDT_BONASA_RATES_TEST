from typing import List, Dict, Any, Optional
from utils.logger import Logger
from utils.google_client import get_gspread_client
from utils.env_loader import get_env
from datetime import datetime

gc = get_gspread_client()
sh = gc.open_by_key(get_env("SHEET_URL"))
shs = gc.open_by_key(get_env("BONASA_SHEET_AGT", ""))  # Souce Sheet
tab = get_env("BONASA_TAB", "BONASA")
result_tab = get_env("EFFECTIVE_CONVERSION_RATE_TAB", "EFFECTIVE CONVERSION RATE")


def read_and_calculate_bonasa_sheet_tab(logger: Logger) -> List[Dict[str, Any]]:
    """Read only today's row from the source sheet and calculate effective rate."""
    try:
        logger.info(f"Opening worksheet: {tab}...")
        worksheet = shs.worksheet(tab)

        # Today's date string
        # today_str = datetime.now().strftime("%d/%m/%Y")
        # Day without leading zero
        today_str = f"{datetime.now().day}/{datetime.now().month}/{datetime.now().year}"


        # Try to find the row for today
        all_rows = worksheet.get_all_values()  # Still minimal read
        results: List[Dict[str, Any]] = []

        for row in all_rows[1:]:  # skip header
            print("---------------------------------------")
            print(row)
            print("---------------------------------------")
            if len(row) < 2:
                continue
            if row[0].strip() == today_str:
                purchase_rate = row[1].strip()
                effective_rate = None
                if purchase_rate:
                    try:
                        effective_rate = round(float(purchase_rate) * 1.01, 2)
                    except ValueError:
                        effective_rate = None

                results.append({
                    "Date": today_str,
                    "Purchase Rate": purchase_rate or None,
                    "Effective Conversion Rate": effective_rate
                })
                logger.info(f"Found data for today ({today_str}).")
                break  # Only need today's row

        if not results:
            logger.info(f"No data found for today ({today_str}).")

        return results

    except Exception as e:
        logger.error(f"Error reading sheet: {e}")
        return []



def save_effective_conversion(logger: Logger, all_rows: List[Dict[str, Any]]) -> Optional[float]:
    """Append or update only today's row in the target sheet."""
    if not all_rows:
        logger.info("No rows to save for today.")
        return None

    try:
        try:
            worksheet = sh.worksheet("BONASA")
        except Exception:
            worksheet = sh.add_worksheet(title="BONASA", rows="2", cols="3")
            worksheet.append_row(["DATE", "PURCHASE RATE", "EFFECTIVE CONVERSION RATE"])
            logger.info("Created worksheet BONASA with headers.")

        # Get existing dates to check if today's row exists
        existing_rows = worksheet.get_all_values()
        existing_dates = [r[0] for r in existing_rows[1:]]  # skip header

        today_row = all_rows[0]  # only today's row
        effective_rate = today_row.get("Effective Conversion Rate")

        if today_row["Date"] in existing_dates:
            row_index = existing_dates.index(today_row["Date"]) + 2
            worksheet.update(f"A{row_index}:C{row_index}", [[
                today_row["Date"],
                today_row["Purchase Rate"],
                # today_row["Effective Conversion Rate"]
                effective_rate
            ]])
            logger.info(f"Updated row for {today_row['Date']}.")
        else:
            worksheet.append_row([
                today_row["Date"],
                today_row["Purchase Rate"],
                # today_row["Effective Conversion Rate"]
                effective_rate
            ], value_input_option="USER_ENTERED")
            logger.info(f"Added new row for {today_row['Date']}.")

        # RETURN the effective conversion rate
        return effective_rate
    except Exception as e:
        logger.error(f"Error saving to sheet: {e}")

