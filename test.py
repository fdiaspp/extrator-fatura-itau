"""
This module tests some functions in lambda_function.py
"""

from main import find_date
import unittest



class TestFindDate(unittest.TestCase):
    def test_valid_date(self):
        self.assertIsNotNone(find_date("01/01"))
        self.assertIsNotNone(find_date("02/29"))
        self.assertIsNotNone(find_date("12/31"))

    def test_invalid_date(self):
        self.assertIsNone(find_date("01/02/2022"))
        self.assertIsNone(find_date("01-01"))
        self.assertIsNone(find_date("01/01/2022"))



if __name__ == "__main__":
    unittest.main()