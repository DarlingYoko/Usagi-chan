import importlib
import logging

logger = logging.getLogger(__name__)

# yt-dlp imports these lazily, from whichever executor thread first extracts a
# YouTube URL. They import each other in a cycle, so two threads racing the
# first import raise "cannot import name ... partially initialized module".
_LAZY_MODULES = (
    "yt_dlp.extractor.youtube.jsc._director",
    "yt_dlp.extractor.youtube.jsc._builtin.ejs",
    "yt_dlp.extractor.youtube.jsc._builtin.bun",
    "yt_dlp.extractor.youtube.jsc._builtin.deno",
    "yt_dlp.extractor.youtube.jsc._builtin.node",
    "yt_dlp.extractor.youtube.jsc._builtin.quickjs",
    "yt_dlp.extractor.youtube.jsc.provider",
)


def preload_ytdlp() -> None:
    """Import yt-dlp's lazily loaded modules once, single-threaded, at startup."""
    from yt_dlp.extractor import gen_extractor_classes

    gen_extractor_classes()
    for name in _LAZY_MODULES:
        try:
            importlib.import_module(name)
        except ImportError:
            # Private yt-dlp layout; a missing module must not stop the cog.
            logger.warning("yt-dlp module %s not importable; skipping preload", name)
