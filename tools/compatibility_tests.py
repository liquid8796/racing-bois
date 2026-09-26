"""No proprietary payloads or live process required for file-ownership tests."""
import tempfile
import unittest
from pathlib import Path
from reference_compatibility import FileLease, CONFIG


class LeaseTests(unittest.TestCase):
    def test_round_trip_preserves_other_files(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); (root / "keep.txt").write_text("keep")
            lease = FileLease(root, {"ddraw.ini": b"config"})
            lease.install()
            self.assertEqual((root / "ddraw.ini").read_bytes(), b"config")
            self.assertEqual(lease.cleanup(), [])
            self.assertEqual(lease.cleanup(), [])
            self.assertEqual((root / "keep.txt").read_text(), "keep")
            self.assertFalse((root / "ddraw.ini").exists())

    def test_existing_file_refused(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); (root / "ddraw.dll").write_bytes(b"owned by user")
            with self.assertRaises(FileExistsError):
                FileLease(root, {"ddraw.dll": b"replacement"})
            self.assertEqual((root / "ddraw.dll").read_bytes(), b"owned by user")

    def test_modified_file_retained(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); lease = FileLease(root, {"ddraw.ini": b"initial"})
            lease.install(); (root / "ddraw.ini").write_bytes(b"changed")
            self.assertEqual(len(lease.cleanup()), 1)
            self.assertEqual((root / "ddraw.ini").read_bytes(), b"changed")

    def test_escaped_name_refused(self):
        with tempfile.TemporaryDirectory() as name:
            with self.assertRaises(ValueError):
                FileLease(Path(name), {"../outside": b"bad"})

    def test_no_game_tick_limiter(self):
        self.assertIn("maxgameticks=-1\n", CONFIG)
        self.assertIn("windowed=true\n", CONFIG)
        self.assertIn("savesettings=0\n", CONFIG)


if __name__ == "__main__":
    unittest.main(verbosity=2)
