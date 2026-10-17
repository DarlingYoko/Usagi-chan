from unittest import TestCase

from usagiBot.tests.utils import *


class TestEncryptedText(TestCase):
    def setUp(self) -> None:
        from usagiBot.db.types import EncryptedText

        self.column_type = EncryptedText()

    def test_bind_encrypts_value(self) -> None:
        token = self.column_type.process_bind_param("ltoken_secret", None)

        self.assertIsNotNone(token)
        self.assertNotEqual(token, "ltoken_secret")
        self.assertNotIn("ltoken_secret", token)

    def test_roundtrip(self) -> None:
        token = self.column_type.process_bind_param("ltoken_secret", None)
        restored = self.column_type.process_result_value(token, None)

        self.assertEqual(restored, "ltoken_secret")

    def test_legacy_plaintext_passes_through(self) -> None:
        restored = self.column_type.process_result_value("old_plaintext_token", None)

        self.assertEqual(restored, "old_plaintext_token")

    def test_none_stays_none(self) -> None:
        self.assertIsNone(self.column_type.process_bind_param(None, None))
        self.assertIsNone(self.column_type.process_result_value(None, None))
