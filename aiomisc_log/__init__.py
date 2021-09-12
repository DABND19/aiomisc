import logging
import logging.handlers
import os
import sys
import typing as t

from .enum import LogFormat, LogLevel
from .formatter import color_formatter, json_handler


LOG_LEVEL: t.Optional[t.Any] = None
LOG_FORMAT: t.Optional[t.Any] = None

try:
    import contextvars
    LOG_LEVEL = contextvars.ContextVar("LOG_LEVEL", default=logging.INFO)
    LOG_FORMAT = contextvars.ContextVar("LOG_FORMAT", default=LogFormat.color)
except ImportError:
    pass


DEFAULT_FORMAT = "%(levelname)s:%(name)s:%(message)s"


def create_logging_handler(
    log_format: LogFormat = LogFormat.color,
    date_format: str = None, **kwargs: t.Any
) -> logging.Handler:

    if LOG_FORMAT is not None:
        LOG_FORMAT.set(log_format)

    handler: logging.Handler

    if log_format == LogFormat.stream:
        handler = logging.StreamHandler()
        if date_format and date_format is not Ellipsis:
            formatter = logging.Formatter(
                "%(asctime)s " + DEFAULT_FORMAT, datefmt=date_format,
            )
        else:
            formatter = logging.Formatter(DEFAULT_FORMAT)

        handler.setFormatter(formatter)
        return handler
    elif log_format == LogFormat.json:
        return json_handler(date_format=date_format, **kwargs)
    elif log_format == LogFormat.color:
        return color_formatter(date_format=date_format, **kwargs)
    elif log_format == LogFormat.syslog:
        if date_format:
            sys.stderr.write("Can not apply \"date_format\" for syslog\n")
            sys.stderr.flush()

        formatter = logging.Formatter("%(message)s")

        if os.path.exists("/dev/log"):
            handler = logging.handlers.SysLogHandler(address="/dev/log")
        else:
            handler = logging.handlers.SysLogHandler()

        handler.setFormatter(formatter)
        return handler
    elif log_format == LogFormat.plain:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        return handler

    raise NotImplementedError


HandlerWrapperType = t.Callable[[logging.Handler], logging.Handler]


def pass_wrapper(handler: logging.Handler) -> logging.Handler:
    return handler


def basic_config(
    level: t.Union[int, str] = logging.INFO,
    log_format: t.Union[str, LogFormat] = LogFormat.color,
    handler_wrapper: HandlerWrapperType = pass_wrapper,
    **kwargs: t.Any
) -> None:

    if isinstance(level, str):
        level = LogLevel[level]

    logging.basicConfig()
    logger = logging.getLogger()
    logger.handlers.clear()

    if isinstance(log_format, str):
        log_format = LogFormat[log_format]

    handler = handler_wrapper(create_logging_handler(log_format, **kwargs))

    if LOG_LEVEL is not None:
        LOG_LEVEL.set(level)

    # noinspection PyArgumentList
    logging.basicConfig(
        level=int(level),
        handlers=[handler],
    )


__all__ = (
    "LogFormat",
    "LogLevel",
    "basic_config",
)
