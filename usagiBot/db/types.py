import os

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator

KEY_ENV = "CREDENTIALS_ENCRYPTION_KEY"

_fernet_instance: Fernet | None = None


def _fernet() -> Fernet:
    global _fernet_instance
    if _fernet_instance is None:
        key = os.environ.get(KEY_ENV)
        if not key:
            raise RuntimeError(
                f"{KEY_ENV} is not set. Generate one with: python -c "
                '"from cryptography.fernet import Fernet; '
                'print(Fernet.generate_key().decode())"'
            )
        _fernet_instance = Fernet(key.encode())
    return _fernet_instance


class EncryptedText(TypeDecorator):
    """
    Text column encrypted at rest with Fernet, key from CREDENTIALS_ENCRYPTION_KEY.

    Lazy migration: stored values that are not valid Fernet tokens (legacy
    plaintext rows) pass through on read and get encrypted on their next
    write. Key rotation invalidates stored credentials = users re-login.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect) -> str | None:
        if value is None:
            return None
        return _fernet().encrypt(str(value).encode()).decode()

    def process_result_value(self, value, dialect) -> str | None:
        if value is None:
            return None
        try:
            return _fernet().decrypt(value.encode()).decode()
        except InvalidToken:
            return value
