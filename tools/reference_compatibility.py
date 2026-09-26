"""Explicit, reversible compatibility files for the private research copy only."""
from __future__ import annotations

import hashlib
import time
import zipfile
from pathlib import Path

ARCHIVE_SHA = "0b13ab89a64c9918189b1dadd449ef6ed3cb3b7b19cabd96d8adbd95505bb908"
DLL_SHA = "85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9"
CONFIG = """[ddraw]
width=640
height=480
windowed=true
fullscreen=false
maintas=true
renderer=gdi
devmode=true
border=true
savesettings=0
resizable=false
maxgameticks=-1
singlecpu=false
maxfps=60
vsync=false
adjmouse=true
nonexclusive=true
minfps=0
shader=
"""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class FileLease:
    """Create new files only; remove only files still matching our own bytes."""

    def __init__(self, directory: Path, files: dict[str, bytes]):
        self.directory = directory.resolve(strict=True)
        self.files = files
        self.created: dict[Path, str] = {}
        for name in files:
            if Path(name).name != name or name in (".", ".."):
                raise ValueError("Lease files must be plain basenames")
            path = self.directory / name
            if path.exists() or path.is_symlink():
                raise FileExistsError(f"Refusing existing compatibility file: {name}")

    def install(self) -> None:
        if self.created:
            raise RuntimeError("Lease already installed")
        try:
            for name, content in self.files.items():
                path = self.directory / name
                with path.open("xb") as stream:
                    # Keep partial writes identifiable even when an I/O error occurs.
                    try:
                        stream.write(content)
                    finally:
                        stream.flush()
                        self.created[path] = digest(path.read_bytes())
        except Exception:
            self.cleanup()
            raise

    def cleanup(self) -> list[str]:
        errors = []
        for path, expected in list(self.created.items()):
            try:
                if not path.exists():
                    del self.created[path]
                elif path.is_symlink() or digest(path.read_bytes()) != expected:
                    errors.append(f"Preserved modified compatibility file: {path.name}")
                else:
                    # Windows can release an image mapping slightly after process exit.
                    for attempt in range(11):
                        try:
                            path.unlink()
                            break
                        except PermissionError:
                            if attempt == 10:
                                raise
                            time.sleep(0.2)
                            if path.is_symlink() or digest(path.read_bytes()) != expected:
                                raise RuntimeError(f"File changed during cleanup: {path.name}")
                    del self.created[path]
            except (OSError, RuntimeError) as error:
                errors.append(f"Compatibility cleanup {path.name}: {error}")
        return errors


def prepare_cnc_ddraw(root: Path, sandbox: Path) -> tuple[FileLease, dict]:
    """No network download or executable launch is performed by this helper."""
    expected = (root / "ReferenceOnly/runtime-sandbox").resolve(strict=True)
    if sandbox.resolve(strict=True) != expected:
        raise ValueError("Compatibility target is not the designated private copy")
    upstream = root / ".tools/cnc-ddraw-v7.1.0.0"
    archive = upstream / "cnc-ddraw.zip"
    if archive.stat().st_size > 10 * 1024 * 1024 or digest(archive.read_bytes()) != ARCHIVE_SHA:
        raise ValueError("Unknown compatibility archive")
    with zipfile.ZipFile(archive) as zipped:
        if zipped.getinfo("ddraw.dll").file_size != 411648:
            raise ValueError("Unexpected DirectDraw DLL size")
        dll = zipped.read("ddraw.dll")
    if digest(dll) != DLL_SHA:
        raise ValueError("Unknown DirectDraw DLL")
    license_data = (upstream / "LICENSE").read_bytes()
    if b"MIT License" not in license_data or b"Copyright (c) 2022" not in license_data:
        raise ValueError("Missing tag-matched compatibility license")
    files = {"ddraw.dll": dll, "ddraw.ini": CONFIG.encode("ascii"),
             "cnc-ddraw-LICENSE.txt": license_data}
    lease = FileLease(expected, files)
    return lease, {"name": "cnc-ddraw", "version": "7.1.0.0",
                   "archive_sha256": ARCHIVE_SHA, "dll_sha256": DLL_SHA,
                   "configuration": CONFIG, "game_tick_limiter": "disabled",
                   "scope": "private compatibility experiment; not native timing"}
