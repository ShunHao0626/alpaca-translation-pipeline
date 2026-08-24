import unittest

from alpaca_translation.validate import validate_dataset


class ValidationTests(unittest.TestCase):
    def test_reports_remaining_chinese_fields(self):
        report = validate_dataset(
            [{"instruction": "Hello", "output": "回答"}, {"instruction": "English"}]
        )
        self.assertEqual(report["records"], 2)
        self.assertEqual(report["remaining_chinese_count"], 1)
        self.assertEqual(report["remaining_chinese_fields"][0]["field"], "output")


if __name__ == "__main__":
    unittest.main()
