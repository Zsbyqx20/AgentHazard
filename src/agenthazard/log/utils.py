from datetime import datetime
from zoneinfo import ZoneInfo

import structlog


def file_json_timezone_processor(_, __, event_dict: structlog.typing.EventDict):
    localized_time = datetime.now(ZoneInfo("Asia/Shanghai")).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    event_dict["timestamp"] = localized_time
    return event_dict
