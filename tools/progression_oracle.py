"""Independent native-byte observations for four progression boundaries.

Original code is never patched. All execution uses the common pinned, bounded
x86 oracle; no Win32 calls, media playback, registry or network routine runs.
This module intentionally imports no expected-model or progression functions.
"""
from __future__ import annotations
import struct
from native_oracle import Oracle, STACK, STOP
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import (
    UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EDX,
    UC_X86_REG_ESP, UC_X86_REG_EIP,
)


def _bounds(*values: tuple[int, int, int]) -> None:
    if any(type(value) is not int or not low <= value <= high for value, low, high in values):
        raise ValueError("Input outside the native experiment domain")


def _u32(machine, address: int) -> int:
    return struct.unpack("<I", machine.mem_read(address, 4))[0]


def _byte(machine, address: int) -> int:
    return bytes(machine.mem_read(address, 1))[0]


def _put32(machine, address: int, value: int) -> None:
    machine.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))


def _put8(machine, address: int, value: int) -> None:
    machine.mem_write(address, bytes([value]))


class ProgressionOracle:
    def __init__(self, executable: bytes):
        self.core = Oracle(executable)

    @staticmethod
    def _execute(machine, start: int, until: int, boundaries: tuple[int, ...] = ()) -> int:
        """Boundary hooks stop BEFORE an instruction, never simulate its effect."""
        if boundaries:
            def stop_before(current, address, size, user):
                if address in boundaries:
                    current.emu_stop()
            machine.hook_add(UC_HOOK_CODE, stop_before)
        machine.emu_start(start, until, timeout=2_000_000, count=2000)
        reached = machine.reg_read(UC_X86_REG_EIP)
        if reached not in (until, *boundaries):
            raise RuntimeError(f"Native budget exhausted at {reached:#x}")
        return reached

    def finish_request(self, request_status: int, delay_i32: int, rank_byte: int,
                       network_a: int, network_b: int, current_status: int,
                       current_delay: int, current_latch: int) -> tuple[int, int, int]:
        _bounds((request_status, 0, 0xFFFFFFFF), (current_status, 0, 0xFFFFFFFF),
                (delay_i32, -2**31, 2**31-1), (current_delay, -2**31, 2**31-1),
                (rank_byte, 0, 255), (network_a, 0, 255), (network_b, 0, 255),
                (current_latch, 0, 255))
        machine = self.core.machine([(0x416010, 0x416082), (0x4160B6, 0x4160BA)],
            write_ranges=((0x4C5D7C, 0x4C5D80), (0x4753C4, 0x4753C8), (0x4753B4, 0x4753B5)))
        for address, value in ((0x4C5D7C, current_status), (0x4753C4, current_delay)):
            _put32(machine, address, value)
        for address, value in ((0x4C5D78, rank_byte), (0x4C5B00, network_a),
                               (0x4C5AF9, network_b), (0x4753B4, current_latch)):
            _put8(machine, address, value)
        machine.reg_write(UC_X86_REG_ESP, STACK + 0x8000)
        machine.reg_write(UC_X86_REG_ECX, request_status)
        machine.reg_write(UC_X86_REG_EDX, delay_i32 & 0xFFFFFFFF)
        self._execute(machine, 0x416010, STOP, (0x416079, 0x4160B6))
        countdown = struct.unpack("<i", machine.mem_read(0x4753C4, 4))[0]
        return _u32(machine, 0x4C5D7C), countdown, _byte(machine, 0x4753B4)

    def offline_outcome_screen(self, mode: int, status_u32: int) -> int:
        _bounds((mode, 0, 3), (status_u32, 0, 0xFFFFFFFF))
        machine = self.core.machine([(0x416237, 0x4162BD)])
        _put32(machine, 0x4753B0, mode)
        _put32(machine, 0x4C5D7C, status_u32)
        sp = STACK + 0x8000
        # Tail epilogue pops ESI, EBX, skips one local dword, then returns.
        machine.mem_write(sp, struct.pack("<4I", 0, 0, 0, STOP))
        machine.reg_write(UC_X86_REG_ESP, sp)
        machine.reg_write(UC_X86_REG_ECX, 0)
        machine.reg_write(UC_X86_REG_EDX, 0)
        self._execute(machine, 0x416237, STOP)
        return machine.reg_read(UC_X86_REG_EAX)

    def result_media(self, screen_code: int, mode: int, level_index: int,
                     qualification_mask: int, course_id: int) -> tuple[int, str, int]:
        _bounds((screen_code, 0x1C, 0x1F), (mode, 0, 3), (level_index, 0, 4),
                (qualification_mask, 0, 255), (course_id, 0, 255))
        if screen_code == 0x1E and mode != 3 and not 1 <= course_id <= 5:
            raise ValueError("Invalid course would read an uninitialized native stack byte")
        machine = self.core.machine([(0x449150, 0x4491EB)], write_ranges=((0x4B8A13, 0x4B8A14),))
        _put32(machine, 0x4753B0, mode)
        for address, value in ((0x4B8A12, level_index), (0x4B8A13, qualification_mask),
                               (0x4B8A15, course_id)):
            _put8(machine, address, value)
        machine.reg_write(UC_X86_REG_ESP, STACK + 0x8000)
        machine.reg_write(UC_X86_REG_ECX, screen_code)
        self._execute(machine, 0x449150, 0x4491EB)
        address = machine.reg_read(UC_X86_REG_EAX)
        if not 0x475568 <= address <= 0x47558C:
            raise RuntimeError("Unexpected media prefix pointer")
        prefix = bytes(machine.mem_read(address, 16)).split(b"\0", 1)[0].decode("ascii")
        return _byte(machine, 0x4B8A13), prefix, machine.reg_read(UC_X86_REG_EDX)

    def acknowledge_result(self, acknowledgement: int, mode: int, level_index: int,
                           qualification_mask: int, character_byte: int,
                           dirty_byte: int) -> tuple[int, int, int, int | None, str]:
        _bounds((acknowledgement, 0, 1), (mode, 0, 3), (level_index, 0, 4),
                (qualification_mask, 0, 255), (character_byte, 0, 255), (dirty_byte, 0, 255))
        machine = self.core.machine([(0x41F6D0, 0x41F740)],
            write_ranges=((0x4B8A12, 0x4B8A14), (0x4753AC, 0x4753AD)))
        _put32(machine, 0x4753B0, mode)
        for address, value in ((0x4B8A12, level_index), (0x4B8A13, qualification_mask),
                               (0x4B8A11, character_byte), (0x4753AC, dirty_byte)):
            _put8(machine, address, value)
        sp = STACK + 0x8000
        _put32(machine, sp, STOP)
        machine.reg_write(UC_X86_REG_ESP, sp)
        machine.reg_write(UC_X86_REG_ECX, acknowledgement)
        reached = self._execute(machine, 0x41F6D0, STOP, (0x41F735,))
        boundary = "network_callback" if reached == 0x41F735 else "return"
        screen = None if reached == 0x41F735 else machine.reg_read(UC_X86_REG_EAX)
        return (_byte(machine, 0x4B8A12), _byte(machine, 0x4B8A13),
                _byte(machine, 0x4753AC), screen, boundary)
