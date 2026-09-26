"""Pure research models. Not the new game implementation or a full behavior spec.

The executable oracle lives separately, so the expected values do not call
the native implementation. Raw units remain raw until runtime establishes them.
"""
from dataclasses import dataclass

BIKE_NAME_IDS = (112, 113, 114, 116, 115, 122, 125, 123, 126, 124, 117, 120, 118, 121, 119)
BASE_PRIZES = (1000, 750, 500, 400, 300, 250, 200, 160, 130, 100, 70, 50, 30, 20)


def integer_range(value: int, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")
    return value


def bike_name_id(byte_index: int) -> int:
    """VA 0x420AA0: all unknown byte IDs default to name 112, not a valid bike."""
    integer_range(byte_index, 0, 255, "byte_index")
    return BIKE_NAME_IDS[byte_index] if byte_index < len(BIKE_NAME_IDS) else 112


@dataclass(frozen=True)
class ResultState:
    cash_u32: int
    displayed_rows: int
    selected_row: int


def result_screen_state(mode: int, level_index: int, place_index: int, cash_u32: int,
                        field_count: int = 15) -> ResultState:
    """VA 0x421290..0x421384; assumes the result-screen entry is reached.

    This does NOT establish when a race finishes, DNF qualification, persistence,
    or repeat-entry prevention. Mode 2 credits the cash field at this call site.
    u32 wrap is faithful legacy behavior, not a safe rule for the new economy.
    """
    integer_range(mode, 1, 3, "mode")
    integer_range(level_index, 0, 255, "level_index")
    integer_range(place_index, 0, 13, "place_index")
    integer_range(cash_u32, 0, 0xFFFFFFFF, "cash_u32")
    integer_range(field_count, 2, 15, "field_count")
    rows = field_count - 1 if mode == 3 else (3 if place_index < 3 else 4)
    selected = place_index if place_index < rows else 3
    if selected >= rows:
        selected = 0
    elif mode == 2:
        cash_u32 = (cash_u32 + BASE_PRIZES[place_index] * (level_index + 1)) & 0xFFFFFFFF
    return ResultState(cash_u32, rows, selected)
