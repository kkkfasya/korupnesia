"""takes data/data_n.html, divide it into some chunks,
each chunk get its own thread and each thread runs it through parse.py.
parsed data will be keep in memory and will be written to database
it also logs the infos
"""

import sys
import math
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from shared.configured_logger import logger
from parse import scrape_korupedia_detail

log = logger.bind(component="dispatcher")

if sys._is_gil_enabled():  # ty: ignore
    logger.warning("GIL is enabled, might not get the best performance")


def _cpu_count() -> int:
    # the fuck do you mean by int | None lol
    c = os.cpu_count()
    if not c:
        return 0

    return c


def get_data_chunk(data_dir, chunk_size: int | None = None) -> list[list[Path]] | None:
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
    ncpu = _cpu_count()
    cs = chunk_size if chunk_size else (ncpu // 2)

    if chunk_size == 0:
        log.error(
            "chunk_size cannot be zero, either misinput or program cannot get cpu count"
        )
        return None

    d = Path(data_dir)
    if not d.is_dir():
        log.error("data_dir provided is not correct")
        log.info("try using absolute path")
        return None

    items = list(d.iterdir())
    if len(items) == 0:
        log.error("no items provided")
        return None

    cs = math.ceil(len(items) / cs)

    return [items[i : i + cs] for i in range(0, len(items), cs)]


def _process_batch_worker(batch: list[Path]) -> None:
    """Processes all items inside a single chunk sequentially.

    Runs natively in parallel with other batch workers on a GIL-free runtime.
    """
    worker_logger = logger.bind(
        worker_size=len(batch),
    )

    worker_logger.info("Batch worker started")

    success = 0
    failed = 0

    for file_path in batch:
        file_logger = worker_logger.bind(
            file=str(file_path),
        )

        try:
            scrape_korupedia_detail(file_path)
            success += 1

        except Exception:
            failed += 1

            file_logger.exception(
                "Failed processing file",
            )

    worker_logger.info(
        "Batch worker completed",
        success=success,
        failed=failed,
    )


def batch_process(data: list[list[Path]]) -> None:
    """Spawns parallel native threads matching the total chunk count.

    Args:
        data: A nested list where each sublist represents an independent
            processing chunk mapped directly to a hardware thread execution line.
    """
    if not data:
        logger.error("no data batches provided")
        return

    num_threads = len(data)

    total_files = sum(len(batch) for batch in data)

    # TODO: why is num thread on the log so big? investigate next time
    log = logger.bind(
        num_threads=num_threads,
        total_batches=len(data),
        total_files=total_files,
    )

    log.info("starting batch processing")

    completed_workers = 0
    failed_workers = 0

    with ThreadPoolExecutor(
        max_workers=num_threads,
        thread_name_prefix="dispatcher",
    ) as executor:
        futures = {
            executor.submit(
                _process_batch_worker,
                batch,
            ): index
            for index, batch in enumerate(data, start=1)
        }

        for future in as_completed(futures):
            batch_id = futures[future]

            try:
                future.result()
                completed_workers += 1
                logger.bind(
                    batch_id=batch_id,
                ).info(
                    "worker completed",
                )

            except Exception:
                logger.bind(
                    batch_id=batch_id,
                ).exception(
                    "worker crashed",
                )

    log.info(
        "batch processing finished",
        completed_workers=completed_workers,
        failed_workers=failed_workers,
    )
