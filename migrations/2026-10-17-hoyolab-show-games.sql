-- Per-account game filter for /hoyolab resin.
-- create_all does not add columns to existing tables, so apply by hand:
--
--   docker compose exec -T postgres psql -U <user> -d <db> -f - < migrations/2026-10-17-hoyolab-show-games.sql
--
-- Existing accounts keep showing every game (default true).

ALTER TABLE usagi_hoyolab
    ADD COLUMN IF NOT EXISTS show_genshin  boolean NOT NULL DEFAULT true,
    ADD COLUMN IF NOT EXISTS show_starrail boolean NOT NULL DEFAULT true,
    ADD COLUMN IF NOT EXISTS show_zzz      boolean NOT NULL DEFAULT true;
