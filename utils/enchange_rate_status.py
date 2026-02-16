def get_horizontal_status(sign: str) -> int:
    return 1 if sign.lower() == "positive" else 0

def normalize_rate(rate) -> float:
    try:
        return abs(float(rate))
    except (TypeError, ValueError):
        return 0.0
