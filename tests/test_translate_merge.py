import unittest

from alpaca_translation.merge import merge_translations
from alpaca_translation.translate import translate_candidates, translate_text


class FakeTranslator:
    def __init__(self):
        self.calls = 0

    def translate(self, text):
        self.calls += 1
        return {"你好": "Hello", "回答": "Answer"}[text]


class FlakyTranslator:
    def __init__(self):
        self.calls = 0

    def translate(self, text):
        self.calls += 1
        if self.calls == 1:
            raise ConnectionError("temporary")
        return "Hello"


class TranslationTests(unittest.TestCase):
    def test_retries_transient_failure(self):
        translator = FlakyTranslator()
        result = translate_text("你好", translator, sleep=lambda _: None)
        self.assertEqual(result, "Hello")
        self.assertEqual(translator.calls, 2)

    def test_resume_skips_existing_record(self):
        translator = FakeTranslator()
        candidates = {"0": {"instruction": "你好"}, "1": {"output": "回答"}}
        result = translate_candidates(
            candidates,
            translator,
            existing={"0": {"instruction": "Existing"}},
            delay=0,
        )
        self.assertEqual(result["0"]["instruction"], "Existing")
        self.assertEqual(result["1"]["output"], "Answer")
        self.assertEqual(translator.calls, 1)

    def test_merge_preserves_source_and_record_count(self):
        source = [{"instruction": "你好", "input": "context", "output": "回答"}]
        merged, report = merge_translations(
            source, {"0": {"instruction": "Hello", "output": "Answer"}}
        )
        self.assertEqual(source[0]["instruction"], "你好")
        self.assertEqual(merged[0]["input"], "context")
        self.assertEqual(report["changed_fields"], 2)
        self.assertTrue(report["record_count_preserved"])


if __name__ == "__main__":
    unittest.main()
