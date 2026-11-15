"""Unit tests for secure password generation."""

import unittest
from password_generator import AMBIGUOUS, CHARACTER_GROUPS, estimate_strength, generate_password


class TestPasswordGenerator(unittest.TestCase):
    def test_length_and_required_character_groups(self):
        selected = ["uppercase", "lowercase", "digits", "symbols"]
        password = generate_password(24, selected)
        self.assertEqual(len(password), 24)
        for key in selected:
            self.assertTrue(any(char in CHARACTER_GROUPS[key] for char in password))

    def test_excludes_ambiguous_characters(self):
        password = generate_password(30, ["uppercase", "lowercase", "digits"], True)
        self.assertTrue(set(password).isdisjoint(AMBIGUOUS))

    def test_invalid_length_and_types(self):
        with self.assertRaises(ValueError):
            generate_password(7, ["uppercase", "lowercase"])
        with self.assertRaises(ValueError):
            generate_password(12, ["uppercase"])

    def test_strength_estimate(self):
        self.assertEqual(estimate_strength(20, 4)[0], "Strong")

    def test_long_two_type_password_is_strong(self):
        self.assertEqual(estimate_strength(128, 2)[0], "Strong")

    def test_short_passwords_are_not_strong(self):
        self.assertEqual(estimate_strength(8, 2)[0], "Weak")
        self.assertEqual(estimate_strength(12, 2)[0], "Medium")


if __name__ == "__main__":
    unittest.main()
