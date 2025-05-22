import ast
import json
import re
from dataclasses import dataclass
from typing import Any, Optional

from PIL import Image, ImageDraw, ImageFont

from ..models import BoundingBox, UIElement

_JSON_SEPARATORS = (",", ":")

ANSWER = "answer"
CLICK = "click"
DOUBLE_TAP = "double_tap"
INPUT_TEXT = "input_text"
KEYBOARD_ENTER = "keyboard_enter"
LONG_PRESS = "long_press"
NAVIGATE_BACK = "navigate_back"
NAVIGATE_HOME = "navigate_home"
OPEN_APP = "open_app"
SCROLL = "scroll"
STATUS = "status"
SWIPE = "swipe"
UNKNOWN = "unknown"
WAIT = "wait"

_ACTION_TYPES = (
    CLICK,
    DOUBLE_TAP,
    SCROLL,
    SWIPE,
    INPUT_TEXT,
    NAVIGATE_HOME,
    NAVIGATE_BACK,
    KEYBOARD_ENTER,
    OPEN_APP,
    STATUS,
    WAIT,
    LONG_PRESS,
    ANSWER,
    UNKNOWN,
)

_SCROLL_DIRECTIONS = ("left", "right", "down", "up")


def generate_ui_element_description(ui_element: UIElement, index: int) -> str:
    """Generate a description for a given UI element with important information.

    Args:
      ui_element: UI elements for the current screen.
      index: The numeric index for the UI element.

    Returns:
      The description for the UI element.
    """
    element_description = f'UI element {index}: {{"index": {index}, '
    if ui_element.text:
        element_description += f'"text": "{ui_element.text}", '
    if ui_element.content_description:
        element_description += (
            f'"content_description": "{ui_element.content_description}", '
        )
    if ui_element.hint_text:
        element_description += f'"hint_text": "{ui_element.hint_text}", '
    if ui_element.tooltip:
        element_description += f'"tooltip": "{ui_element.tooltip}", '
    element_description += (
        f'"is_clickable": {"True" if ui_element.is_clickable else "False"}, '
    )
    element_description += (
        f'"is_long_clickable": {"True" if ui_element.is_long_clickable else "False"}, '
    )
    element_description += (
        f'"is_editable": {"True" if ui_element.is_editable else "False"}, '
    )
    if ui_element.is_scrollable:
        element_description += '"is_scrollable": True, '
    if ui_element.is_focusable:
        element_description += '"is_focusable": True, '
    element_description += (
        f'"is_selected": {"True" if ui_element.is_selected else "False"}, '
    )
    element_description += (
        f'"is_checked": {"True" if ui_element.is_checked else "False"}, '
    )
    return element_description[:-2] + "}"


def generate_concise_ui_element_description(ui_element: UIElement, index: int) -> str:
    """Generate a description for a given UI element with important information.

    Args:
      ui_element: UI elements for the current screen.
      index: The numeric index for the UI element.

    Returns:
      The description for the UI element.
    """
    element_description = f'Element {index}: {{"index": {index}, '
    if ui_element.text:
        element_description += f'"text": "{ui_element.text}", '
    if ui_element.content_description:
        element_description += (
            f'"content_description": "{ui_element.content_description}", '
        )
    if ui_element.hint_text:
        element_description += f'"hint_text": "{ui_element.hint_text}", '
    if ui_element.tooltip:
        element_description += f'"tooltip": "{ui_element.tooltip}", '
    element_description += (
        f'"clickable": {"True" if ui_element.is_clickable else "False"}, '
    )
    element_description += (
        f'"long_clickable": {"True" if ui_element.is_long_clickable else "False"}, '
    )
    element_description += (
        f'"editable": {"True" if ui_element.is_editable else "False"}, '
    )
    if ui_element.is_scrollable:
        element_description += '"scrollable": True, '
    if ui_element.is_focusable:
        element_description += '"focusable": True, '
    element_description += (
        f'"selected": {"True" if ui_element.is_selected else "False"}, '
    )
    element_description += (
        f'"checked": {"True" if ui_element.is_checked else "False"}, '
    )
    return element_description[:-2] + "}"


def mark_image(
    image: Image.Image,
    bbox: BoundingBox,
    index: int | None = None,
) -> Image.Image:
    draw = ImageDraw.Draw(image)
    draw.rectangle(
        (
            bbox.x_min,
            bbox.y_min,
            bbox.x_max,
            bbox.y_max,
        ),
        outline="red",
        width=2,
    )
    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
    if index is not None:
        draw.text((bbox.x_min, bbox.y_min), str(index), fill="white", font=font)
    return image


@dataclass
class JSONAction:
    """Represents a parsed JSON action.

    # Example
    result_json = {'action_type': 'click', 'x': %d, 'y': %d}
    action = JSONAction(**result_json)

    Attributes:
      action_type: The action type.
      index: The index to click, if action is a click. Either an index or a <x, y>
        should be provided. See x, y attributes below.
      x: The x position to click, if the action is a click.
      y: The y position to click, if the action is a click.
      text: The text to type, if action is type.
      direction: The direction to scroll, if action is scroll.
      goal_status: If the status is a 'status' type, indicates the status of the
        goal.
      app_name: The app name to launch, if the action type is 'open_app'.
      keycode: Keycode actions are necessary for an agent to interact with complex
        UI elements (like large textareas) that can't be accessed or controlled by
        simply taping, ensuring precise control over navigation and selection in
        the interface.
    """

    action_type: Optional[str] = None
    index: Optional[str | int] = None
    x: Optional[int] = None
    y: Optional[int] = None
    text: Optional[str] = None
    direction: Optional[str] = None
    goal_status: Optional[str] = None
    app_name: Optional[str] = None
    keycode: Optional[str] = None

    # for aria-UI
    target: Optional[str] = None
    instruction: Optional[str] = None
    coords: Optional[tuple[int, int]] = None
    # for aria and UGround
    element: Optional[str] = None

    def __post_init__(self):
        if self.action_type not in _ACTION_TYPES:
            raise ValueError(f"Invalid action type: {self.action_type}")
        if self.index is not None:
            self.index = int(self.index)
            if self.x is not None or self.y is not None:
                raise ValueError("Either an index or a <x, y> should be provided.")
        if self.element is not None:
            self.element = str(self.element)
            if self.x is not None or self.y is not None:
                raise ValueError("Either an index or a <x, y> should be provided.")
        if self.direction and self.direction not in _SCROLL_DIRECTIONS:
            raise ValueError(f"Invalid scroll direction: {self.direction}")
        if self.text is not None and not isinstance(self.text, str):
            self.text = str(self.text)
        if self.keycode is not None and not self.keycode.startswith("KEYCODE_"):
            raise ValueError(f"Invalid keycode: {self.keycode}")

    def __repr__(self) -> str:
        properties = []
        for key, value in self.__dict__.items():
            if value is not None:
                if isinstance(value, float):
                    value = f"{value:.3f}"
                properties.append(f"{key}={value!r}")
        return f"JSONAction({', '.join(properties)})"

    def __eq__(self, other):
        if isinstance(other, JSONAction):
            return _compare_actions(self, other)
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def json_str(self) -> str:
        non_null = {}
        for key, value in self.__dict__.items():
            if value is not None:
                non_null[key] = value
        return json.dumps(non_null, separators=_JSON_SEPARATORS)


def _compare_actions(a: JSONAction, b: JSONAction) -> bool:
    """Compares two JSONActions.

    Args:
      a: The first action.
      b: The second action.

    Returns:
      If the actions are equal.
    """
    # Ignore cases.
    if a.app_name is not None and b.app_name is not None:
        app_name_match = a.app_name.lower() == b.app_name.lower()
    else:
        app_name_match = a.app_name == b.app_name

    if a.text is not None and b.text is not None:
        text_match = a.text.lower() == b.text.lower()
    else:
        text_match = a.text == b.text

    # Compare the non-metadata fields.
    return (
        app_name_match
        and text_match
        and a.action_type == b.action_type
        and a.index == b.index
        and a.x == b.x
        and a.y == b.y
        and a.keycode == b.keycode
        and a.direction == b.direction
        and a.goal_status == b.goal_status
    )


def extract_json(s: str) -> dict[str, Any] | None:
    """Extracts JSON from string.

    Tries conversion with ast and json modules.

    Args:
      s: A string with a JSON in it. E.g., "{'hello': 'world'}" or from CoT:
        "let's think step-by-step, ..., {'hello': 'world'}".

    Returns:
      JSON object.
    """
    pattern = r"\{.*?\}"
    match = re.search(pattern, s)
    if match:
        try:
            return ast.literal_eval(match.group())
        except (SyntaxError, ValueError) as error:
            try:
                # Try conversion with json module.
                return json.loads(match.group())
            except (SyntaxError, ValueError) as error2:
                print(
                    "Cannot extract JSON, skipping due to errors %s and %s",
                    error,
                    error2,
                )
                return None
    else:
        return None
