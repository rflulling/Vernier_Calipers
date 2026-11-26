import tempfile
import unittest
from pathlib import Path

from caliper_core import (
    calculate_reading,
    converted_readings,
    corrected_reading,
    default_settings,
    load_settings,
    save_settings,
)


class CalculatorTests(unittest.TestCase):
    def test_digit_places_are_added_from_most_to_least_significant(self):
        self.assertAlmostEqual(calculate_reading([1, 8, 3, 0, 2]), 1.8302)

    def test_offset_direction_accounts_for_calibration_and_inner_jaw_fit(self):
        self.assertAlmostEqual(corrected_reading(10, 0.25, "past_zero"), 9.75)
        self.assertAlmostEqual(corrected_reading(10, 0.25, "not_reached"), 10.25)
        self.assertAlmostEqual(
            corrected_reading(10, 0.25, "not_reached", "gap", "Inner"), 9.75
        )
        self.assertAlmostEqual(
            corrected_reading(10, 0.25, "not_reached", "overlap", "Inner"), 10.25
        )

    def test_converts_in_both_directions(self):
        self.assertEqual(converted_readings(1, "in"), (1, 25.4))
        self.assertEqual(converted_readings(25.4, "mm"), (1, 25.4))

    def test_settings_are_sticky_and_corrupt_files_fall_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            settings = default_settings()
            settings["Inner"]["offset_in"] = -0.0123
            settings["Outer"]["scale_position"] = "past_zero"
            save_settings(path, settings)
            self.assertEqual(load_settings(path), settings)
            path.write_text("{", encoding="utf-8")
            self.assertEqual(load_settings(path), default_settings())


if __name__ == "__main__":
    unittest.main()
