from typing import NotRequired, TypedDict


class RichConsoleStyle(TypedDict):
    key: str
    style: str
    format: str
    prefix_format: NotRequired[str]


TARGET_PLACEHOLDER = "@"

RICH_CONSOLE_STYLES: list[RichConsoleStyle] = [
    {
        "key": "logger",
        "style": "green3",
        "format": f"{TARGET_PLACEHOLDER}, ",
    },
    {
        "key": "id",
        "style": "dark_green",
        "format": f"[{TARGET_PLACEHOLDER}], ",
    },
    {"key": "MISC", "style": "orange4", "format": f"{TARGET_PLACEHOLDER}, "},
]

RICH_CONSOLE_EVENT_LEVEL_STYLE = {
    "info": "b uu frame dodger_blue2",
    "debug": "b uu green3",
    "warning": "b uu orange_red1",
    "error": "b uu red1",
    "critical": "b uu red1",
}
