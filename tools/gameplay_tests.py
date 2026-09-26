"""Synthetic tests; full byte-code comparisons are in validate_gameplay.py."""
import unittest
from legacy_gameplay import BIKE_NAME_IDS, bike_name_id, result_screen_state


class GameplayModelTests(unittest.TestCase):
    def test_name_mapping_is_permutation(self):
        self.assertEqual(set(BIKE_NAME_IDS), set(range(112, 127)))
    def test_internal_order_is_not_showroom_order(self):
        self.assertEqual(bike_name_id(6), 125)
        self.assertEqual(bike_name_id(10), 117)
    def test_unknown_byte_preserves_legacy_fallback(self):
        for index in range(15, 256):
            self.assertEqual(bike_name_id(index), 112)
    def test_bad_index_rejected(self):
        for value in [-1, 256, True, 1.5, "1"]:
            with self.subTest(value=value), self.assertRaises(ValueError): bike_name_id(value)
    def test_first_level_first_place(self):
        self.assertEqual(result_screen_state(2, 0, 0, 50).cash_u32, 1050)
    def test_fifth_level_last_place(self):
        self.assertEqual(result_screen_state(2, 4, 13, 50).cash_u32, 150)
    def test_noncareer_does_not_credit_cash(self):
        for mode in [1, 3]: self.assertEqual(result_screen_state(mode, 4, 0, 50).cash_u32, 50)
    def test_legacy_unsigned_wrap_is_explicit(self):
        self.assertEqual(result_screen_state(2, 0, 0, 0xFFFFFFFF).cash_u32, 999)
    def test_display_rows_and_selection(self):
        self.assertEqual(result_screen_state(2, 0, 2, 0).displayed_rows, 3)
        self.assertEqual(result_screen_state(2, 0, 13, 0).selected_row, 3)
        self.assertEqual(result_screen_state(3, 0, 13, 0, 3).selected_row, 0)
    def test_out_of_range_inputs_rejected(self):
        for values in [(0,0,0,0), (2,-1,0,0), (2,0,14,0), (2,0,0,-1)]:
            with self.subTest(values=values), self.assertRaises(ValueError): result_screen_state(*values)


if __name__ == "__main__": unittest.main(verbosity=2)
