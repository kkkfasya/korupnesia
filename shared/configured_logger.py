import traceback
import sys
import json
from pathlib import Path
from loguru import logger

# absolute path to the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATADIR = Path(f"{PROJECT_ROOT}/data")
LOGFORMAT = "<level>[{level}]</level>: <green>{time}</green> | {extra[component]} | {message}"
LOGSTASH_LOGFILE = Path(f"{PROJECT_ROOT}/logs/dispatcher_serializable.log")
_configured = False


def ecs_formatter(record):
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

    return json.dumps(event, ensure_ascii=False) + "\n"


# TODO: add filter for different logfile
def setup_logger(*, level: str = "INFO"):
    global _configured

    if _configured:
        return

    log_dir = Path(f"{PROJECT_ROOT}/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()

    logger.add(
        sys.stderr,
        level=level,
        enqueue=True,
        format=LOGFORMAT,
    )

    logger.add(
        f"{log_dir}/dispatcher.log",
        level=level,
        rotation="100 MB",
        retention="30 days",
        compression="gz",
        encoding="utf-8",
        enqueue=True,
        backtrace=True,
        format=LOGFORMAT,
    )
    
    # BUG:i dont understand this, will configure later on
    # logger.add(
    #     f"{log_dir}/ecs-log.json",
    #     level=level,
    #     rotation="100 MB",
    #     retention="30 days",
    #     compression="gz",
    #     encoding="utf-8",
    #     enqueue=True,
    #     backtrace=True,
    #     diagnose=False,
    #     format=ecs_formatter,
    # )

    _CONFIGURED = True


setup_logger()
