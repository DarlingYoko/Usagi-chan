import json
from unittest import TestCase

from usagiBot.tests.utils import *


def _load(lang):
    with open(f"usagiBot/files/language/{lang}.json", encoding="utf-8") as f:
        return json.load(f)


class TestI18nCrashSites(TestCase):
    """Keys referenced in code that previously raised InvalidTranslationKeyError."""

    REQUIRED_KEYS = [
        "This emoji already used",          # Main edit_emoji_reaction_role
        "VPN no profiles",                  # VPN request_renew_vpn
        "Invalid date",                     # Birthdays birthday_add
        "You already have a unic role",     # Tech create_new_unic_role
        "I don't have permissions to do that",  # Events on_command_error (repointed)
        "Some requirements were not met",       # Events on_application_command_error
        "This user isn't in birthday list",     # Birthdays birthday_remove (repointed)
    ]

    def setUp(self) -> None:
        self.en = _load("en")
        self.ru = _load("ru")

    def test_required_keys_present_in_en(self) -> None:
        missing = [k for k in self.REQUIRED_KEYS if k not in self.en]
        self.assertEqual(missing, [], f"missing en keys: {missing}")

    def test_required_keys_present_in_ru(self) -> None:
        missing = [k for k in self.REQUIRED_KEYS if k not in self.ru]
        self.assertEqual(missing, [], f"missing ru keys: {missing}")

    def test_en_ru_parity(self) -> None:
        self.assertEqual(
            set(self.en) - set(self.ru), set(), "keys in en missing from ru"
        )
        self.assertEqual(
            set(self.ru) - set(self.en), set(), "keys in ru missing from en"
        )
