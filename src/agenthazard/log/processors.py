import datetime
from typing import Any
from zoneinfo import ZoneInfo

import structlog

from .rich_types import (
    RICH_CONSOLE_EVENT_LEVEL_STYLE,
    RICH_CONSOLE_STYLES,
    TARGET_PLACEHOLDER,
    RichConsoleStyle,
)


def rich_style_wrapper(src: Any, style: str) -> str:
    """
    Wraps the given string with a specified rich text style.

    Args:
        src (str): The source string to be styled.
        style (str): The style to be applied. If an empty string is provided, the source string is returned unmodified.

    Returns:
        str: The styled string if a style is provided, otherwise the original string.
    """
    if style == "":
        return str(src)
    return f"[{style}]{str(src)}[/]"


def rich_style_format_parser(
    src: Any,
    style: RichConsoleStyle,
    placeholder: str = TARGET_PLACEHOLDER,
    prefix_key: str | None = None,
) -> str:
    """
    Parses and formats an object using a specified rich console style.
    Args:
        src (Any): The source object to be formatted.
        style (RichConsoleStyle): A dictionary containing style information.
        placeholder (str, optional): The placeholder in the format string to be replaced by the source string. Defaults to TARGET_PLACEHOLDER.
        prefix_key (Optional[str], optional): An optional key to use as a prefix. If not provided, the key from the style dictionary is used. Defaults to None.
    Returns:
        str: The formatted string with the applied rich console style.
    """
    key = style["key"] if prefix_key is None else prefix_key
    target = style["format"].replace(placeholder, str(src))
    prefix_format = style.get("prefix_format", "u")
    prefix = rich_style_wrapper(key.upper(), prefix_format)
    target = rich_style_wrapper(target, style["style"])
    return f"{prefix}: {target}"


def rich_console_processor(_, __, event_dict: structlog.typing.EventDict):
    """
    Processes an event dictionary to format its text using `rich` styles.

    This function modifies the given event dictionary by applying rich text
    formatting to its keys based on predefined styles. The formatted text is
    then combined into a single string and stored back in the event dictionary
    under the "event" key.

    Args:
        _ (Any): Placeholder argument, not used.
        __ (Any): Placeholder argument, not used.
        event_dict (structlog.typing.EventDict): The event dictionary containing
            the log event data to be processed.

    Returns:
        structlog.typing.EventDict: The modified event dictionary with rich
        formatted text under the "event" key.
    """
    event_modified: list[str] = []

    original_event = event_dict.pop("event", "")
    level: str = event_dict.pop("level", "debug")
    event_style = RICH_CONSOLE_EVENT_LEVEL_STYLE.get(level, "")
    original_event = rich_style_wrapper(original_event, event_style)

    misc_style = RICH_CONSOLE_STYLES[-1]
    for style in RICH_CONSOLE_STYLES:
        key = style["key"]
        if key in event_dict:
            tmp = rich_style_format_parser(
                event_dict.pop(key),
                style,
            )
            event_modified.append(f"{tmp:<30}")
    for key in event_dict:
        event_modified.append(
            rich_style_format_parser(
                event_dict[key],
                misc_style,
                prefix_key=key,
            )
        )
    attached_information = (original_event + "\n" + "".join(event_modified)).strip()
    event_dict = {"event": attached_information}
    return event_dict


def file_json_timezone_processor(_, __, event_dict: structlog.typing.EventDict):
    localized_time = datetime.datetime.now(ZoneInfo("Asia/Shanghai")).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    event_dict["timestamp"] = localized_time
    return event_dict
