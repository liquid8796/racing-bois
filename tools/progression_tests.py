"""Explicit expected outcomes, invalid-input cases and repeat-entry regression."""
import dataclasses
import unittest
from unittest.mock import Mock
from legacy_progression import (
    FinishState, MediaState, ProgressionState, finish_request,
    offline_outcome_screen, result_media, acknowledge_result,
)


class FinishRequestTests(unittest.TestCase):
    def finish(self, rank, network_a=0, network_b=0, **overrides):
        values = dict(request_status=0x7F, delay_i32=0, rank_byte=rank,
                      network_a=network_a, network_b=network_b,
                      current_status=1, current_delay=0, current_latch=0)
        values.update(overrides)
        return finish_request(**values)

    def test_offline_top_three_boundary(self):
        self.assertEqual([self.finish(rank).status_u32 for rank in (0, 1, 2, 3, 13)], [2, 2, 2, 3, 3])

    def test_either_network_flag_changes_threshold(self):
        for flags in ((1, 0), (0, 1), (1, 1), (128, 0), (0, 255)):
            self.assertEqual(self.finish(0, *flags).status_u32, 2)
            self.assertEqual(self.finish(1, *flags).status_u32, 3)

    def test_signed_rank_byte_is_explicit_not_safe_production_behavior(self):
        self.assertEqual(self.finish(127).status_u32, 3)
        self.assertEqual(self.finish(128).status_u32, 2)
        self.assertEqual(self.finish(255, 1, 0).status_u32, 2)

    def test_positive_delay_does_not_set_latch(self):
        self.assertEqual(self.finish(0, delay_i32=7), FinishState(2, 7, 0))

    def test_nonpositive_delay_sets_latch_without_negative_countdown(self):
        for delay in (0, -1, -2**31):
            self.assertEqual(self.finish(0, delay_i32=delay), FinishState(2, 0, 1))

    def test_pending_countdown_suppresses_request(self):
        for delay in (-1, 1, 2**31-1):
            self.assertEqual(self.finish(0, current_status=4, current_delay=delay), FinishState(4, delay, 0))

    def test_any_nonzero_latch_suppresses_request(self):
        for latch in (1, 2, 128, 255):
            self.assertEqual(self.finish(0, current_status=4, current_latch=latch), FinishState(4, 0, latch))

    def test_explicit_outcome_bypasses_rank_classification(self):
        for status in (0, 1, 2, 3, 4, 0xFFFFFFFF):
            self.assertEqual(self.finish(0, request_status=status).status_u32, status)

    def test_second_immediate_request_is_ignored(self):
        first = self.finish(2)
        second = self.finish(0, request_status=4, current_status=first.status_u32,
                             current_delay=first.countdown_i32, current_latch=first.exit_latch)
        self.assertEqual(first, second)

    def test_invalid_input_rejected(self):
        for changes in ({'rank_byte': 256}, {'rank_byte': True}, {'network_a': -1},
                        {'delay_i32': 2**31}, {'current_status': -1}, {'current_latch': '1'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                rank = changes.get('rank_byte', 0)
                self.finish(rank, **{key: value for key, value in changes.items() if key != 'rank_byte'})

    def test_state_is_immutable(self):
        with self.assertRaises(dataclasses.FrozenInstanceError):
            self.finish(0).exit_latch = 0


class ResultFlowTests(unittest.TestCase):
    def test_offline_outcome_screen_ids(self):
        self.assertEqual([offline_outcome_screen(2, status) for status in (1, 2, 3, 4)], [28, 30, 31, 29])

    def test_mode_zero_returns_menu_regardless_of_status(self):
        for status in (0, 2, 3, 4, 0xFFFFFFFF):
            self.assertEqual(offline_outcome_screen(0, status), 9)

    def test_qualification_sets_each_course_bit(self):
        for course in range(1, 6):
            self.assertEqual(result_media(30, 2, 0, 0, course), MediaState(1 << (course - 1), 'Win', 6))

    def test_repeated_course_is_idempotent(self):
        self.assertEqual(result_media(30, 2, 0, 4, 3).qualification_mask, 4)

    def test_fifth_distinct_course_selects_level_video(self):
        self.assertEqual(result_media(30, 2, 0, 15, 5), MediaState(31, 'Level', 6))

    def test_final_level_selects_final_video_not_level_six(self):
        self.assertEqual(result_media(30, 2, 4, 15, 5), MediaState(31, 'FinalWin', 0))

    def test_other_outcomes_do_not_qualify(self):
        for screen, prefix, count in ((28, 'Wreck', 6), (29, 'Busted', 6), (31, 'Lose', 10)):
            self.assertEqual(result_media(screen, 2, 4, 15, 5), MediaState(15, prefix, count))

    def test_mode_three_accepts_zero_course_without_setting_bit(self):
        self.assertEqual(result_media(30, 3, 0, 15, 0), MediaState(15, 'Win', 6))

    def test_completion_selection_still_checks_mask_in_mode_three(self):
        self.assertEqual(result_media(30, 3, 4, 31, 0), MediaState(31, 'FinalWin', 0))

    def test_upper_mask_bits_do_not_count_as_exact_completion(self):
        self.assertEqual(result_media(30, 2, 4, 255, 5).prefix, 'Win')
        self.assertEqual(acknowledge_result(1, 2, 4, 255, 1, 0).qualification_mask, 255)

    def test_invalid_qualifying_course_rejected(self):
        for mode in (0, 1, 2):
            for course in (0, 6, 128, 255):
                with self.subTest(mode=mode, course=course), self.assertRaises(ValueError):
                    result_media(30, mode, 0, 0, course)

    def test_acknowledgement_zero_changes_nothing(self):
        self.assertEqual(acknowledge_result(0, 2, 0, 31, 1, 8), ProgressionState(0, 31, 8, 0, 'return'))

    def test_advance_clears_mask_and_sets_raw_dirty_field(self):
        self.assertEqual(acknowledge_result(1, 2, 0, 31, 1, 0), ProgressionState(1, 0, 1, 32, 'return'))

    def test_final_acknowledgement_stays_on_fifth_level(self):
        self.assertEqual(acknowledge_result(1, 2, 4, 31, 1, 0), ProgressionState(4, 0, 1, 35, 'return'))

    def test_second_acknowledgement_does_not_advance_again(self):
        first = acknowledge_result(1, 2, 0, 31, 1, 0)
        second = acknowledge_result(1, 2, first.level_index, first.qualification_mask, 1, first.dirty_byte)
        self.assertEqual(second, ProgressionState(1, 0, 1, 15, 'return'))

    def test_completion_check_precedes_mode_dispatch(self):
        for mode in (0, 1, 3):
            self.assertEqual(acknowledge_result(1, mode, 0, 31, 1, 0).level_index, 1)

    def test_incomplete_mode_dispatch_and_character_zero(self):
        self.assertEqual(acknowledge_result(1, 0, 0, 0, 0, 0).next_screen, 9)
        self.assertEqual(acknowledge_result(1, 1, 0, 0, 0, 0).next_screen, 10)
        self.assertEqual(acknowledge_result(1, 2, 0, 0, 0, 0).next_screen, 14)
        self.assertEqual(acknowledge_result(1, 2, 0, 0, 255, 0).next_screen, 15)

    def test_network_callback_is_not_claimed_as_executed(self):
        self.assertEqual(acknowledge_result(1, 3, 2, 7, 0, 0), ProgressionState(2, 7, 0, None, 'network_callback'))

    def test_invalid_model_domains(self):
        for function, values in (
            (offline_outcome_screen, (4, 2)), (offline_outcome_screen, (2, -1)),
            (result_media, (27, 2, 0, 0, 1)), (result_media, (30, 2, 5, 0, 1)),
            (result_media, (30, 2, 0, 256, 1)), (acknowledge_result, (True, 2, 0, 0, 0, 0)),
            (acknowledge_result, (1, 2, -1, 0, 0, 0)), (acknowledge_result, (1, 2, 0, 0, 0, 256)),
        ):
            with self.subTest(function=function.__name__, values=values), self.assertRaises(ValueError):
                function(*values)


class NativeBoundaryTests(unittest.TestCase):
    def test_invalid_inputs_rejected_before_emulator_allocation(self):
        from progression_oracle import ProgressionOracle
        oracle = ProgressionOracle.__new__(ProgressionOracle)
        oracle.core = Mock()
        for method, values in (
            ('finish_request', (127, 0, 256, 0, 0, 1, 0, 0)),
            ('offline_outcome_screen', (4, 2)),
            ('result_media', (30, 2, 0, 0, 0)),
            ('acknowledge_result', (1, 2, 5, 0, 0, 0)),
        ):
            with self.subTest(method=method), self.assertRaises(ValueError):
                getattr(oracle, method)(*values)
        oracle.core.machine.assert_not_called()

    def test_unexpected_native_stop_is_failure(self):
        from progression_oracle import ProgressionOracle
        machine = Mock()
        machine.reg_read.return_value = 0xDEADBEEF
        with self.assertRaises(RuntimeError):
            ProgressionOracle._execute(machine, 0x416010, 0x416079)


class EvidenceIntegrityTests(unittest.TestCase):
    def test_same_inputs_accepted(self):
        from validate_progression import require_unchanged_inputs
        before = {'tool_version': '0.1.21', 'scripts': {'model': 'abc'}}
        require_unchanged_inputs(before, dict(before))

    def test_version_drift_rejected(self):
        from validate_progression import require_unchanged_inputs
        with self.assertRaises(RuntimeError):
            require_unchanged_inputs({'tool_version': '0.1.21'}, {'tool_version': '0.1.22'})

    def test_script_drift_rejected(self):
        from validate_progression import require_unchanged_inputs
        with self.assertRaises(RuntimeError):
            require_unchanged_inputs({'scripts': {'model': 'abc'}}, {'scripts': {'model': 'xyz'}})

    def test_runner_fails_drift_even_when_native_result_matches(self):
        import contextlib
        import io
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        import validate_progression as runner
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'RacingBois.exe').write_bytes(b'synthetic oracle fixture')
            out = root / 'evidence'
            before = {'tool_version': '0.1.21', 'scripts': {'model': 'abc'}}
            after = {'tool_version': '0.1.22', 'scripts': {'model': 'abc'}}
            fake = Mock()
            fake.offline_outcome_screen.return_value = 30
            manifest = [{'path': 'RacingBois.exe', 'sha256': 'synthetic', 'bytes': 24}]
            with patch.object(runner, 'validate_paths', return_value=(root, out)), \
                 patch.object(runner, 'inventory', return_value=manifest), \
                 patch.object(runner, 'tool_inputs', side_effect=[before, after]), \
                 patch.object(runner, 'ProgressionOracle', return_value=fake), \
                 patch.object(runner, 'cases', return_value=iter([('offline_outcome_screen', (2, 2))])), \
                 patch.object(runner, 'sequence_cases', return_value=iter([])), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(runner.run(root, out), 1)
            summary = json.loads((out / 'summary.json').read_text())
            self.assertEqual(summary['matches'], 1)
            self.assertFalse(summary['passed'])
            self.assertFalse(summary['tool_inputs_unchanged'])
            self.assertEqual(summary['tool_version'], '0.1.21')

if __name__ == '__main__':
    unittest.main(verbosity=2)
