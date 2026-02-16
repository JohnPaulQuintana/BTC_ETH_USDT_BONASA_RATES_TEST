def convert_crypto_prices(binance_data: dict, xe_data: dict) -> dict:
    """
    Multiply Binance USD prices with XE conversion rates.

    Args:
        binance_data: {'BTC': {'symbol': 'BTCUSDT', 'price': '110273.46'}, ...}
        xe_data: {'rates': {'BDT': 121.64, 'PKR': 283.70, 'INR': 88.01}}

    Returns:
        dict like:
        {
            'BTC': {'BDT': 13415564.06, 'PKR': 31289028.26, 'INR': 9700464.73},
            'ETH': {'BDT': 533107.54, 'PKR': 1243564.73, 'INR': 385859.61}
        }
    """
    rates = xe_data.get("rates", {})
    results = {}

    for coin, coin_data in binance_data.items():
        usd_price = float(coin_data["price"])
        results[coin] = {
            currency: round(usd_price * rate, 2)
            for currency, rate in rates.items()
        }

    return results
