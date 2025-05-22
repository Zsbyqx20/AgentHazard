import logging
from datetime import datetime
from pathlib import Path
from typing import Literal

import structlog

from .handlers import file_json_handler, rich_console_handler


def default_logging_setup(
    filename: str | None = None,
    filename_add_timestamp: bool = True,
    handlers: Literal["console", "file", "both"] = "both",
    target_module: str | None = None,
    target_module_level_console: int = logging.DEBUG,
    target_module_level_file: int = logging.DEBUG,
):
    hds = []

    if filename is None:
        if handlers in ["file", "both"]:
            raise ValueError("Filename is required for file logging.")
    else:
        if handlers in ["file", "both"]:
            path_filename = Path(filename)
            path_filename.parent.mkdir(parents=True, exist_ok=True)
            if filename_add_timestamp:
                filename = str(
                    path_filename.with_stem(
                        f"{path_filename.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    ).with_suffix(path_filename.suffix)
                )

            file_handler = file_json_handler(filename, mode="w")
            file_handler.setLevel(target_module_level_file)
            hds.append(file_handler)

    console_handler = rich_console_handler()
    console_handler.setLevel(target_module_level_console)

    if handlers in ["console", "both"]:
        hds.append(console_handler)

    logging.basicConfig(
        level=logging.WARNING,
        handlers=hds,
        format="%(message)s",
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    if target_module is not None:
        logging.getLogger(target_module).setLevel(logging.DEBUG)
