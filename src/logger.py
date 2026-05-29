
# THis file will serve as the central logging configuration for the project. The setup_logging() function configures a logger with both console and file handlers, while get_logger() provides a convenient way for other modules to obtain a logger instance that is a child of the main project logger. This design ensures consistent logging across the entire codebase while keeping third-party library logs separate and manageable.
import logging
import logging.handlers
from pathlib import Path


_PROJECT   = "space_missions"
_LOG_DIR   = Path("logs")
_LOG_FILE  = _LOG_DIR / "space_missions.log"


_FMT_CONSOLE = "%(asctime)s  %(levelname)-8s  %(message)s"
_FMT_FILE    = (
    "%(asctime)s  %(levelname)-8s  "
    "%(name)s  %(filename)s:%(lineno)d  %(message)s"
)
_DATEFMT_CONSOLE = "%H:%M:%S"
_DATEFMT_FILE    = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    console_level: int = logging.INFO,
    file_level:    int = logging.DEBUG,
    silence_libs:  bool = True,
) -> logging.Logger:
    """


    Example
    -------
    # At the top of etl_load.py or a notebook's first cell:
        from src.logger import setup_logging, get_logger
        setup_logging()
        log = get_logger(__name__)
        log.info("ETL started")
    """
    logger = logging.getLogger(_PROJECT)

    # Guard: if handlers already exist this function was already called
    if logger.handlers:
        return logger

  
    logger.setLevel(logging.DEBUG)

    # ── Console handler ──────────────────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(
        logging.Formatter(_FMT_CONSOLE, datefmt=_DATEFMT_CONSOLE)
    )

  
    # Rotates at 5 MB, keeps 3 backup files:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        filename    = _LOG_FILE,
        maxBytes    = 5 * 1024 * 1024,   # 5 MB
        backupCount = 3,
        encoding    = "utf-8",
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(
        logging.Formatter(_FMT_FILE, datefmt=_DATEFMT_FILE)
    )

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # ── Silence noisy third-party loggers ────────────────────────────────────
    if silence_libs:
        for lib in ("sqlalchemy", "psycopg2", "urllib3", "matplotlib", "PIL"):
            logging.getLogger(lib).setLevel(logging.WARNING)

    # ── Do NOT propagate to the root logger ──────────────────────────────────

    logger.propagate = False

    logger.info(f"Logging initialised — file: {_LOG_FILE.resolve()}")
    return logger

#Return a child logger scoped to a specific module,Always returns a child of the project logger — never the root logger.
    
def get_logger(module_name: str) -> logging.Logger:
    
    clean_name = module_name.replace("src.", "")
    return logging.getLogger(f"{_PROJECT}.{clean_name}")
