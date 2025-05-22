import asyncio
import json
import logging
import os
import re
from typing import Awaitable, TypeVar

import pandas as pd
from rich.progress import Progress

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def async_gather_with_progress(
    progress: Progress,
    tasks: list[Awaitable[T]],
    name: str = "Processing...",
):
    with progress:
        tp = progress.add_task(name, total=len(tasks))
        results: list[T] = []

        for coro in asyncio.as_completed(tasks):
            try:
                result = await coro
                results.append(result)
            except asyncio.TimeoutError:
                logger.error("TimeoutError occurred during processing")
            except Exception as e:
                logger.exception(f"Error occurred during processing: {e}")
            finally:
                progress.update(tp, advance=1)
    return results


def recover_from_log(log_path: str, ckpt_path: str):
    # Ensure the ckpt_path has .parquet extension
    if not ckpt_path.endswith(".parquet"):
        ckpt_path += ".parquet"

    # Read from log file
    with open(log_path) as f:
        data = [json.loads(line) for line in f]
    pattern = re.compile(r"correct=(\w+), is_misled=(\w+), invalid=(\w+)")
    results = []
    for dt in data:
        if "result" in dt:
            matched = pattern.search(dt["result"])
            if not matched:
                continue
            results.append({
                "package": dt["package"],
                "folder": dt["folder"],
                "task_description": dt["task_description"],
                "correct": matched.group(1) == "True",
                "misled": matched.group(2) == "True",
                "invalid": matched.group(3) == "True",
                "reason": dt["reason"],
                "action": dt["action"],
            })
    new_df = pd.DataFrame(results)

    # If checkpoint exists, merge with existing data
    if os.path.exists(ckpt_path):
        existing_df = pd.read_parquet(ckpt_path)
        # Merge based on package, folder and task_description to avoid duplicates
        df = pd.concat([existing_df, new_df]).drop_duplicates(
            subset=["package", "folder", "task_description"], keep="last"
        )
    else:
        df = new_df

    df.to_parquet(ckpt_path)
    return df
