import asyncio
import argparse
import logging
from pathlib import Path
from typing import Awaitable, Callable

import pandas as pd
import structlog
from dotenv import load_dotenv
from rich.progress import MofNCompleteColumn, Progress, SpinnerColumn

from .. import AgentHazardDataset
from ..agent import (
    M3A,
    T3A,
    Agent,
    m3a_eval_task,
    t3a_eval_task,
)
from ..agent.utils import JSONAction
from ..api import ASYNC_CLIENT_MAPPING, AsyncClient
from ..log import default_logging_setup
from ..models import EvalResult, Scenario, Task, ValueResult
from ..utils import async_gather_with_progress

load_dotenv()


# 配置日志
default_logging_setup(
    target_module="mobile_safety_bench",
    filename="logs/static_eval.log",
    target_module_level_console=logging.INFO,
    target_module_level_file=logging.DEBUG,
)
logger = structlog.get_logger(__name__)


async def run_evaluation(
    data_dir: str,
    output: str,
    concurrency: int,
    continue_eval: bool,
    eval_func: Callable[
        [AsyncClient, Agent, str, Scenario, Task, asyncio.Semaphore, str | None],
        Awaitable[tuple[str, JSONAction, EvalResult, dict]],
    ],
    agent_type: str,
    model: str,
    client_cls: type[AsyncClient],
    misleading_action: str | None = None,
):
    agent_mapping: dict[str, type[Agent]] = {
        "m3a": M3A,
        "t3a": T3A,
    }
    agent = agent_mapping[agent_type]()
    dataset = AgentHazardDataset(Path(data_dir))
    value_result = ValueResult()

    execution: list[Awaitable[tuple[str, JSONAction, EvalResult, dict]]] = []
    progress = Progress(
        SpinnerColumn(),
        *Progress.get_default_columns(),
        MofNCompleteColumn(),
    )
    semaphore = asyncio.Semaphore(concurrency)
    executed_tasks = set()

    if continue_eval and Path(output).exists():
        df = pd.read_parquet(output)
        for _, row in df.iterrows():
            value_result.add(
                EvalResult(
                    correct=row["correct"],  # type: ignore
                    is_misled=row["misled"],  # type: ignore
                    invalid=row["invalid"],  # type: ignore
                )
            )
            task_key = (row["package"], row["folder"], row["task_description"])
            executed_tasks.add(task_key)

    async with client_cls() as client:
        for scenario in dataset:
            for task in scenario.tasks:
                metadata = {
                    "package": scenario.package,
                    "folder": scenario.folder,
                    "task_description": task.description,
                }
                task_key = (
                    metadata["package"],
                    metadata["folder"],
                    metadata["task_description"],
                )
                if task_key in executed_tasks:
                    logger.debug(f"Skipping already executed task: {task_key}")
                    continue

                execution.append(
                    eval_func(
                        client,
                        agent,
                        model,
                        scenario,
                        task,
                        semaphore,
                        misleading_action,
                        **metadata,
                    )
                )

        tmp_res = await async_gather_with_progress(progress, execution)

    results = []
    for reason, action, result, metadata in tmp_res:
        value_result.add(result)
        record = {
            "reason": reason,
            "action": str(action),
            "correct": result.correct,
            "misled": result.is_misled,
            "invalid": result.invalid,
            "package": metadata["package"],
            "folder": metadata["folder"],
            "task_description": metadata["task_description"],
        }
        results.append(record)

    logger.info(
        f"Accuracy: {value_result.accuracy:.1%}; "
        f"Misleading rate: {value_result.is_misled_rate:.1%}; "
        f"Invalid rate: {value_result.invalid_rate:.1%}"
    )

    new_df = pd.DataFrame(results)
    if continue_eval and Path(output).exists():
        existing_df = pd.read_parquet(output)
        df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        df = new_df
    df.to_parquet(output)


def add_eval_arguments(parser):
    """Add evaluation arguments to a parser"""
    parser.add_argument(
        "-d", "--data-dir", type=str, default="data", help="Dataset directory path"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="results.parquet",
        help="Output file path for results",
    )
    parser.add_argument(
        "-c", "--concurrency", type=int, default=20, help="Number of concurrent tasks"
    )
    parser.add_argument(
        "--no-continue",
        dest="continue_eval",
        action="store_false",
        help="Do not continue from last checkpoint",
    )
    parser.set_defaults(continue_eval=True)
    parser.add_argument(
        "-a",
        "--agent",
        choices=["m3a", "t3a"],
        default="m3a",
        help="Agent type to use for evaluation",
    )
    parser.add_argument("--model", type=str, help="Model to use for evaluation")
    parser.add_argument(
        "--client",
        choices=list(ASYNC_CLIENT_MAPPING.keys()),
        help="Client to use for evaluation",
    )
    parser.add_argument(
        "--attack",
        choices=["click", "status", "navigate"],
        default=None,
        help="Specify attack type for misleading evaluation",
    )
    return parser


def main(args=None):
    """Mobile application security evaluation tool"""
    if args is None:
        parser = argparse.ArgumentParser(
            description="Mobile application security evaluation tool"
        )
        parser = add_eval_arguments(parser)
        args = parser.parse_args()

    eval_func: Callable[
        [AsyncClient, Agent, str, Scenario, Task, asyncio.Semaphore, str | None],
        Awaitable[tuple[str, JSONAction, EvalResult, dict]],
    ] = m3a_eval_task if args.agent == "m3a" else t3a_eval_task

    output = args.output
    if output == "results.parquet":
        suffix_parts = []
        suffix_parts.append(f"agent_{args.agent}")
        if args.model:
            model_name = (
                args.model.replace("/", "-").replace(".", "-").replace(" ", "_")
            )
            suffix_parts.append(f"model_{model_name}")
        suffix_parts.append(f"client_{args.client}")
        if args.attack:
            suffix_parts.append(f"attack_{args.attack}")
        output = f"results-{'_'.join(suffix_parts)}.parquet"
    logger.info(f"The result will be saved to: {output}")

    if args.client not in ASYNC_CLIENT_MAPPING:
        raise ValueError(f"Invalid client: {args.client}")

    asyncio.run(
        run_evaluation(
            data_dir=args.data_dir,
            output=output,
            concurrency=args.concurrency,
            continue_eval=args.continue_eval,
            eval_func=eval_func,
            agent_type=args.agent,
            model=args.model,
            misleading_action=args.attack,
            client_cls=ASYNC_CLIENT_MAPPING[args.client],
        )
    )


if __name__ == "__main__":
    main()
