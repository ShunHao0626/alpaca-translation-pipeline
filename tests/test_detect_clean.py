import unittest

from alpaca_translation.clean import clean_candidates
from alpaca_translation.detect import contains_chinese, detect_candidates


class DetectionTests(unittest.TestCase):
    def test_detects_chinese_and_ignores_english(self):
        self.assertTrue(contains_chinese("解释这个概念"))
        self.assertFalse(contains_chinese("Explain this concept"))

    def test_candidates_preserve_record_indices(self):
        records = [
            {"instruction": "English", "output": "Answer"},
            {"instruction": "翻译这个句子", "output": "Translate it"},
        ]
        self.assertEqual(detect_candidates(records), {"1": {"instruction": "翻译这个句子"}})

    def test_clean_removes_non_chinese_fields(self):
        candidates = {"01": {"instruction": "你好", "output": "English"}}
        self.assertEqual(clean_candidates(candidates), {"1": {"instruction": "你好"}})


if __name__ == "__main__":
    unittest.main()
