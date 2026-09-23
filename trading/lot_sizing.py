from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN


XAUUSD_CONTRACT_SIZE = 100.0

MIN_LOT = 0.01
MAX_LOT = 0.50
LOT_STEP = 0.01


@dataclass
class LotSizeResult:
    balance: float
    risk_percent: float
    risk_amount: float
    entry: float
    stop_loss: float
    stop_distance: float
    calculated_lot: float
    final_lot: float
    capped: bool
    below_minimum: bool


def round_down_lot(value: float) -> float:
    value = Decimal(str(value))
    step = Decimal(str(LOT_STEP))

    result = (value / step).to_integral_value(
        rounding=ROUND_DOWN
    ) * step

    return float(result)


def calculate_xauusd_lot(
    balance: float,
    entry: float,
    stop_loss: float,
    risk_percent: float = 1.0,
) -> LotSizeResult:

    balance = float(balance)
    entry = float(entry)
    stop_loss = float(stop_loss)
    risk_percent = float(risk_percent)

    if balance <= 0:
        raise ValueError("Balance must be greater than zero.")

    if risk_percent <= 0:
        raise ValueError("Risk percent must be greater than zero.")

    if entry <= 0 or stop_loss <= 0:
        raise ValueError("Entry and stop-loss must be greater than zero.")

    stop_distance = abs(entry - stop_loss)

    if stop_distance <= 0:
        raise ValueError("Stop-loss must differ from entry.")

    risk_amount = balance * (risk_percent / 100.0)

    calculated_lot = (
        risk_amount
        / (stop_distance * XAUUSD_CONTRACT_SIZE)
    )

    below_minimum = calculated_lot < MIN_LOT

    rounded_lot = round_down_lot(calculated_lot)

    if rounded_lot < MIN_LOT:
        final_lot = MIN_LOT
    elif rounded_lot > MAX_LOT:
        final_lot = MAX_LOT
    else:
        final_lot = rounded_lot

    capped = calculated_lot > MAX_LOT

    return LotSizeResult(
        balance=balance,
        risk_percent=risk_percent,
        risk_amount=risk_amount,
        entry=entry,
        stop_loss=stop_loss,
        stop_distance=stop_distance,
        calculated_lot=round(calculated_lot, 4),
        final_lot=round(final_lot, 2),
        capped=capped,
        below_minimum=below_minimum,
    )


def validate_lot(lot: float) -> float:
    lot = float(lot)

    if lot < MIN_LOT or lot > MAX_LOT:
        raise ValueError(
            f"Lot must be between {MIN_LOT:.2f} and {MAX_LOT:.2f}."
        )

    rounded = round(lot / LOT_STEP) * LOT_STEP

    if abs(lot - rounded) > 1e-9:
        raise ValueError(
            "Lot must use 0.01 increments."
        )

    return round(lot, 2)
