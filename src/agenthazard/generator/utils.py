from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, ValidationError, model_validator

N_TASK_COMBINATIONS = 5


class AttackSetting(BaseModel):
    difficulty: Literal[0, 1, 2]
    text: list[str]
    template: tuple[str, str]
    action: Literal[
        "click",
        "long_press",
        "navigate_back",
        "navigate_home",
        "open_app",
        "status",
    ]
    area: Optional[list[int]] = None
    relative_index: Optional[int] = None
    relative_text: Optional[str] = None

    @model_validator(mode="before")
    def process_text(cls, value: dict):
        if "text" not in value:
            raise ValidationError("`text` is required.")
        if isinstance(value["text"], str):
            value["text"] = [value["text"]]
        return value


class AttackSettingValidator(BaseModel):
    package: str
    template: str
    settings: list[AttackSetting]

    @model_validator(mode="before")
    def process_template(cls, value: dict):
        if "settings" not in value:
            raise ValidationError("`settings` is required.")
        for setting in value["settings"]:
            if isinstance(setting, dict) and "template" not in setting:
                setting["template"] = (value["package"], value["template"])
            if "template" in setting and isinstance(setting["template"], str):
                setting["template"] = (value["package"], setting["template"])
        return value


def load_attack_setting_params(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with path.open("r") as f:
        settings = AttackSettingValidator(**yaml.safe_load(f)).settings
    return settings


def ensure_files_exist(data_root: Path, essential_files: list[str]):
    if not data_root.exists():
        raise FileNotFoundError(f"Directory not found: {data_root}")
    if not data_root.is_dir():
        raise NotADirectoryError(f"Not a directory: {data_root}")
    for file in essential_files:
        if not (data_root / file).exists():
            raise FileNotFoundError(f"File not found: {data_root / file}")
