"""Unit tests for BMI calculation and SQLite persistence."""

import tempfile
import unittest
from pathlib import Path

from bmi_calculator import BMIStore, calculate_bmi, chart_points, is_valid_name


class TestBMICalculation(unittest.TestCase):
    def test_normal_category(self):
        value, category = calculate_bmi(68.5, 1.75)
        self.assertAlmostEqual(value, 22.37, places=2)
        self.assertEqual(category, "Normal")

    def test_category_boundaries(self):
        self.assertEqual(calculate_bmi(18.49, 1.0)[1], "Underweight")
        self.assertEqual(calculate_bmi(25, 1)[1], "Overweight")
        self.assertEqual(calculate_bmi(30, 1)[1], "Obese")

    def test_invalid_measurements(self):
        for weight, height in [(0, 1.7), (-2, 1.7), (70, 0), (70, -1), (float("inf"), 1.7), (70, float("nan"))]:
            with self.subTest(weight=weight, height=height):
                with self.assertRaises(ValueError):
                    calculate_bmi(weight, height)


class TestBMIStore(unittest.TestCase):
    def test_add_and_retrieve(self):
        with tempfile.TemporaryDirectory() as folder:
            store = BMIStore(Path(folder) / "test.db")
            store.add("Sam", 70, 1.75, 22.86, "Normal")
            self.assertEqual(store.users(), ["Sam"])
            self.assertEqual(len(store.history("Sam")), 1)


class TestNameAndChartHelpers(unittest.TestCase):
    def test_names_with_hyphen_and_apostrophe_are_accepted(self):
        for name in ["Mary-Ann", "O'Brien", "Jos\u00e9", "Vishal Kumar"]:
            self.assertTrue(is_valid_name(name), name)

    def test_bad_names_are_rejected(self):
        for name in ["", "Alex2", "---", "A@B"]:
            self.assertFalse(is_valid_name(name), name)

    def test_same_day_records_get_separate_chart_positions(self):
        records = [(22.0, "Normal", "2026-11-15T10:00:00"),
                   (23.0, "Normal", "2026-11-15T10:00:30"),
                   (24.0, "Normal", "2026-11-15T10:01:00")]
        positions, labels, values = chart_points(records)
        self.assertEqual(positions, [1, 2, 3])
        self.assertEqual(values, [22.0, 23.0, 24.0])
        self.assertEqual(labels[0], "11-15 10:00:00")


if __name__ == "__main__":
    unittest.main()
