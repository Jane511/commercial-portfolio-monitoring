"""Logging configuration for the portfolio-monitor pipeline.

Usage in any src/ module::

    from .logger import get_logger
    _log = get_logger(__name__)

    _log.info("Step started")
    _log.warning("Edge case: %s", detail)
    _log.error("Critical failure: %s", reason)

Log output goes to both the console (INFO+) and a timestamped file in
``logs/pipeline_YYYYMMDD_HHMMSS.log`` (DEBUG+).
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_LOGS_DIR = _ROOT / "logs"

_LOG_FORMAT = "[%(asctime)s] [%(levelname)-8s] [%(module)s] %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_PROJECT_LOGGER_NAME = "portfolio_monitor"


def _initialise_handlers() -> None:
    """Attach console and file handlers to the project root logger (once only)."""
    _LOGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = _LOGS_DIR / f"pipeline_{timestamp}.log"

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    root = logging.getLogger(_PROJECT_LOGGER_NAME)
    root.setLevel(logging.DEBUG)
    root.addHandler(console)
    root.addHandler(file_handler)
    # Prevent messages from propagating to the root Python logger.
    root.propagate = False


# Initialise exactly once when this module is first imported.
_project_root = logging.getLogger(_PROJECT_LOGGER_NAME)
if not _project_root.handlers:
    _initialise_handlers()


def get_logger(name: str) -> logging.Logger:
    """Return a named child logger under the portfolio_monitor namespace.

    Parameters
    ----------
    name:
        Typically ``__name__`` of the calling module, e.g. ``src.staging``.
        The logger is created as a child of ``portfolio_monitor`` so it
        inherits all configured handlers automatically.
    """
    # Strip the leading package path so log output shows e.g. "src.staging"
    # rather than "portfolio_monitor.src.staging".
    child_name = f"{_PROJECT_LOGGER_NAME}.{name}"
    return logging.getLogger(child_name)
