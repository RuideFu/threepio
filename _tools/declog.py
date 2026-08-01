"""
Debug logging for the declinometer read path.

Writes to stderr and to dec-debug.log, flushing every record so the trail
survives a hard freeze (e.g. a blocking serial read that never returns).
"""
import logging
import sys

LOG_FILENAME = "dec-debug.log"

_logger = None


class _FlushingFileHandler(logging.FileHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()


def get_dec_logger() -> logging.Logger:
    """Lazily build the shared declinometer logger."""
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger("threepio.dec")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d %(levelname)s %(message)s", datefmt="%H:%M:%S"
    )

    file_handler = _FlushingFileHandler(LOG_FILENAME, mode="a", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    _logger = logger
    logger.info("--- dec logging started ---")
    return logger
