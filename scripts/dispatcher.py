"""
takes data/data_n.html, divide it into some chunks,
each chunk get its own thread and each thread runs it through parse.py.
parsed data will be keep in memory and will be written to database
it also logs the infos
"""

from pathlib import Path
from loguru import logger
import sys
import os
import json
import traceback

# absolute path to the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATADIR = Path(f"{PROJECT_ROOT}/data")
LOGFORMAT = "<level>[{level}]</level> | <green>{time}</green> | {module}.py | {function}(...) | {message}"
LOGSTASH_LOGFILE = Path(f"{PROJECT_ROOT}/logs/dispatcher_serializable.log")


def logstash_sink(message):
    record = message.record
    event = {
        "@timestamp": record["time"].isoformat(),
        "log.level": record["level"].name.lower(),
        "message": record["message"],
        "log.logger": record["name"],
        "process.pid": record["process"].id,
        "thread.id": record["thread"].id,
        "source.module": record["module"],
        "source.function": record["function"],
        "source.line": record["line"],
        **record["extra"],
    }

    if record["exception"]:
        exc = record["exception"]
        event["error"] = {
            "type": exc.type.__name__,
            "message": str(exc.value),
            "stack_trace": "".join(
                traceback.format_exception(
                    exc.type,
                    exc.value,
                    exc.traceback,
                )
            ),
        }

    with LOGSTASH_LOGFILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False))
        f.write("\n")


logger.remove()

# stderr and normal logfile
logger.add(sys.stderr, format=LOGFORMAT)
logger.add(
    f"{PROJECT_ROOT}/logs/dispatcher.log",
    retention="14 days",
    level="DEBUG",
    format=LOGFORMAT,
)

# for logstash
logger.add(logstash_sink)

if sys._is_gil_enabled():  # ty: ignore
    logger.warning("GIL is enabled, might not get the best performance")


def _cpu_count() -> int:
    # the fuck do you mean by int | None lol
    c = os.cpu_count()
    if not c:
        return 0

    return c


def get_data_chunk(data_dir, chunk_size: int | None) -> list[list[Path]] | None:
    """Splits files inside a directory into smaller sublists (chunks).

    scans the provided directory, retrieves all immediate filesystem entries, and partitions them into batches.
    The chunk size used for slicing, if not provided, will take machine cpu count and divided by two, otherwise will
    batch accordingly to the size provided

    Args:
        data_dir: The path or string path to the directory containing files
            to partition into chunks.
        chunk_size: if not provided, will take machine cpu count and be divided by two

    Returns:
        A nested list of ``Path`` objects where each inner list represents
        a processing chunk, or ``None`` if validation fails or the directory
        does not exist.
    """
    cs: int

    if chunk_size == 0:
        logger.error(
            "chunk_size cannot be zero, either misinput or program cannot get cpu count"
        )
        return None

    if chunk_size is None:
        cs = _cpu_count() // 2
    else:
        cs = chunk_size

    d = Path(data_dir)
    if not d.is_dir():
        logger.error("data_dir provided is not correct")
        return None

    items = list(d.iterdir())

    return [items[i : i + cs] for i in range(0, len(items), cs)]
