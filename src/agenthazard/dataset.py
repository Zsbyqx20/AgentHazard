from pathlib import Path
from typing import overload

import structlog

from .models import Scenario

logger = structlog.get_logger(__name__)


class AgentHazardDataset:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.scenarios = self._validate()

    def _validate(self):
        data: dict[str, dict[str, Scenario]] = {}
        for package_dir in self.root.iterdir():
            if not package_dir.is_dir():
                continue
            scenarios: dict[str, Scenario] = {}
            for scenario_dir in package_dir.iterdir():
                if not scenario_dir.is_dir():
                    continue
                required_files = [
                    "metadata.json",
                    "screenshot.jpg",
                    "original_vh.json",
                    "filtered_elements.json",
                ]
                for file in required_files:
                    if not (scenario_dir / file).exists():
                        logger.warning(
                            "File not found; skipping",
                            package_name=package_dir.name,
                            scenario_name=scenario_dir.name,
                            file=file,
                        )
                        continue
                scenarios[scenario_dir.name] = Scenario(scenario_dir)
            data[package_dir.name] = scenarios
        return data

    def __len__(self):
        return len(self.scenarios)

    @overload
    def __getitem__(self, index: str) -> dict[str, Scenario]: ...

    @overload
    def __getitem__(self, index: tuple[str, str]) -> Scenario: ...

    def __getitem__(self, index: str | tuple[str, str]):
        if isinstance(index, str):
            return self.scenarios[index]
        else:
            return self.scenarios[index[0]][index[1]]

    def __iter__(self):
        for scenarios in self.scenarios.values():
            for scenario in scenarios.values():
                yield scenario
