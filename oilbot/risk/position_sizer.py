from oilbot.config import MAX_POSITION_PCT


def size_position(capital: float, price: float, conviction: float = 1.0) -> int:
    risk_amount = capital * MAX_POSITION_PCT * abs(conviction)
    raw_units = risk_amount / price
    units = int(raw_units)
    return max(units, 1)
