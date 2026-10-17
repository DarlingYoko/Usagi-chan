-- One-off migration for IMPROVEMENT_PLAN.md 3.6 (NOT NULL + defaults).
-- create_all does not alter existing columns, so the new
-- nullable=False/server_default on the models only applies to fresh DBs.
-- Backfill existing NULLs, set the defaults, then enforce NOT NULL:
--
--   docker compose exec postgres psql -U <user> -d <db> -f - < migrations/2026-06-14-not-null-defaults.sql
--
-- Nullable booleans were three-state (NULL/true/false); `not None` read as
-- "subscribed", so a missing flag behaved like an enabled one. Counters
-- defaulting to NULL break SUM/arithmetic. Both collapse to a real default.

BEGIN;

-- usagi_hoyolab subscription/notified flags -> false
UPDATE usagi_hoyolab SET
    genshin_resin_sub          = COALESCE(genshin_resin_sub, false),
    genshin_resin_sub_notified = COALESCE(genshin_resin_sub_notified, false),
    genshin_daily_sub          = COALESCE(genshin_daily_sub, false),
    daily_notify_sub           = COALESCE(daily_notify_sub, false),
    starrail_daily_sub         = COALESCE(starrail_daily_sub, false),
    starrail_resin_sub         = COALESCE(starrail_resin_sub, false),
    starrail_resin_sub_notified = COALESCE(starrail_resin_sub_notified, false),
    zzz_daily_sub              = COALESCE(zzz_daily_sub, false),
    zzz_resin_sub              = COALESCE(zzz_resin_sub, false),
    zzz_resin_sub_notified     = COALESCE(zzz_resin_sub_notified, false);

ALTER TABLE usagi_hoyolab
    ALTER COLUMN genshin_resin_sub          SET DEFAULT false,
    ALTER COLUMN genshin_resin_sub          SET NOT NULL,
    ALTER COLUMN genshin_resin_sub_notified SET DEFAULT false,
    ALTER COLUMN genshin_resin_sub_notified SET NOT NULL,
    ALTER COLUMN genshin_daily_sub          SET DEFAULT false,
    ALTER COLUMN genshin_daily_sub          SET NOT NULL,
    ALTER COLUMN daily_notify_sub           SET DEFAULT false,
    ALTER COLUMN daily_notify_sub           SET NOT NULL,
    ALTER COLUMN starrail_daily_sub         SET DEFAULT false,
    ALTER COLUMN starrail_daily_sub         SET NOT NULL,
    ALTER COLUMN starrail_resin_sub         SET DEFAULT false,
    ALTER COLUMN starrail_resin_sub         SET NOT NULL,
    ALTER COLUMN starrail_resin_sub_notified SET DEFAULT false,
    ALTER COLUMN starrail_resin_sub_notified SET NOT NULL,
    ALTER COLUMN zzz_daily_sub              SET DEFAULT false,
    ALTER COLUMN zzz_daily_sub              SET NOT NULL,
    ALTER COLUMN zzz_resin_sub              SET DEFAULT false,
    ALTER COLUMN zzz_resin_sub              SET NOT NULL,
    ALTER COLUMN zzz_resin_sub_notified     SET DEFAULT false,
    ALTER COLUMN zzz_resin_sub_notified     SET NOT NULL;

-- usagi_gryphline flags -> false
UPDATE usagi_gryphline SET
    endfield_sanity_sub          = COALESCE(endfield_sanity_sub, false),
    endfield_sanity_sub_notified = COALESCE(endfield_sanity_sub_notified, false),
    endfield_daily_sub           = COALESCE(endfield_daily_sub, false);

ALTER TABLE usagi_gryphline
    ALTER COLUMN endfield_sanity_sub          SET DEFAULT false,
    ALTER COLUMN endfield_sanity_sub          SET NOT NULL,
    ALTER COLUMN endfield_sanity_sub_notified SET DEFAULT false,
    ALTER COLUMN endfield_sanity_sub_notified SET NOT NULL,
    ALTER COLUMN endfield_daily_sub           SET DEFAULT false,
    ALTER COLUMN endfield_daily_sub           SET NOT NULL;

-- usagi_save_roles.saving_roles -> false
UPDATE usagi_save_roles SET saving_roles = COALESCE(saving_roles, false);
ALTER TABLE usagi_save_roles
    ALTER COLUMN saving_roles SET DEFAULT false,
    ALTER COLUMN saving_roles SET NOT NULL;

-- usagi_birthday_timer.enable -> false
UPDATE usagi_birthday_timer SET enable = COALESCE(enable, false);
ALTER TABLE usagi_birthday_timer
    ALTER COLUMN enable SET DEFAULT false,
    ALTER COLUMN enable SET NOT NULL;

-- usagi_backup counters -> 0
UPDATE usagi_backup SET
    messages  = COALESCE(messages, 0),
    images    = COALESCE(images, 0),
    gifs      = COALESCE(gifs, 0),
    emojis    = COALESCE(emojis, 0),
    stickers  = COALESCE(stickers, 0),
    voice_min = COALESCE(voice_min, 0);

ALTER TABLE usagi_backup
    ALTER COLUMN messages  SET DEFAULT 0,
    ALTER COLUMN messages  SET NOT NULL,
    ALTER COLUMN images    SET DEFAULT 0,
    ALTER COLUMN images    SET NOT NULL,
    ALTER COLUMN gifs      SET DEFAULT 0,
    ALTER COLUMN gifs      SET NOT NULL,
    ALTER COLUMN emojis    SET DEFAULT 0,
    ALTER COLUMN emojis    SET NOT NULL,
    ALTER COLUMN stickers  SET DEFAULT 0,
    ALTER COLUMN stickers  SET NOT NULL,
    ALTER COLUMN voice_min SET DEFAULT 0,
    ALTER COLUMN voice_min SET NOT NULL;

-- usagi_wordle_results counters -> 0
UPDATE usagi_wordle_results SET
    points         = COALESCE(points, 0),
    count_of_games = COALESCE(count_of_games, 0);

ALTER TABLE usagi_wordle_results
    ALTER COLUMN points         SET DEFAULT 0,
    ALTER COLUMN points         SET NOT NULL,
    ALTER COLUMN count_of_games SET DEFAULT 0,
    ALTER COLUMN count_of_games SET NOT NULL;

COMMIT;
