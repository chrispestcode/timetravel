from fastapi.responses import JSONResponse
from loguru import logger

from service.record_service import ServiceError
from util.log import log_error

ErrInternal = Exception("internal error")


def write_json(data: dict, status_code: int = 200) -> JSONResponse:
    """Serialises data as a JSON response."""
    return JSONResponse(content=data, status_code=status_code)


def write_error(message: str, status_code: int) -> JSONResponse:
    """Writes message as a JSON error response."""
    logger.error(f"response errored: {message}")
    return JSONResponse(content={"error": message}, status_code=status_code)


def write_service_error(err: Exception) -> JSONResponse:
    """Maps a ServiceError to its HTTP response; falls back to 500 for unknown errors."""
    if isinstance(err, ServiceError):
        return write_error(err.message, err.code)
    log_error(err)
    return write_error(str(ErrInternal), 500)
