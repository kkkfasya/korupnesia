"""takes data/data_n.html, divide it into some chunks,
each chunk get its own thread and each thread runs it through parse.py.
parsed data will be keep in memory and will be written to database
it also logs the infos
"""

import sys
import os
from pathlib import Path
from shared.configured_logger import logger
from .parse import scrape_korupedia_detail

logger = logger.bind(component="dispatcher")

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


def _process_batch_worker(batch: list[Path]) -> None:
    """Processes all items inside a single chunk sequentially

    Runs natively in parallel with other batch workers on a GIL-free runtime.
    """
    for file_path in batch:
        try:
            scrape_korupedia_detail(file_path)
        except Exception:
            # Prevents an unhandled exception in one file from halting
            # the entire thread execution block.
            pass


#TODO: implement
def batch_process(data: list[list[Path]]) -> None:
    """Spawns parallel native threads matching the total chunk count.

    Args:
        data: A nested list where each sublist represents an independent
            processing chunk mapped directly to a hardware thread execution line.
    """
    if not data:
        return

    num_threads = len(data)
    ...
