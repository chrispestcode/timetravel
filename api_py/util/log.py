from loguru import logger


def log_error(err: Exception | None) -> None:
    """Logs err if it is not None."""
    if err is not None:
        logger.error(str(err))
