import json
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
            for index, tool in enumerate(("Inner", "Outer", "Probe"), 1):
                settings[tool]["offset_in"] = -index * 0.0123
                settings[tool]["offset_mm"] = index * 0.123
            settings["Outer"]["scale_position"] = "past_zero"
            save_settings(path, settings)
            self.assertEqual(load_settings(path), settings)
            path.write_text("{", encoding="utf-8")
            self.assertEqual(load_settings(path), default_settings())

    def test_existing_settings_gain_default_probe_without_losing_offsets(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            old_settings = default_settings()
            del old_settings["Probe"]
            old_settings["Inner"]["offset_in"] = 0.125
            old_settings["Outer"]["offset_mm"] = -0.25
            save_settings(path, old_settings)
            settings = load_settings(path)
            self.assertEqual(settings["Inner"], old_settings["Inner"])
            self.assertEqual(settings["Outer"], old_settings["Outer"])
            self.assertEqual(settings["Probe"], default_settings()["Probe"])

    def test_probe_uses_scale_direction(self):
        self.assertAlmostEqual(corrected_reading(10, 0.25, "past_zero", tool="Probe"), 9.75)
        self.assertAlmostEqual(corrected_reading(10, 0.25, "not_reached", tool="Probe"), 10.25)

    def test_legacy_offsets_are_migrated_to_signed_corrections(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            legacy = default_settings()
            for tool in legacy:
                legacy[tool].update(offset_in=0.1, offset_mm=-0.2, scale_position="past_zero")
            path.write_text(json.dumps(legacy), encoding="utf-8")
            settings = load_settings(path)
            for tool in legacy:
                for key in ("offset_in", "offset_mm"):
                    self.assertAlmostEqual(
                        settings[tool][key],
                        corrected_reading(0, legacy[tool][key], "past_zero", "gap", tool),
                    )
            save_settings(path, settings)
            self.assertEqual(load_settings(path), settings)


if __name__ == "__main__":
    unittest.main()
