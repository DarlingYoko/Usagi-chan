"""encrypt credentials stored before EncryptedText existed

EncryptedText (2026-06) only encrypted a value when it was written again,
and the Hoyolab/Endfield/VPN credential columns are almost never rewritten,
so rows from before that change stayed plaintext. This rewrites every
non-Fernet value with the configured key. Data-only: no schema change.

Revision ID: 0002_encrypt_legacy_credentials
Revises: 0001_baseline
Create Date: 2026-11-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from usagiBot.db.types import encrypt_value, looks_encrypted

revision: str = '0002_encrypt_legacy_credentials'
down_revision: Union[str, Sequence[str], None] = '0001_baseline'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Snapshot of the EncryptedText columns at this revision (not read from the
# models, which may change later).
ENCRYPTED_COLUMNS = (
    ("usagi_gryphline", "token"),
    ("usagi_hoyolab", "ltoken_v2"),
    ("usagi_hoyolab", "cookie_token_v2"),
    ("usagi_vpn_users", "uid"),
    ("usagi_vpn_history_logs", "uid"),
    ("usagi_vpn_renewal_requests", "uid"),
)


def upgrade() -> None:
    bind = op.get_bind()
    for table, column in ENCRYPTED_COLUMNS:
        rows = bind.execute(
            sa.text(f"SELECT id, {column} FROM {table} WHERE {column} IS NOT NULL")
        ).fetchall()
        for row_id, value in rows:
            if looks_encrypted(value):
                continue
            bind.execute(
                sa.text(f"UPDATE {table} SET {column} = :value WHERE id = :id"),
                {"value": encrypt_value(value), "id": row_id},
            )


def downgrade() -> None:
    # Decrypting credentials back to plaintext is never wanted; EncryptedText
    # reads the encrypted rows on any revision.
    pass
