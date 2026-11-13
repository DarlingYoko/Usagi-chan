import os

from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator

KEY_ENV = "CREDENTIALS_ENCRYPTION_KEY"

# Every Fernet token is base64 of a 0x80 version byte plus a timestamp,
# so it always starts like this; plaintext cookies/tokens/uuids never do.
FERNET_TOKEN_PREFIX = "gAAAAA"

_fernet_instance: MultiFernet | None = None


class CredentialKeyError(RuntimeError):
    """A stored credential is encrypted with a key that isn't configured."""


def _fernet() -> MultiFernet:
    """
    Keys come from CREDENTIALS_ENCRYPTION_KEY, comma-separated. The first
    one encrypts; all of them decrypt — prepend a new key to rotate, keep
    the old one until every row has been rewritten.
    """
    global _fernet_instance
    if _fernet_instance is None:
        raw = os.environ.get(KEY_ENV, "")
        keys = [key.strip() for key in raw.split(",") if key.strip()]
        if not keys:
            raise RuntimeError(
                f"{KEY_ENV} is not set. Generate one with: python -c "
                '"from cryptography.fernet import Fernet; '
                'print(Fernet.generate_key().decode())"'
            )
        _fernet_instance = MultiFernet([Fernet(key.encode()) for key in keys])
    return _fernet_instance


def ensure_encryption_key() -> None:
    """Fail at startup, not on the first credential read, when the key is missing or malformed."""
    _fernet()


def looks_encrypted(value: str) -> bool:
    return value.startswith(FERNET_TOKEN_PREFIX)


def encrypt_value(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


class EncryptedText(TypeDecorator):
    """
    Text column encrypted at rest with Fernet, key from CREDENTIALS_ENCRYPTION_KEY.

    Values that are not Fernet tokens are legacy plaintext rows (revision
    0002 encrypts them) and pass through on read. A Fernet token that no
    configured key opens raises CredentialKeyError: returning it as-is
    would send ciphertext to HoYoLAB/SKPort/3x-ui as if it were a cookie.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect) -> str | None:
        if value is None:
            return None
        return encrypt_value(str(value))

    def process_result_value(self, value, dialect) -> str | None:
        if value is None:
            return None
        try:
            return _fernet().decrypt(value.encode()).decode()
        except InvalidToken:
            if looks_encrypted(value):
                raise CredentialKeyError(
                    f"stored credential can't be decrypted with {KEY_ENV}; "
                    "was the key changed without keeping the old one?"
                ) from None
            return value
