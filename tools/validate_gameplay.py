"""Read-only independent native checks with versioned, reproducible evidence."""
from __future__ import annotations
import argparse, dataclasses, datetime, hashlib, json, random, sys, xml.etree.ElementTree as ET
from pathlib import Path
from gameplay_oracle import GameplayOracle
from legacy_gameplay import bike_name_id, result_screen_state
from native_oracle import EXE_SHA
from validate_phase0 import inventory, save, validate_paths, ROOT, DEFAULT


def run(source: Path, out: Path) -> int:
    source, out = validate_paths(source, out)
    if out.exists(): raise ValueError("Use a new output directory; preserve prior evidence")
    before = inventory(source)
    executable = (source / "RacingBois.exe").read_bytes()
    oracle = GameplayOracle(executable)
    cases = []
    for index in range(256):
        actual = oracle.bike_name(index)
        expected = bike_name_id(index)
        cases.append(dict(kind="bike_name", input=index, actual=actual, expected=expected, match=actual == expected))
    rng = random.Random(20260926)
    inputs = [(mode, level, place, cash, 15)
              for mode in (1, 2, 3) for level in range(5) for place in range(14)
              for cash in (0, 0xFFFFFFFF)]
    inputs += [(3, 4, place, 1234, field) for field in (2, 3, 4, 8) for place in range(14)]
    inputs += [(rng.randrange(1,4), rng.randrange(256), rng.randrange(14), rng.randrange(2**32), rng.randrange(2,16)) for _ in range(100)]
    for values in inputs:
        actual = oracle.result_screen(*values)
        state = result_screen_state(*values)
        expected = (state.cash_u32, state.displayed_rows, state.selected_row)
        cases.append(dict(kind="result_screen", input=values, actual=actual, expected=expected, match=actual == expected))
    after = inventory(source)
    failures = [case for case in cases if not case["match"]]
    summary = dict(run_id=datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
                   tool_version=ET.parse(ROOT / "Directory.Build.props").findtext(".//Version"),
                   executable_sha256=EXE_SHA, source_unchanged=before == after,
                   cases=len(cases), bike_name_cases=256, result_cases=len(inputs),
                   matches=len(cases)-len(failures), failures=failures, passed=not failures and before == after,
                   scope="Two bounded native routines. Result-screen entry precondition is assumed; finish/DNF/reentry/persistence and full gameplay remain unverified.")
    save(out / "inventory.json", before)
    save(out / "native_cases.json", cases)
    save(out / "summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    sys.exit(run(args.source, args.out))
