"""Pure, bounded research models for the hash-pinned reference executable.

These are not production rules. Signed rank bytes and exact mask comparison
reproduce legacy behavior without endorsing it for the new game. No model
loads native bytes or performs I/O; the independent oracle is separate.
"""
from dataclasses import dataclass


def _integer(value: int, low: int, high: int, name: str) -> None:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")


@dataclass(frozen=True)
class FinishState:
    status_u32: int
    countdown_i32: int
    exit_latch: int


def finish_request(request_status: int, delay_i32: int, rank_byte: int,
                   network_a: int, network_b: int, current_status: int,
                   current_delay: int, current_latch: int) -> FinishState:
    """0x416010 prefix, stopping before network notification/string copying.

    A positive delay has an unknown time unit. A nonzero countdown OR latch
    suppresses repeated requests. Status 0x7f classifies an already-requested
    finish; it does not detect crossing the finish line.
    """
    for name, value in (("request_status", request_status), ("current_status", current_status)):
        _integer(value, 0, 0xFFFFFFFF, name)
    for name, value in (("delay_i32", delay_i32), ("current_delay", current_delay)):
        _integer(value, -2**31, 2**31 - 1, name)
    for name, value in (("rank_byte", rank_byte), ("network_a", network_a),
                        ("network_b", network_b), ("current_latch", current_latch)):
        _integer(value, 0, 255, name)
    if current_delay != 0 or current_latch != 0:
        return FinishState(current_status, current_delay, current_latch)
    status = request_status
    if request_status == 0x7F:
        signed_rank = rank_byte if rank_byte < 128 else rank_byte - 256
        threshold = 1 if network_a != 0 or network_b != 0 else 3
        status = 2 if signed_rank < threshold else 3
    return FinishState(status, delay_i32 if delay_i32 > 0 else 0,
                       0 if delay_i32 > 0 else 1)


def offline_outcome_screen(mode: int, status_u32: int) -> int:
    """0x416237 tail with network registers CL=DL=0, after earlier cleanup.

    Does not execute the full caller, registry writes, race shutdown or network
    result recording. Screen IDs are original interface state identifiers.
    """
    _integer(mode, 0, 3, "mode")
    _integer(status_u32, 0, 0xFFFFFFFF, "status_u32")
    if mode == 0:
        return 9
    return {2: 0x1E, 3: 0x1F, 4: 0x1D}.get(status_u32, 0x1C)


@dataclass(frozen=True)
class MediaState:
    qualification_mask: int
    prefix: str
    variants: int


def result_media(screen_code: int, mode: int, level_index: int,
                 qualification_mask: int, course_id: int) -> MediaState:
    """0x449150..0x4491eb: selection only, before media playback.

    For a qualifying screen outside mode 3, course IDs 1..5 are required.
    Other IDs hit an uninitialized native stack read, not a valid fallback.
    Upper mask bits are preserved; only the exact byte 0x1f is complete.
    """
    _integer(screen_code, 0x1C, 0x1F, "screen_code")
    _integer(mode, 0, 3, "mode")
    _integer(level_index, 0, 4, "level_index")
    _integer(qualification_mask, 0, 255, "qualification_mask")
    _integer(course_id, 0, 255, "course_id")
    mask = qualification_mask
    if screen_code != 0x1E:
        prefix, count = {0x1C: ("Wreck", 6), 0x1D: ("Busted", 6),
                         0x1F: ("Lose", 10)}[screen_code]
        return MediaState(mask, prefix, count)
    if mode != 3:
        _integer(course_id, 1, 5, "qualifying course_id")
        mask |= 1 << (course_id - 1)
    if mask == 0x1F:
        return MediaState(mask, "FinalWin", 0) if level_index == 4 else MediaState(mask, "Level", 6)
    return MediaState(mask, "Win", 6)


@dataclass(frozen=True)
class ProgressionState:
    level_index: int
    qualification_mask: int
    dirty_byte: int
    next_screen: int | None
    boundary: str


def acknowledge_result(acknowledgement: int, mode: int, level_index: int,
                       qualification_mask: int, character_byte: int,
                       dirty_byte: int) -> ProgressionState:
    """0x41f6d0 callback. Network continuation is deliberately unexecuted.

    Completion is checked before mode dispatch. Mask clearing and level updates
    are observed here, not in result_media. dirty_byte is a raw field: writing
    it does not establish that a save or persistence transaction occurred.
    """
    _integer(acknowledgement, 0, 1, "acknowledgement")
    _integer(mode, 0, 3, "mode")
    _integer(level_index, 0, 4, "level_index")
    for name, value in (("qualification_mask", qualification_mask),
                        ("character_byte", character_byte), ("dirty_byte", dirty_byte)):
        _integer(value, 0, 255, name)
    if acknowledgement == 0:
        return ProgressionState(level_index, qualification_mask, dirty_byte, 0, "return")
    if qualification_mask == 0x1F:
        if level_index == 4:
            return ProgressionState(4, 0, 1, 0x23, "return")
        return ProgressionState(level_index + 1, 0, 1, 0x20, "return")
    if mode == 3:
        return ProgressionState(level_index, qualification_mask, dirty_byte, None, "network_callback")
    screen = {0: 9, 1: 10, 2: 14 if character_byte == 0 else 15}[mode]
    return ProgressionState(level_index, qualification_mask, dirty_byte, screen, "return")
