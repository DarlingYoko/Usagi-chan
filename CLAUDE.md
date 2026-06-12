# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Stack

Python 3.12, [py-cord 2.7](https://docs.pycord.dev) Discord bot, async SQLAlchemy 2 over Postgres with the `pgvector` extension (image `pgvector/pgvector:pg17`). Internationalisation via `pycord18n` (`_()` helper, `en`/`ru` JSON dictionaries in `usagiBot/files/language/`). The container also installs `ffmpeg` for the Music cog and `yt-dlp` for downloads.

## Run / build

```bash
docker compose build
docker compose up                 # launches bot + postgres, env from stack.env
docker compose exec postgres psql -U <user> -W <db>
```

After the first DB start, enable pgvector once: `CREATE EXTENSION IF NOT EXISTS vector;`. Tables are then auto-created by `create_tables()` in `usagiBot.usagi.UsagiBot.before_identify_hook` — there is no migration tool, schema changes happen by editing `schemas.py` files and letting `Base.metadata.create_all` add new tables on next boot (existing columns are not migrated).

Local (non-docker) runs need a Postgres reachable at `POSTGRES_HOST` and the env vars from `example-usagi-variables.env` exported, then `python main.py`.

## Tests

```bash
pytest                                                          # full suite (what CI runs)
pytest usagiBot/tests/test_checks.py                            # single file
pytest usagiBot/tests/test_checks.py::TestCheckMethods::test_check_is_already_set_up
pytest -k wordle                                                # by name
coverage run -m pytest && coverage report                       # coverage already configured
```

`pytest.ini` silences SQLAlchemy `SAWarning` (duplicate `GenericFunction` / declarative base re-registration) and NumPy reload warnings — these show up because tests re-import modules between cases via the `clear_imports` autouse fixture in `test_checks.py`. Don't "fix" them by changing the import patterns.

`usagiBot/tests/utils.py` is imported by every test module and **sets `BOT_OWNER`/`BOT_ID` env vars at import time** so `usagiBot.env` doesn't crash on the `int(os.environ.get(...))` calls. Most tests `mock.patch` the SQLAlchemy model classes (e.g. `usagiBot.cogs.Main.schemas.UsagiConfig`) with `AsyncMock` and patch `sqlalchemy.ext.asyncio.create_async_engine` so no real DB is touched.

CI: `.github/workflows/pytest.yml` runs `pytest` on push to `universal` (the default branch) under the `Portainer` GitHub environment.

## Architecture

### Cog auto-loading

`UsagiBot.__init__` walks `COGS_DIR` (set in env, normally `usagiBot/cogs`) and loads every subdirectory that contains an `index.py` via `bot.load_extension`. To add a feature, create `usagiBot/cogs/<Name>/index.py` exposing a `setup(bot)` that calls `bot.add_cog(...)`. The directory name becomes the cog's qualified name and is what users pass to `/help <module>` and what moderators enable via `/setup module`.

### Per-cog file layout convention

```
usagiBot/cogs/<Name>/
    index.py         # Cog class + setup(bot); slash commands live here
    schemas.py       # SQLAlchemy models for this cog (optional)
    <name>_utils.py  # heavy logic, API clients, helpers (optional)
```

Schemas inherit `(Base, ModelAdmin)` from `usagiBot.db`. **All DB access goes through `ModelAdmin` classmethods** (`create`, `get`, `get_all_by`, `get_all_by_or`, `update`, `update_all`, `delete`, `delete_all`, `get_last_obj`, `get_last_n`, `get_embedding`) — there is no shared session passed around; each call opens its own `async_session()` transaction. `get_embedding` orders by pgvector L2 distance and is used by the AI cog for memory recall (`Vector(1536)` columns).

### Per-guild gating

Two layered access checks built on top of py-cord's standard checks (see `usagiBot/src/UsagiChecks.py`):

1. **Module on/off per guild** — `check_cog_whitelist` reads `bot.guild_cogs_settings` (populated from the `usagi_cogs` table by `init_cogs_settings`). Cogs that should be user-toggleable implement `cog_check` as: `if check_cog_whitelist(self, ctx): return True; raise UsagiModuleDisabledError()`. **Exceptions:** `Main`, `Moderation`, and `Events` are always-on (hard-coded in `Moderation.get_bot_cogs`'s `no_access_cogs`).
2. **Per-command channel binding** — slash commands declare a `command_tag="..."` kwarg; `check_is_already_set_up` and `check_correct_channel_command` look up `UsagiConfig(guild_id, command_tag)` and verify the channel matches. Moderators bind a tag to a channel via `/setup command add`. `load_all_command_tags` discovers tags by walking `command.__original_kwargs__["command_tag"]` for autocompletion.

Moderator gate: `check_member_is_moder` matches the member's roles against `bot.moder_roles[guild_id]` (loaded from `usagi_moder_roles`), or grants access on `guild_permissions.administrator`. `is_owner()` checks against `BOT_OWNER` env var. Custom errors live in `usagiBot/src/UsagiErrors.py`; `error_notification_to_owner` in `UsagiUtils.py` DMs the owner with command/user/channel/error context.

### Bot-level state caches

Several dicts live on the `bot` instance and are populated once in `before_identify_hook` (or by individual cogs on startup) — treat them as authoritative caches that the DB mirrors:

- `bot.guild_cogs_settings` — `{guild_id: {cog_name: bool}}`
- `bot.moder_roles` — `{guild_id: [role_id, ...]}`
- `bot.auto_roles` — `{guild_id: {message_id: {"name", "channel_id"}}}`
- `bot.language` — `{user_id: "en"|"ru"}`
- `bot.command_tags` — `[OptionChoice]` for autocompletion
- `bot.wordle_games`, `bot.ai_questions`, `bot.messages_dump` — per-cog ephemeral state

When mutating any of these via a slash command, **also persist to the matching DB table** so the cache survives restarts (look at `Main.create_auto_role_message` for the pattern: write row, then update `ctx.bot.auto_roles`).

### Background loops

Cogs commonly start `discord.ext.tasks.loop` schedulers in `__init__` — e.g. `Main.update_timer` (10 min), `AI.check_reminders` (1 min), `Events.dump_data` (30 min), `VPN.check_vpn_expiry` (1 h), three Hoyolab loops. They use `bot.get_channel(...) or await bot.fetch_channel(...)` to handle uncached channels.

### Cog status notes

- **AI cog is disabled**: `cogs/AI/index.py`'s `setup()` is a no-op (`bot.add_cog` commented out, issue #28). The pgvector memory/embedding code is only reachable from there. Its `openai_async` dependency is an archived project — if re-enabling, migrate to the official `openai` async client first.
- **VPN cog** (`cogs/VPN/`) manages 3x-ui panel subscriptions via `py3xui` (`Vpn3xui` wrapper in `vpn_utils.py`). Admin commands (`/vpn renew`, `create_user`, `fill_inbound`) are owner-gated via `checks=[is_owner().predicate]`; user commands are `/vpn info|top|request`. Renewal flow: hourly expiry check DMs the user a modal → request rows in `usagi_vpn_renewal_requests` → owner approves with `/vpn renew`.
- `Music` cog is a 2300-line monolith pending split; see `REFACTOR_PLAN.md` before making changes there.

### i18n

User-facing strings go through `_("text")` from `pycord18n.extension`; translations are added to both `usagiBot/files/language/en.json` and `ru.json`. Slash command names/descriptions get Russian variants via `name_localizations={"ru": "..."}` / `description_localizations={"ru": "..."}` decorator kwargs — match this style for new commands. The locale resolver is `lambda ctx: ctx.bot.language.get(ctx.author.id, "en")`.

### Custom embed equality

`UsagiEmbed` (`usagiBot/src/UsagiUtils.py`) overrides `__eq__` so tests can assert embed equality by title/description/fields. Use `get_embed(...)` (same file) to build embeds with consistent styling/timestamp.

## Conventions worth knowing

- Default reply colour is `0xF08080`; success uses `discord.Color.green()`, error uses `discord.Color.red()`, almost always `ephemeral=True` for moderation/setup responses.
- Long-running responses use `await ctx.defer(...)` then `ctx.send_followup(...)` instead of `ctx.respond(...)`.
- DB models keyed by `BigInteger` for Discord IDs (snowflakes don't fit in 32-bit) and `Text` for stringified message IDs where needed (see `UsagiAutoRoles.message_id`).
- Primary git branch is `universal`, not `main`/`master`.

## Secrets

`stack.env` holds runtime secrets (Discord token, OpenAI key, Postgres password, Twitch/Hoyolab/VPN creds) and is git-ignored — never commit it or echo its contents into chat/logs. `example-usagi-variables.env` is the template for new keys. Note: there is currently no `.dockerignore`, so `stack.env` lands in the Docker build context — fix tracked in `REFACTOR_PLAN.md` 0.2; don't add new `ADD/COPY` steps that widen this.

## Known issues / refactor

`REFACTOR_PLAN.md` (repo root) is the prioritized security/performance refactor plan from the 2026-06 audit. Check it before touching `Music`, `Events.dump_data`, `ModelAdmin`, or anything using `requests`. Rules of thumb derived from the audit:

- Never call `requests.*`, sync `yt-dlp`, PIL rendering, or `subprocess.check_output` directly in async code — use `aiohttp`, `run_in_executor`/`asyncio.to_thread`, or `asyncio.create_subprocess_exec`. Always set HTTP timeouts.
- Never build shell strings from user input; pass argv lists without `shell=True`.
- User-supplied URLs must be validated (scheme, no private hosts, timeout) before the bot fetches them.
- In background loops, fetch related rows in one query up front instead of per-row `get` calls (see plan §3.1).
