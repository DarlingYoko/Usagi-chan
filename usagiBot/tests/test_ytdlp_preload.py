import subprocess
import sys
import textwrap
from pathlib import Path

from usagiBot.tests.utils import *  # noqa: F401,F403  (sets BOT_OWNER/BOT_ID)

PRELOAD_MODULE = Path(__file__).parents[1] / "cogs" / "Music" / "ytdlp_preload.py"

# Regression: yt-dlp lazily imports its YouTube JS-challenge modules, which
# import each other in a cycle. Two executor threads hitting that first import
# together fail with "cannot import name '_EJS_WIKI_URL' from partially
# initialized module". Preloading from the main thread must prevent it.
RACE_PROBE = textwrap.dedent(
    """
    import importlib, sys, threading
    {preload}
    mods = [
        "yt_dlp.extractor.youtube.jsc._director",
        "yt_dlp.extractor.youtube.jsc._builtin.ejs",
        "yt_dlp.extractor.youtube.jsc._builtin.bun",
        "yt_dlp.extractor.youtube.jsc.provider",
    ]
    errors = []

    def go(name):
        try:
            importlib.import_module(name)
        except Exception as exc:
            errors.append(f"{{name}}: {{exc}}")

    threads = [threading.Thread(target=go, args=(m,)) for m in mods]
    [t.start() for t in threads]
    [t.join() for t in threads]
    print("ERRORS:" + "|".join(errors))
    """
)


def _run_probe(preload: str) -> str:
    result = subprocess.run(
        [sys.executable, "-I", "-c", RACE_PROBE.format(preload=preload)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip().splitlines()[-1]


def test_preload_prevents_concurrent_import_race() -> None:
    # load by path: importing the usagiBot.cogs.Music package needs bot env vars
    preload = textwrap.dedent(
        f"""
        import importlib.util as u
        spec = u.spec_from_file_location('ytdlp_preload', {str(PRELOAD_MODULE)!r})
        mod = u.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.preload_ytdlp()
        """
    )
    assert _run_probe(preload) == "ERRORS:"
