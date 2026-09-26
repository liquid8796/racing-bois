"""Isolated native experiments for bike identity and result-screen arithmetic.

No Win32 imports execute. The result experiment stops before InvalidateRect;
only enumerated emulated globals and synthetic UI memory can be written.
"""
import struct
from native_oracle import Oracle, DEST, STACK, STOP
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_ESP, UC_X86_REG_EIP


class GameplayOracle:
    def __init__(self, executable: bytes):
        self.core = Oracle(executable)

    def bike_name(self, index: int) -> int:
        if type(index) is not int or not 0 <= index <= 255:
            raise ValueError("Byte index required")
        machine = self.core.machine([(0x420AA0, 0x420B0B)])
        sp = STACK + 0x8000
        machine.mem_write(sp, struct.pack("<I", STOP))
        machine.reg_write(UC_X86_REG_ESP, sp)
        machine.reg_write(UC_X86_REG_ECX, index)
        machine.emu_start(0x420AA0, STOP, timeout=2000000, count=100)
        if machine.reg_read(UC_X86_REG_EIP) != STOP:
            raise RuntimeError("Bike-name oracle did not return")
        return machine.reg_read(UC_X86_REG_EAX)

    def result_screen(self, mode: int, level: int, place: int, cash: int, field_count: int = 15) -> tuple[int, int, int]:
        values = [(mode, 1, 3), (level, 0, 255), (place, 0, 13),
                  (cash, 0, 0xFFFFFFFF), (field_count, 2, 15)]
        if any(type(x) is not int or not low <= x <= high for x, low, high in values):
            raise ValueError("Result oracle input outside experiment bounds")
        machine = self.core.machine([(0x421290, 0x421384)], write_ranges=(
            (0x46A638, 0x46A63C), (0x46A034, 0x46A034 + 14 * 0x38),
            (0x4B8A18, 0x4B8A1C)))
        for address, value in [(0x4753B0, mode), (0x4642D4, field_count),
                               (0x475378, DEST), (0x4B8A18, cash)]:
            machine.mem_write(address, struct.pack("<I", value))
        machine.mem_write(0x4B8A12, bytes([level]))
        machine.mem_write(0x4B8A16, bytes([place]))
        machine.reg_write(UC_X86_REG_ESP, STACK + 0x8000)
        machine.emu_start(0x421290, 0x421384, timeout=2000000, count=2000)
        if machine.reg_read(UC_X86_REG_EIP) != 0x421384:
            raise RuntimeError("Result oracle left its bounded code range")
        cash_out = struct.unpack("<I", machine.mem_read(0x4B8A18, 4))[0]
        rows = struct.unpack("<I", machine.mem_read(0x46A638, 4))[0]
        return cash_out, rows, machine.reg_read(UC_X86_REG_EDX)
