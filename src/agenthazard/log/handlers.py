import logging

import structlog
from rich.logging import RichHandler

from .processors import file_json_timezone_processor, rich_console_processor


def rich_console_handler(level: int = logging.DEBUG):
    console_handler = RichHandler(markup=True, rich_tracebacks=True)
    console_formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            rich_console_processor,
            structlog.dev.ConsoleRenderer(
                colors=False, exception_formatter=structlog.dev.plain_traceback
            ),
        ]
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(level)
    return console_handler


def file_json_handler(filename: str, mode: str = "w", level: int = logging.DEBUG):
    file_handler = logging.FileHandler(filename, mode=mode)
    file_formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.CallsiteParameterAdder([
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]),
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            file_json_timezone_processor,
            structlog.processors.JSONRenderer(ensure_ascii=False),
        ]
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(level)
    return file_handler
