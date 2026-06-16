"""
takes data/data_n.html, divide it into some chunks,
each chunk get its own thread and each thread runs it through parse.py.
parsed data will be keep in memory and will be written to database
it also logs the infos
"""

from cmath import log

from pathlib import Path
from loguru import logger
import sys
import json
import traceback

# absolute path to the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGFORMAT = "<level>[{level}]</level> | <green>{time}</green> | {message}"
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

logger.info("HALLo")
