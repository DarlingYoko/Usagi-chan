-- One-off migration for REFACTOR_PLAN.md 3.2 (dump_data upsert).
-- Base.metadata.create_all only creates new tables, so the unique
-- constraint must be added to the existing usagi_backup by hand:
--
--   docker compose exec postgres psql -U <user> -d <db> -f - < migrations/2026-06-12-usagi-backup-unique.sql

BEGIN;

-- Collapse any duplicate (guild, channel, user) rows left by the old
-- delete-then-insert flow into a single summed row.
CREATE TEMP TABLE usagi_backup_merged AS
SELECT
    min(id)       AS id,
    guild_id,
    channel_id,
    user_id,
    sum(messages) AS messages,
    sum(images)   AS images,
    sum(gifs)     AS gifs,
    sum(emojis)   AS emojis,
    sum(stickers) AS stickers,
    max(voice_min) AS voice_min
FROM usagi_backup
GROUP BY guild_id, channel_id, user_id;

TRUNCATE usagi_backup;
INSERT INTO usagi_backup SELECT * FROM usagi_backup_merged;

ALTER TABLE usagi_backup
    ADD CONSTRAINT uq_usagi_backup_guild_channel_user
    UNIQUE (guild_id, channel_id, user_id);

-- Old code assigned ids manually, so the sequence was never advanced.
SELECT setval(
    pg_get_serial_sequence('usagi_backup', 'id'),
    COALESCE((SELECT max(id) FROM usagi_backup), 1)
);

COMMIT;
