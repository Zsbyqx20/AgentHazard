from pathlib import Path
from typing import Any, Optional

import pandas as pd
import structlog
import yaml
from jinja2 import Environment, FileSystemLoader
from tabulate import tabulate

from .utils import AttackSetting, load_attack_setting_params

TASKS_DIR = "tasks"
INTERFACE_DIR = "interface"
logger = structlog.get_logger(__name__)


class AttackSettingRegistry:
    def __init__(self, jinja_root: str, print_registry_summary: bool = False) -> None:
        self._jinja_root = Path(jinja_root).absolute()
        self._env = Environment(
            loader=FileSystemLoader(self._jinja_root),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self._setting_df, self._task_data = self._discover_tasks(print_registry_summary)

    def _discover_tasks(self, add_summary: bool = False):
        tasks_path = self._jinja_root / TASKS_DIR
        interface_path = self._jinja_root / INTERFACE_DIR
        data = []
        mapping: dict[str, list[AttackSetting]] = {}

        for entry in tasks_path.iterdir():
            if not entry.is_file() or entry.suffix != ".yaml":
                continue
            settings = load_attack_setting_params(entry)
            mapping[entry.name] = settings
            for setting in settings:
                template_path = (
                    interface_path / setting.template[0] / f"{setting.template[1]}.j2"
                ).relative_to(self._jinja_root)
                data.append({
                    "task_name": entry.stem,
                    "difficulty": setting.difficulty,
                    "action": setting.action,
                    "setting": setting,
                    "template": self._env.get_template(str(template_path)),
                })

        df = pd.DataFrame(data)
        if add_summary:
            summary = (
                df.groupby("task_name")
                .agg({
                    "difficulty": lambda x: sorted(list(set(x))),
                    "action": lambda x: len(set(x)),
                    "setting": "count",
                })
                .rename(columns={"setting": "total_settings"})  # type: ignore
            )

            print("\n" + "=" * 50)
            print("📊 Tasks Discovery Summary")
            print("=" * 50)

            table = tabulate(
                summary.reset_index().to_dict(orient="records"),
                headers={
                    "task_name": "🎯 Task Name",
                    "difficulty": "🔢 Difficulty Levels",
                    "action": "🎬 Actions",
                    "total_settings": "📝 Total Settings",
                },
                tablefmt="pretty",
            )
            print(f"\n{table}")

            print("\n" + "-" * 50)
            print(f"📌 Total Tasks: {len(summary)}")
            print(f"📌 Total Settings: {df['setting'].count()}")
            print(
                f"📌 Unique Difficulty Levels: {sorted(df['difficulty'].unique().tolist())}"
            )
            print(f"📌 Unique Actions: {sorted(df['action'].unique())}")
            print("-" * 50 + "\n")

        return df, mapping

    def generate_config(
        self,
        task_name: Optional[str | list[str]] = None,
        difficulty: Optional[int | list[int]] = None,
        action: Optional[str | list[str]] = None,
    ) -> dict[tuple[int, str], dict[str, Any]]:
        query = self._setting_df

        if task_name:
            if isinstance(task_name, str):
                task_name = [task_name]
            query = query[query["task_name"].isin(task_name)]
        if difficulty is not None:
            if isinstance(difficulty, int):
                difficulty = [difficulty]
            query = query[query["difficulty"].isin(difficulty)]  # type: ignore
        if action:
            if isinstance(action, str):
                action = [action]
            query = query[query["action"].isin(action)]  # type: ignore

        # Group by difficulty and action
        results = {}
        for _, row in query.iterrows():  # type: ignore
            setting_key = (row["difficulty"], row["action"])
            if setting_key not in results:
                results[setting_key] = {}

            rendered = row["template"].render(**row["setting"].model_dump())  # type: ignore
            results[setting_key][row["task_name"]] = yaml.safe_load(rendered)

        return results
