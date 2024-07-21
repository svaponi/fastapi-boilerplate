import json
import logging
import os
import sys

from app.utils.getenv import getenv_bool

# TODO consider refactoring, see https://github.com/mCodingLLC/VideosSampleCode/tree/master/videos/135_modern_logging

_IS_LOGGING_INITIALIZED = False
# see https://docs.python.org/3/library/logging.html#logrecord-attributes
_LOG_FORMAT = (
    "%(asctime)s | %(levelname)-5.5s | %(threadName)s | %(name)s :: %(message)s"
)
_FORMATTER = logging.Formatter()


def _log_record_to_json(record: logging.LogRecord) -> dict:
    _message = record.getMessage()
    return {
        k: v
        for k, v in {
            "level": record.levelname,
            "name": record.name,
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
            "message": _message,
            "exc_info": (
                _FORMATTER.formatException(record.exc_info) if record.exc_info else None
            ),
            "stack_info": record.stack_info,
        }.items()
        if v
    }


def _build_handler():
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    return _handler


def _build_json_handler():
    class _JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            return json.dumps(_log_record_to_json(record))

    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(_JsonFormatter())
    return _handler


def _setup_logging():
    log_level = os.getenv(key="LOG_LEVEL", default="info").upper()
    log_as_json = getenv_bool(key="LOG_AS_JSON", default=True)

    # remove any predefined root logger handler
    for h in logging.root.handlers:
        logging.root.removeHandler(h)

    # re-configure root logger handler
    _handler = _build_json_handler() if log_as_json else _build_handler()
    logging.root.addHandler(_handler)

    # set root logger level
    logging.root.setLevel(log_level)

    # remove every other logger's handlers and propagate to root logger
    for name in logging.root.manager.loggerDict.keys():
        _logger = logging.getLogger(name)
        _logger.handlers = []
        _logger.propagate = True


def _override_log_levels():
    """
    Example
    ```
        LOG_LEVEL_UVICORN_ERROR=warn
        LOG_LEVEL_APP_CORE=debug
    ```
    Or, alternatively (same result):
    ```
        LOG_LEVELS=uvicorn.error=warn,app.core=debug
    ```
    """
    for k, v in os.environ.items():
        if k.startswith("LOG_LEVEL_"):
            _name = k.removeprefix("LOG_LEVEL_").replace("_", ".").lower()
            logging.getLogger(_name).setLevel(v.upper())

    for part in os.getenv("LOG_LEVELS", default="").split(","):
        if "=" in part:
            _name, _level = part.split("=", maxsplit=2)
            logging.getLogger(_name).setLevel(_level.upper())


def setup_logging() -> None:
    global _IS_LOGGING_INITIALIZED
    if not _IS_LOGGING_INITIALIZED:
        _setup_logging()
        _override_log_levels()
        _IS_LOGGING_INITIALIZED = True
