import asyncio
import logging
from collections.abc import Awaitable, Callable
from pathlib import Path

import click
import pandas as pd
import structlog
from dotenv import load_dotenv
from pandas import DataFrame
from rich.progress import MofNCompleteColumn, Progress, SpinnerColumn

from ..agent import (
    M3A,
    T3A,
    Agent,
    Autodroid,
    UGround,
    autodroid_eval_task,
    m3a_eval_task,
    t3a_eval_task,
    uground_eval_task,
)
from ..agent.utils import JSONAction
from ..api import ASYNC_CLIENT_MAPPING, AsyncClient
from ..dataset import AgentHazardDataset
from ..log import default_logging_setup
from ..models import EvalResult, Scenario, Task, ValueResult
from ..utils import async_gather_with_progress

load_dotenv()


# 配置日志
default_logging_setup(
    target_module="agenthazard",
    filename="logs/static_eval.log",
    target_module_level_console=logging.INFO,
    target_module_level_file=logging.DEBUG,
)
logger = structlog.get_logger(__name__)


def build_value_result(df: pd.DataFrame) -> ValueResult:
    value_result = ValueResult()
    for _, row in df.iterrows():
        value_result.add(
            EvalResult(
                correct=bool(row["correct"]),
                is_misled=bool(row["misled"]),
                invalid=bool(row["invalid"]),
            )
        )
    return value_result


def log_metrics(label: str, value_result: ValueResult) -> None:
    logger.info(
        f"{label} - "
        f"Accuracy: {value_result.accuracy:.1%}; "
        f"Misleading rate: {value_result.is_misled_rate:.1%}; "
        f"Invalid rate: {value_result.invalid_rate:.1%}; "
        f"Total: {value_result.total}"
    )


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
        "autodroid": Autodroid,
        "uground": UGround,
    }
    agent = agent_mapping[agent_type]()
    dataset = AgentHazardDataset(Path(data_dir))
    value_result = ValueResult()
    task_configs: dict[tuple[str, str, str], dict[str, bool]] = {}

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
                    correct=bool(row["correct"]),
                    is_misled=bool(row["misled"]),
                    invalid=bool(row["invalid"]),
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
                task_configs[task_key] = {
                    "has_click": task.get_misleading_config("click") is not None,
                    "has_status": task.get_misleading_config("status") is not None,
                }
                if task_key in executed_tasks:
                    logger.debug(f"Skipping already executed task: {task_key}")
                    continue
                if (
                    misleading_action is not None
                    and task.get_misleading_config(misleading_action) is None
                ):
                    logger.debug(
                        "Skipping task without matching misleading config",
                        misleading_action=misleading_action,
                        **metadata,
                    )
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

    if hasattr(agent, "aclose"):
        await agent.aclose()  # type: ignore

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

    log_metrics("Overall", value_result)

    new_df = pd.DataFrame(results)
    if continue_eval and Path(output).exists():
        existing_df = pd.read_parquet(output)
        df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        df = new_df
    df.to_parquet(output)

    if misleading_action is None and not df.empty:
        task_keys = list(zip(df["package"], df["folder"], df["task_description"]))
        click_mask = [
            task_configs.get(task_key, {}).get("has_click", False)
            for task_key in task_keys
        ]
        status_mask = [
            task_configs.get(task_key, {}).get("has_status", False)
            for task_key in task_keys
        ]

        click_df = df[click_mask]
        status_df = df[status_mask]

        if not isinstance(click_df, DataFrame) or not isinstance(status_df, DataFrame):
            raise TypeError("Subset selection did not produce a DataFrame")

        log_metrics("Click subset", build_value_result(click_df))
        log_metrics("Status subset", build_value_result(status_df))


@click.command()
@click.option(
    "-d",
    "--data-dir",
    type=click.Path(exists=True),
    default="data",
    help="Dataset directory path",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    default="results.parquet",
    help="Output file path for results",
)
@click.option(
    "-c",
    "--concurrency",
    type=int,
    default=20,
    help="Number of concurrent tasks",
)
@click.option(
    "--continue/--no-continue",
    "continue_eval",
    default=True,
    help="Continue from last checkpoint",
)
@click.option(
    "-a",
    "--agent",
    type=click.Choice(["m3a", "t3a", "autodroid", "uground"]),
    default="m3a",
    help="Agent type to use for evaluation",
)
@click.option(
    "--model",
    type=str,
    help="Model to use for evaluation",
)
@click.option(
    "--client",
    type=click.Choice(list(ASYNC_CLIENT_MAPPING.keys())),
    help="Client to use for evaluation",
)
@click.option(
    "--attack",
    type=click.Choice(["click", "status", "navigate"]),
    default=None,
    help="Specify attack type for misleading evaluation",
)
def main(
    data_dir: str,
    output: str,
    concurrency: int,
    continue_eval: bool,
    agent: str,
    model: str,
    client: str,
    attack: str | None,
):
    """Mobile application security evaluation tool"""
    eval_func: Callable[
        [AsyncClient, Agent, str, Scenario, Task, asyncio.Semaphore, str | None],
        Awaitable[tuple[str, JSONAction, EvalResult, dict]],
    ] = (
        m3a_eval_task
        if agent == "m3a"
        else t3a_eval_task
        if agent == "t3a"
        else uground_eval_task
        if agent == "uground"
        else autodroid_eval_task
    )

    if output == "results.parquet":
        suffix_parts = []
        suffix_parts.append(f"agent_{agent}")
        if model:
            model_name = model.replace("/", "-").replace(".", "-").replace(" ", "_")
            suffix_parts.append(f"model_{model_name}")
        suffix_parts.append(f"client_{client}")
        if attack:
            suffix_parts.append(f"attack_{attack}")
        output = f"results-{'_'.join(suffix_parts)}.parquet"
    logger.info(f"The result will be saved to: {output}")

    if client not in ASYNC_CLIENT_MAPPING:
        raise ValueError(f"Invalid client: {client}")
    asyncio.run(
        run_evaluation(
            data_dir=data_dir,
            output=output,
            concurrency=concurrency,
            continue_eval=continue_eval,
            eval_func=eval_func,
            agent_type=agent,
            model=model,
            misleading_action=attack,
            client_cls=ASYNC_CLIENT_MAPPING[client],
        )
    )


if __name__ == "__main__":
    main()
