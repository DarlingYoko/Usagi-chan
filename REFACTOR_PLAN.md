# Refactor Plan — Security & Performance

Audit date: 2026-06-12. Findings ordered by severity; each item lists location, problem, and fix. Phases are ordered so that each can ship independently.

---

## Phase 0 — Critical security (do first, small diffs)

### 0.1 Shell command injection in Music cog
- `usagiBot/cogs/Music/index.py:449` and `usagiBot/cogs/Music/index.py:2031`
- `subprocess.check_output(f'ffprobe ... "{link}"', shell=True)` where `link` comes straight from the `/music play` slash-command option. A link like `http://x/a"; <command> #` executes arbitrary shell commands in the container.
- Fix: build argv list, no shell, and move off the event loop:
  ```python
  proc = await asyncio.create_subprocess_exec(
      "ffprobe", "-v", "error", "-show_entries", "format=duration",
      "-of", "default=noprint_wrappers=1:nokey=1", link,
      stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
  )
  ```
- Regression test: assert the command list form is used / mock `create_subprocess_exec` and feed a link containing `"; echo pwned`.

### 0.2 Secrets baked into Docker image
- `Dockerfile` (`ADD . /Usagi/`), no `.dockerignore`, and `stack.env` exists in the build context. Every image build copies the Discord token, OpenAI key, Postgres and VPN credentials into an image layer; anyone with image pull access has all secrets.
- Fix: add `.dockerignore` with at minimum `stack.env`, `*.env`, `.git`, `.idea`, `venv`, `__pycache__`, `.pytest_cache`, `.coverage`, `usagiBot/tests`. Secrets keep flowing in via `env_file` at runtime (already the case in docker-compose).
- If the image was ever pushed to a registry: rotate all secrets in `stack.env` (user decision).

### 0.3 Postgres published to the network
- `docker-compose.yaml` — `ports: "5432:5432"` exposes the DB on the host (and the LAN unless firewalled), protected only by the password. The bot reaches Postgres over the compose network and does not need the published port.
- Fix: delete the `ports:` block, or bind `127.0.0.1:5432:5432` if host access is needed for debugging.

### 0.4 SSRF via user-supplied URLs (Arknights Endfield)
- `usagiBot/cogs/ArknightsEndfield/index.py:519` (`/endfield set_bg` does `requests.get(url)` on raw user input) and `arknights_utils.py:642` (`draw_endfield_profile` re-fetches the stored `background_url` on every profile render).
- The bot will fetch any URL: internal services (3x-ui panel, qBittorrent, Postgres, cloud metadata endpoints) become reachable through it. Also blocking and timeout-less (see Phase 2).
- Fix: validate scheme is `http/https`, resolve host and reject private/link-local ranges, set `timeout=`, cap response size, and require an image `Content-Type` before accepting/storing the URL.

### 0.5 Hardcoded privileged user IDs
- `usagiBot/src/UsagiChecks.py:67` — `check_member_is_moder` grants moderator on **every guild** to hardcoded ID `290166276796448768`; `usagiBot/cogs/Music/index.py:32` — `authors = (290166276796448768,)`.
- Fix: replace both with `BOT_OWNER` from env (it's the same person today, but the bypass should be visible in config, not buried in a check).

---

## Phase 1 — Security hardening

### 1.1 Run container as non-root
- `Dockerfile` has no `USER`; combined with 0.1 the blast radius of any injection is root-in-container.
- Fix: create app user, `chown` workdir, add `USER usagi`. Also: copy `requirements.txt` first and install before `COPY .` for layer caching; `pip install --no-cache-dir`.

### 1.2 Credentials at rest in Postgres
- Hoyolab cookies (`ltoken_v2`, `cookie_token_v2` in `usagiBot/cogs/Hoyolab/schemas.py`), Arknights `token`, VPN sub UUIDs — all plaintext `Text` columns. These are session credentials for other people's game accounts.
- Fix (pragmatic): symmetric encryption (e.g. `cryptography.Fernet`) with key from env, applied in `set_cookies`-style accessors. Keep it inside `ModelAdmin`-adjacent helpers so cogs don't repeat it. Document key rotation = users re-login.

### 1.3 Exception-handling bugs in VPN cog (auth-adjacent logic)
- `usagiBot/cogs/VPN/index.py:451` — `except ValueError or KeyError` evaluates to `except ValueError`; `KeyError` propagates.
- `usagiBot/cogs/VPN/index.py:96` — `amount // subscriptions_count` raises uncaught `ZeroDivisionError` when user enters `0` in the modal.
- Fix: `except (ValueError, KeyError)`; validate `subscriptions_count > 0` before dividing. Both get regression tests in `usagiBot/tests/test_vpn.py`.

### 1.4 CI hygiene
- `.github/workflows/pytest.yml`: pin `actions/setup-python@v5`, add pip cache. Consider adding `ruff` (a `.ruff_cache` already exists locally) and a secret-scanning step (`gitleaks`) since `stack.env` lives next to the repo.

---

## Phase 2 — Performance: stop blocking the event loop

Single-threaded asyncio bot; every blocking call below freezes **all** commands, music playback, and background loops while it runs.

### 2.1 Synchronous HTTP (`requests`) inside async paths
| Location | Call | Fix |
|---|---|---|
| `cogs/Fun/fun_utils.py:17,22` | tradingview scrape, no timeout | `aiohttp` session with timeout |
| `cogs/Twitch/twitch_utils.py:70` | streamer icon fetch inside 5-min notify loop | `aiohttp`, reuse session |
| `cogs/ArknightsEndfield/arknights_utils.py:642,661` | background/avatar fetch per profile render | `aiohttp` (file already has a `ClientSession` for the API — reuse the pattern) |
| `cogs/ArknightsEndfield/index.py:519` | URL validation fetch | covered by 0.4 |

All `requests` call sites lack `timeout=` — a hung remote host blocks the loop indefinitely. After conversion, drop `requests`/`bs4` double-dependency review (see 4.3).

### 2.2 Synchronous yt-dlp and ffprobe
- `cogs/Music/index.py:2123` — `/music search` calls `ytdl_playlist.extract_info` directly (not via `run_in_executor` like `play` does); a YouTube search freezes the bot for seconds.
- ffprobe `subprocess.check_output` (same lines as 0.1) — becomes `asyncio.create_subprocess_exec` in the 0.1 fix.

### 2.3 Synchronous PIL image generation
- Twitch notify card (`gen_pic`), Wordle board rendering (`wordle_utils.py`), Endfield profile card (`draw_endfield_profile`, ~150 lines of drawing + font loading per call).
- Fix: wrap entry points in `asyncio.to_thread(...)`. Load fonts/template images once at module level instead of per call.

### 2.4 Polling loops in Music `VoiceState`
- `cogs/Music/index.py` — every guild's `VoiceState` spawns three `while True: await asyncio.sleep(1)` tasks (`update_volume`, `check_user_listening`, `update_voice_state`). 10 guilds = 30 wakeups/sec doing mostly nothing.
- Fix: replace `check_user_listening`/`update_voice_state` with an `on_voice_state_update` listener on the cog; set volume directly in the setter instead of polling.

### 2.5 Wordle dictionary reads
- `cogs/Wordle/wordle_utils.py:299,317` — reads `russian.txt` / `check_ru_dict.txt` from disk on every guess/game. Load once at module import into a `set`.
- Also fix off-by-one: `wordle_utils.py:305` `random.randint(0, len(words))` can raise `IndexError` — use `random.choice(words)`.

---

## Phase 3 — Performance: database access patterns

### 3.1 N+1 queries in background loops
- `cogs/Hoyolab/index.py:300` `check_resin_overflow`: one `UsagiConfig.get` per subscribed user every 30 min → fetch all configs for tag `genshin` once into a dict.
- `cogs/AI/index.py:44` `check_reminders`: loads **all** reminders every minute, filters in Python → add a `get_due(date)` query (`WHERE date <= now`).
- `cogs/VPN/index.py:193` `check_vpn_expiry`: per-row `update` calls → batch with one `update_all` on collected ids.

### 3.2 `Events.dump_data` rewrite
- `cogs/Events/index.py:34-88`: every 30 min reads the entire `usagi_backup` table, assigns ids manually from `get_last_obj()` (collision-prone, defeats the sequence), and does delete-then-insert to "update" counters.
- Fix: composite unique constraint on `(guild_id, channel_id, user_id)` + a single Postgres upsert (`INSERT ... ON CONFLICT ... DO UPDATE SET messages = usagi_backup.messages + EXCLUDED.messages, ...`). Drop manual id math entirely. This also removes the unbounded read.

### 3.3 `ModelAdmin` overhead
- `usagiBot/db/models.py`: SELECTs run inside `session.begin()` transactions (pointless overhead); bulk update/delete use `synchronize_session="fetch"` (issues an extra SELECT per statement — there are no live ORM objects to sync, use `False`); `generate_conditions` silently builds `col == None` for typo'd kwargs — raise on unknown attribute.
- Add `get_due`-style targeted helpers as needed by 3.1 rather than fetching-all-and-filtering.

### 3.4 Discord API round-trips in hot event handlers
- `cogs/Events/index.py:313-330, 360-362` — `on_raw_reaction_add/remove` use `fetch_guild`/`fetch_channel`/`fetch_member` (HTTP) on every reaction. Use `bot.get_guild`/`guild.get_member`/`get_channel` first, fall back to fetch only on cache miss (the pattern other loops already use).
- `UsagiUtils.error_notification_to_owner:128` — `fetch_user(BOT_OWNER)` per error → `bot.get_user(...) or await bot.fetch_user(...)`.

### 3.5 VPN 3x-ui API fan-out
- `cogs/VPN/vpn_utils.py` — `generate_vpn_user_info` calls `get_sub` per profile, each of which fetches the **full inbound list**; `get_top_traffic` then queries each client by email individually. O(profiles × inbounds) HTTP calls per `/vpn info`.
- Fix: fetch the inbound list once per operation, pass it down; the inbound payload already contains client stats in most 3x-ui versions — check before issuing per-email queries. Reuse one logged-in `Vpn3xui` per command instead of `login()` per helper.

### 3.6 Gateway intents
- `usagiBot/usagi.py:62` — `discord.Intents.all()` subscribes to presence/typing events the bot never uses (highest-volume gateway traffic). Declare only what's needed: `members`, `message_content`, `messages`, `reactions`, `voice_states`, `guilds`, `emojis`.

---

## Phase 4 — Structure & correctness cleanups

### 4.1 Split `cogs/Music/index.py` (2352 lines)
- Mixes audio sources, queue, voice-state machine, UI views, and commands. Split: `sources.py` (YTDLSource/FFMPEGSource/Song), `voice_state.py`, `views.py`, `index.py` (commands only). Replace the 24 numbered `print("ERROR N- ", e)` with `bot.logger`; delete commented-out dead code.

### 4.2 Test-only correctness bugs
- `UsagiUtils.UsagiEmbed.__eq__:27-31` — field comparison joins with `and`, so two fields differing in only one attribute compare equal; embed assertions in tests can pass falsely. Should be `or` (any attribute differs → not equal).
- `cogs/Events/index.py:402` — emoji counter regex `"<*:*:*>"` matches any colon; intended custom-emoji pattern is `r"<a?:\w+:\d+>"`.

### 4.3 Dependency prune (`requirements.txt`)
- `openai_async` is an archived/dead project and the AI cog is disabled (`cogs/AI/index.py:449` `setup()` is a no-op) — when re-enabling, migrate to the official `openai` async client.
- Both `psycopg2-binary` and `asyncpg` installed (only asyncpg used at runtime); `browser-cookie3`, `WMI` (Windows-only), `shadowcopy`, dev tools (`black`, `pytest`, `astroid`, `coverage`, `freezegun`) mixed into runtime deps. Split `requirements.txt` / `requirements-dev.txt`; Dockerfile installs runtime only.

### 4.4 Misc
- `usagi.py:40-41` — `json.load(open(...))` leaks file handles; use `with`.
- `cogs/Hoyolab/genshin_utils.py:37` — hardcoded test UID in `check_cookies`; move to constant with comment.
- Type hints per repo rule: add to every function touched during this refactor.

---

## Suggested order of work

| Step | Items | Size |
|---|---|---|
| 1 | 0.1, 0.2, 0.3, 0.5 | small, same day |
| 2 | 0.4, 1.3, 4.2, 2.5 (off-by-one) | small + tests |
| 3 | 1.1, 1.4 | small infra |
| 4 | 2.1, 2.2, 2.3 | medium, mechanical |
| 5 | 3.1, 3.3, 3.4, 3.6 | medium |
| 6 | 3.2 (upsert), 3.5 | medium, needs schema constraint |
| 7 | 2.4, 4.1 (Music rework) | large, isolate in own branch |
| 8 | 1.2 (encryption at rest), 4.3 | medium, needs user decision on key mgmt |

Every fix lands with a failing-first regression test where logic is involved (repo TDD rule); pure config (0.2, 0.3, 1.1) ships without tests.
