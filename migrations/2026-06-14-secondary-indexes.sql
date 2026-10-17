-- One-off migration for IMPROVEMENT_PLAN.md 3.4 (secondary indexes).
-- Base.metadata.create_all never adds indexes to existing tables, so the
-- hot-path lookups below run as sequential scans until this is applied:
--
--   docker compose exec postgres psql -U <user> -d <db> -f - < migrations/2026-06-14-secondary-indexes.sql
--
-- IF NOT EXISTS makes this safe to re-run.

BEGIN;

-- Per-(guild, user) lookups: command callbacks and the background loops
-- that read one user's rows.
CREATE INDEX IF NOT EXISTS ix_usagi_hoyolab_guild_user
    ON usagi_hoyolab (guild_id, user_id);
CREATE INDEX IF NOT EXISTS ix_usagi_birthday_guild_user
    ON usagi_birthday (guild_id, user_id);
CREATE INDEX IF NOT EXISTS ix_usagi_twitch_notify_guild_user
    ON usagi_twitch_notify (guild_id, user_id);
CREATE INDEX IF NOT EXISTS ix_usagi_wordle_results_guild_user
    ON usagi_wordle_results (guild_id, user_id);
CREATE INDEX IF NOT EXISTS ix_usagi_member_roles_guild_user
    ON usagi_member_roles (guild_id, user_id);
CREATE INDEX IF NOT EXISTS ix_usagi_gryphline_guild_user
    ON usagi_gryphline (guild_id, user_id);

-- /help and setup resolve a command's bound channel by (guild, tag).
CREATE INDEX IF NOT EXISTS ix_usagi_config_guild_tag
    ON usagi_config (guild_id, command_tag);

-- Auto-role reaction handlers look up rows by message id on every reaction.
CREATE INDEX IF NOT EXISTS ix_usagi_auto_roles_data_message
    ON usagi_auto_roles_data (message_id);

-- Wordle leaderboard: ModelAdmin.get_top runs
--   WHERE guild_id = ? ORDER BY points DESC LIMIT n
-- which this index serves without a sort.
CREATE INDEX IF NOT EXISTS ix_usagi_wordle_results_guild_points
    ON usagi_wordle_results (guild_id, points DESC);

COMMIT;
