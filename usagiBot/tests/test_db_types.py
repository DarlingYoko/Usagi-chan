from unittest import TestCase, mock

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


class TestEncryptionKeys(TestCase):
    def setUp(self) -> None:
        from cryptography.fernet import Fernet

        from usagiBot.db import types

        self.types = types
        self.Fernet = Fernet
        self.old_key = Fernet.generate_key().decode()
        self.new_key = Fernet.generate_key().decode()
        self.addCleanup(self.reset)

    def reset(self) -> None:
        self.types._fernet_instance = None

    def use_keys(self, value: str | None) -> None:
        self.reset()
        patcher = mock.patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        if value is None:
            os.environ.pop(self.types.KEY_ENV, None)
        else:
            os.environ[self.types.KEY_ENV] = value

    def test_wrong_key_raises_instead_of_leaking_ciphertext(self) -> None:
        token = self.Fernet(self.old_key.encode()).encrypt(b"cookie").decode()
        self.use_keys(self.new_key)

        with self.assertRaises(self.types.CredentialKeyError):
            self.types.EncryptedText().process_result_value(token, None)

    def test_rotation_reads_old_key_and_writes_new(self) -> None:
        old_token = self.Fernet(self.old_key.encode()).encrypt(b"cookie").decode()
        self.use_keys(f"{self.new_key},{self.old_key}")
        column = self.types.EncryptedText()

        self.assertEqual(column.process_result_value(old_token, None), "cookie")
        fresh = column.process_bind_param("cookie", None)
        self.assertEqual(self.Fernet(self.new_key.encode()).decrypt(fresh.encode()), b"cookie")

    def test_looks_encrypted(self) -> None:
        self.use_keys(self.new_key)
        token = self.types.EncryptedText().process_bind_param("x", None)

        self.assertTrue(self.types.looks_encrypted(token))
        self.assertFalse(self.types.looks_encrypted("plain_ltoken"))

    def test_missing_key_is_reported_at_boot(self) -> None:
        self.use_keys(None)

        with self.assertRaises(RuntimeError):
            self.types.ensure_encryption_key()

    def test_present_key_passes_boot_check(self) -> None:
        self.use_keys(self.new_key)

        self.types.ensure_encryption_key()
