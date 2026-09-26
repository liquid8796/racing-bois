"""Reproducible native comparisons; all raw evidence remains private/local.

Each boundary has a separate pure model. Exceptions fail, never skip, cases.
A completed evidence run never silently overwrites another run.
"""
from __future__ import annotations
import argparse
import collections
import dataclasses
import datetime
import hashlib
import json
import random
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import legacy_progression as models
from progression_oracle import ProgressionOracle
from native_oracle import EXE_SHA
from validate_phase0 import inventory, save, validate_paths, ROOT, DEFAULT

BOUNDARIES = {
    'finish_request': '0x416010 -> 0x416079 or guarded epilogue 0x4160b6; notification excluded',
    'offline_outcome_screen': '0x416237 -> return; synthetic tail stack, CL=DL=0',
    'result_media': '0x449150 -> 0x4491eb; media call excluded',
    'acknowledge_result': '0x41f6d0 -> return or BEFORE network call 0x41f735',
}


def normalize(value):
    if dataclasses.is_dataclass(value):
        return list(dataclasses.astuple(value))
    if isinstance(value, tuple):
        return list(value)
    return value


def tool_inputs(root: Path = ROOT) -> dict:
    """Fingerprint version and research dependencies before AND after a run."""
    props = (root / "Directory.Build.props").read_bytes()
    names = ("legacy_progression.py", "progression_oracle.py", "validate_progression.py",
             "native_oracle.py", "validate_phase0.py", "research_formats.py", "mids_reference.py")
    return {"tool_version": ET.fromstring(props).findtext(".//Version"),
            "version_file_sha256": hashlib.sha256(props).hexdigest(),
            "scripts": {name: hashlib.sha256((root / "tools" / name).read_bytes()).hexdigest()
                        for name in names}}


def require_unchanged_inputs(before: dict, after: dict) -> None:
    if before != after:
        raise RuntimeError("Research sources or tool version changed during the run; evidence is invalid")


def cases():
    for rank in range(256):
        for a, b in ((0, 0), (1, 0), (0, 1), (1, 1)):
            yield 'finish_request', (127, 0, rank, a, b, 1, 0, 0)
    for request in (0, 1, 2, 3, 4, 127, 0xFFFFFFFF):
        for delay in (-2**31, -1, 0, 1, 2**31-1):
            for pending, latch in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, 255), (5, 128)):
                yield 'finish_request', (request, delay, 2, 0, 255, 4, pending, latch)
    for mode in range(4):
        for status in (*range(256), 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
            yield 'offline_outcome_screen', (mode, status)
    for mask in range(32):
        for course in range(1, 6):
            for level in range(5):
                for mode in (2, 3):
                    yield 'result_media', (30, mode, level, mask, course)
    for mode in (0, 1):
        for mask in (0, 30, 31):
            for course in range(1, 6):
                for level in (0, 4):
                    yield 'result_media', (30, mode, level, mask, course)
    for screen in (28, 29, 31):
        for mode in range(4):
            for mask in (0, 31, 255):
                for level in (0, 4):
                    yield 'result_media', (screen, mode, level, mask, 0)
    for mask in range(32, 256):
        yield 'result_media', (30, 2, 4, mask, 5)
    for mask in range(32):
        for level in range(5):
            yield 'result_media', (30, 3, level, mask, 0)
    for mask in range(32):
        for level in range(5):
            for mode in range(4):
                for ack in (0, 1):
                    yield 'acknowledge_result', (ack, mode, level, mask, mask % 2, (mask * 7) % 256)
    for character in range(256):
        yield 'acknowledge_result', (1, 2, 0, 0, character, 0)
    for mask in range(32, 256):
        yield 'acknowledge_result', (1, 2, 4, mask, 1, 255)
    rng = random.Random(20260926)
    for _ in range(120):
        yield 'finish_request', (rng.choice((127, 2, 3, 4)), rng.randrange(-100, 100),
            rng.randrange(256), rng.randrange(256), rng.randrange(256), rng.randrange(2**32),
            rng.choice((0, 0, -1, 1)), rng.choice((0, 0, 0, 255)))


def sequence_cases(oracle):
    """Synthetic call-boundary chains, NOT recorded races or full runtime tests."""
    for initial_level in (0, 3, 4):
        expected_level = actual_level = initial_level
        expected_mask = actual_mask = 0
        expected_dirty = actual_dirty = 0
        rows = []
        for course, rank in ((1, 2), (1, 0), (2, 3), (2, 2), (3, 1), (4, 0), (5, 2)):
            expected_finish = models.finish_request(127, 0, rank, 0, 0, 1, 0, 0)
            actual_finish = oracle.finish_request(127, 0, rank, 0, 0, 1, 0, 0)
            expected_screen = models.offline_outcome_screen(2, expected_finish.status_u32)
            actual_screen = oracle.offline_outcome_screen(2, actual_finish[0])
            expected_media = models.result_media(expected_screen, 2, expected_level, expected_mask, course)
            actual_media = oracle.result_media(actual_screen, 2, actual_level, actual_mask, course)
            expected_advance = models.acknowledge_result(1, 2, expected_level, expected_media.qualification_mask, 1, expected_dirty)
            actual_advance = oracle.acknowledge_result(1, 2, actual_level, actual_media[0], 1, actual_dirty)
            rows.append(dict(course=course, rank=rank,
                expected=[normalize(expected_finish), expected_screen, normalize(expected_media), normalize(expected_advance)],
                actual=[normalize(actual_finish), actual_screen, normalize(actual_media), normalize(actual_advance)]))
            expected_level, expected_mask, expected_dirty = expected_advance.level_index, expected_advance.qualification_mask, expected_advance.dirty_byte
            actual_level, actual_mask, actual_dirty = actual_advance[:3]
        yield dict(kind='synthetic_sequence', input=dict(initial_level=initial_level), steps=rows,
                   match=all(row['expected'] == row['actual'] for row in rows))


def run(source: Path, out: Path) -> int:
    source, out = validate_paths(source, out)
    out.mkdir(parents=True, exist_ok=False)
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    inputs_before = tool_inputs()
    before = inventory(source)
    rows, errors = [], []
    try:
        executable = (source / 'RacingBois.exe').read_bytes()
        oracle = ProgressionOracle(executable)
        for kind, values in cases():
            row = dict(kind=kind, input=values, boundary=BOUNDARIES[kind], match=False)
            try:
                row['expected'] = normalize(getattr(models, kind)(*values))
                row['actual'] = normalize(getattr(oracle, kind)(*values))
                row['match'] = row['actual'] == row['expected']
            except Exception as error:
                row['error'] = f'{type(error).__name__}: {error}'
            rows.append(row)
            if len(rows) % 500 == 0:
                print(f"Compared {len(rows)} isolated cases", flush=True)
        rows.extend(sequence_cases(oracle))
    except Exception as error:
        errors.append(f'{type(error).__name__}: {error}')
    after = inventory(source)
    inputs_after = tool_inputs()
    try:
        require_unchanged_inputs(inputs_before, inputs_after)
    except RuntimeError as error:
        errors.append(str(error))
    failures = [row for row in rows if not row['match']]
    counts = dict(collections.Counter(row['kind'] for row in rows))
    summary = dict(run_id=stamp, tool_version=inputs_before['tool_version'],
        expected_executable_sha256=EXE_SHA,
        executable_sha256=next((row['sha256'] for row in before if row['path'] == 'RacingBois.exe'), None),
        script_sha256=inputs_before['scripts'], tool_inputs_unchanged=inputs_before == inputs_after,
        cases=len(rows), counts=counts,
        matches=len(rows)-len(failures), failure_count=len(failures), errors=errors,
        source_unchanged=before == after, source_files=len(before),
        passed=bool(rows) and not failures and not errors and before == after,
        scope='Four isolated code boundaries plus synthetic call chains. No finish-line detection, race execution, native timing, media playback, persistence or networking is established.')
    save(out/'inventory-before.json', before)
    save(out/'inventory-after.json', after)
    save(out/'tool-inputs-before.json', inputs_before)
    save(out/'tool-inputs-after.json', inputs_after)
    save(out/'native_cases.json', rows)
    save(out/'failures.json', failures)
    save(out/'summary.json', summary)
    print(json.dumps(summary, indent=2))
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=DEFAULT)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    sys.exit(run(args.source, args.out))
