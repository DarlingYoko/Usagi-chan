# Usagi-chan Deep Audit — 2026-06-12

Follow-up to `REFACTOR_PLAN.md` (2026-06 security/performance audit, fully
implemented). This pass covers translations, DB usage, every cog, API usage,
error handling, tests, and operations.

## Score

| Area | Score | Why |
|---|---|---|
| Security | **8/10** | Post-refactor: encrypted credentials, SSRF guard, non-root container, no shell injection. Open: `!ip` leaks host public IP to any user and blocks the event loop (sync `requests`, no timeout); `/unic_role create` has no per-user cap (guild role-limit abuse). |
| Reliability | **4/10** | The Hoyolab loop-death bug class exists in **7 more loops** (Main, Events, Twitch, Birthdays ×2, Arknights ×2): one unhandled exception permanently kills the loop until restart. 4 missing `await`s in Arknights leave users on eternal "thinking…". `on_ready` re-runs full init + `sync_commands` on every reconnect; `before_identify_hook` runs `create_tables()` on every reconnect. Two `except A or B` bugs silently narrow exception handling. |
| i18n | **6/10** | en/ru parity perfect (212/212), placeholders match. But **5 live `InvalidTranslationKeyError` crash sites** (key used in code, absent from dicts) and 14 dead keys, two of which are typo-drifted twins of the missing ones. |
| DB | **6/10** | ModelAdmin solid (pooling, pre-ping, upsert, batching). Missing: secondary indexes (every query is a seq scan), NOT NULL/defaults (nullable booleans = three-state bugs), real migrations (create_all only adds tables), stale-row cleanup. A few N+1 loops remain. |
| Cogs / architecture | **6/10** | Consistent layout and gating. Dead weight: ~120 lines commented torrent code + `qbittorrentapi` dependency, disabled AI cog pinning archived `openai-async`. Cache/DB divergence in auto-roles remove. Several logic bugs (below). |
| API usage | **6/10** | genshin/Endfield clients clean (per-request sessions, timeouts). `fetch_emoji`/`fetch_channel` N+1s where cache would do; Twitch polls per-streamer instead of one batched `get_streams` (API takes 100 logins/call). |
| Tests / CI | **7/10** | 130 green, CI on push+PR. But coverage report hides never-imported files: **Main (915 lines), Birthdays, ArknightsEndfield, AI have zero tests**; Music 16–26%, Events 29%. Real coverage is below the reported 63%. |
| Observability | **4/10** | One root logger named `mylogger`, INFO to stdout. Owner error-DM has no traceback and can exceed the 2000-char limit; `ApplicationCommandInvokeError` branch logs `str(error)` only and never notifies the owner. |

**Overall: 6/10.** Security is now strong; reliability is the weakest axis —
the same "stuck after a few days" class fixed in Hoyolab lives in every other
background loop.

---

## Phase 1 — Crashes & correctness (do first)

**Done 2026-06-13** (commits `6308997`..`da5cf19`, + `4ce5e6e` test isolation).
All items below fixed with regression tests; suite green at 159. The only
carry-over is the dead-key deletion in 1.1 (cleanup, non-crashing) — moved to
Phase 4.

- [x] **1.1 i18n missing keys** — add to both `en.json`+`ru.json` or repoint code
  to the existing twin:
  - `Main/index.py:754` `"This emoji already used"` (dict has dead twin `"This emoji already use"`)
  - `Events/index.py:149` `"Don't have permissions to do that"` (dict has dead `"I don't have permissions to do that"`)
  - `Events/index.py:162` `"Some requirements were not met."` (period variant; no-period key exists)
  - `Birthdays/index.py:193` `"This user isn't in birthday list, add him firstly"` (dict has shorter dead twin)
  - `VPN/index.py:426` `"VPN no profiles"` — new `/vpn request` path, crashes today
  - _(carried to Phase 4)_ Delete 14 dead keys (incl. the now-renamed emoji twin, 6 old Hoyolab sub texts, `Geetest error`, `Stamina`, `Slash command group`, redeem-token pair). Keys passed via variables (`_(answer)` in Birthdays, `get_text(f"VPN notify {x}")`) are **used** — keep.
- [x] **1.2 Arknights missing awaits** — `index.py:305,381,469,511` `ctx.respond(...)` not awaited; after `defer` the user hangs forever.
- [x] **1.3 `except A or B`** — `Main/index.py:212` (`ValueError or KeyError`), `Main/index.py:400` (`Forbidden or NotFound`): only the first exception is caught. Use tuples.
- [x] **1.4 Save-roles flag never checked** — `Events/index.py:215,243`: `saving is False` is never true (row object); `saving.saving_roles` is ignored, so the feature can't be turned off. Also filter `None` from `guild.get_role(...)` before `add_roles` (deleted roles crash the restore).
- [x] **1.5 Birthdays** — `index.py:227` `update(channel=...)` → column is `channel_id` (re-pointing a timer crashes); `index.py:106` `return` → `continue` (one guild without upcoming birthday skips all remaining timers); validate `datetime(day, month)` (31.02 → unhandled ValueError); drop the `asyncio.sleep(600)` inside the loop body (serial 10-min sleeps per timer inside an hourly task).
- [x] **1.6 Tech** — `purge(limit + 1)` deletes one innocent extra message (slash commands have no invoking message); `/unic_role delete` only unassigns — `role.delete()` the guild role too, else orphan roles accumulate; cap unic roles to 1/user on create.
- [x] **1.7 Main auto-roles** — `edit role/emoji/description`: `new_entity` stays `None` when the picked role isn't in payload (stale autocomplete) → AttributeError; `remove_auto_role_message` never pops `bot.auto_roles` cache (deleted message still autocompletes until restart); `update_timer` shows garbage for expired timers (negative timedelta `.seconds`) — delete or zero them.
- [x] **1.8 Arknights claim loop** — after failed `sign_in()` it still calls `get_attendance()` (`index.py:249-257`); `continue` after recording the error.
- [x] **1.9 Small ones** — Twitch `if streamers is None` ×2 → `if not streamers` (empty list renders header-only message); Wordle top numbering starts at 0 (`enumerate(..., start=1)`).

## Phase 2 — Reliability (the "stuck after a few days" class)

py-cord `tasks.loop` dies permanently on any exception outside
`(OSError, ClientError, TimeoutError, gateway errors)`. Hoyolab got the fix
(`b26e6b1`); the same pattern is needed in:

**Done 2026-06-13** (commits `67d1f21`..`684c11f`). All items below fixed
with regression tests; suite green at 179. 2.6 shipped as `guard_loop`
(whole-body safety net) + `guarded_item` (per-iteration isolation) in
`UsagiUtils`; the new fixes use them, Hoyolab keeps its existing inline
guards. VPN's hourly loop was out of the audit's Phase 2 list — left as-is.

- [x] **2.1** `Main.update_timer` (deleted channel = NotFound = dead loop)
- [x] **2.2** `Events.dump_data` — also: counters are swapped out **before** the
  upsert; a DB error loses 30 min of stats *and* kills the loop. Re-merge the
  dump back into `bot.messages_dump` on failure.
- [x] **2.3** `Twitch.twitch_notify_loop` — `TwitchAPIException` kills it; also
  `self.twitch` auth failure path.
- [x] **2.4** `Birthdays.check_birthday` + `update_birthday_timer` — `guild_config.generic_id` with `config=None` is an AttributeError today; `texts.json` KeyError too.
- [x] **2.5** `Arknights.check_sanity_overflow` + `claim_endfield_daily_reward`
- [x] **2.6** Consider a shared helper in `UsagiUtils` (guarded-iteration pattern: per-item try/except + whole-body guard, log via `bot.logger.exception`) so the 10 loops don't each reinvent it. TDD like `test_genshin.py` survival tests.
- [x] **2.7 Reconnect hygiene** — `before_identify_hook` ignores its `initial` flag: run `create_tables()`/`init_language()` only when `initial=True`. Move one-time init out of `on_ready` (fires on every reconnect) or guard with a `self._ready_once` flag — especially `sync_commands()` (rate-limit-heavy global call).
- [x] **2.8 Error visibility** — `Events.on_application_command_error`: the
  `ApplicationCommandInvokeError` branch logs `str(error)` (no traceback, no
  `error.original`) and never DMs the owner. Use `traceback.format_exception`,
  truncate to ~1900 chars, and call `error_notification_to_owner` there too.

## Phase 3 — Performance

**Done 2026-06-14** (commits `0f6134c`..`f99fb5b`). 3.1 reuses the
`check_resin_overflow` batch pattern (load all configs once, dict by
guild/tag); Hoyolab already had it. 3.2 adds `Twitch._fetch_live_streams`
(one batched get_streams per 100 logins). 3.5 adds
`ModelAdmin.get_top(order_by, limit, **filters)`. 3.4/3.6 are hand-apply
SQL in `migrations/2026-06-14-*.sql` (create_all never alters existing
tables) — **run both before deploy**. Suite green at 185.

- [x] **3.1 Batch config lookups** (pattern from `check_resin_overflow`): Twitch loop, Birthdays `check_birthday`, both Arknights loops, `/help` (one `get_all_by(guild_id=...)` instead of per-command `get`).
- [x] **3.2 Twitch single API call** — `get_streams(user_login=[...])` accepts 100 logins; currently one call per streamer per 5 min.
- [x] **3.3 Cache-first Discord lookups** — `guild.get_emoji` before `fetch_emoji` in Main auto-roles (5 sites, one API call per row per edit today); `get_channel`-first in Events listeners, Fun `add_based_message`, Birthdays loop, and both autocompletes (`get_timers`, `get_birthdays` — `fetch_member` per row inside a 3-second autocomplete budget).
- [x] **3.4 Indexes** — migration SQL: composite `(guild_id, user_id)` on `usagi_hoyolab`, `usagi_birthday`, `usagi_twitch_notify`, `usagi_wordle_results`, `usagi_member_roles`, `usagi_gryphline`; `(guild_id, command_tag)` on `usagi_config`; `(message_id)` on `usagi_auto_roles_data`.
- [x] **3.5 Sort in SQL** — Wordle top loads the whole table and sorts in Python; add `get_top(limit, **filters)` (ORDER BY points DESC LIMIT n) to ModelAdmin.
- [x] **3.6 Schema hardening** — NOT NULL + server defaults for counters and booleans (nullable booleans are three-state bugs waiting); needs a backfill migration.

## Phase 4 — Security & operations

- [ ] **4.1 `!ip`** (`Fun/index.py:125`) — sync `requests.get`, no timeout, on the event loop, and prints the host's public IP to any chat member. Owner-gate it + aiohttp, or delete it.
- [ ] **4.2 Logging** — named loggers per module (`logging.getLogger(__name__)` is already the convention in new files), rename `mylogger`, add level via env var.
- [ ] **4.3 Alembic** — replace `create_all` migrations-by-restart; with 2.7 the per-reconnect `create_tables()` goes away anyway. The two hand-written SQL files in `migrations/` become alembic revisions.
- [ ] **4.4 Dead code & deps** — torrent block (`Fun/index.py:151-221`), `init_qbt_client` + `qbittorrentapi` import (`UsagiUtils.py`) + dependency + 3 `Qbittorrent*` env vars; commented `redeem_code`/`redeem_code_all` in Hoyolab; verify-then-drop unused env vars (`DISCORD_TEST*`, `HOYOLAB_CLIENT_ID/SECRET`).
- [ ] **4.5 AI cog decision** — disabled since #28 but still imported at cog scan, pinning archived `openai-async`. Either delete the cog (git keeps history) or migrate to the official `openai` client when re-enabling; then drop the dep.

## Phase 5 — Tests & CI

- [ ] **5.1** Coverage visibility: run `coverage run --source=usagiBot -m pytest` so never-imported files (Main, Birthdays, Arknights, AI) stop hiding; current "63%" overstates.
- [ ] **5.2** New tests, priority order: Main auto-roles flows + timer loop (915 untested lines, moderator-facing), Birthdays (both loops + 1.5 regressions), Arknights (mock `EndfieldClient`; 1.2/1.8 regressions), Events listeners (1.4 regression).
- [ ] **5.3** Add `--cov-fail-under` gate once 5.1 baseline is known.

## Suggested order

1. Phase 1 (one PR, mostly one-liners, every item user-visible)
2. Phase 2 (one PR; reuse the genshin survival-test pattern)
3. Phase 5.1 + 5.2 alongside Phase 1/2 regressions (TDD)
4. Phase 3, then 4 — independent, any order
