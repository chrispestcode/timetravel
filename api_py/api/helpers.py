from http import HTTPStatus

from fastapi.responses import JSONResponse
from loguru import logger

from service.record_service import ServiceError, ServiceErrorCode
from util.log import log_error

_SERVICE_ERROR_MAP: dict[ServiceErrorCode, HTTPStatus] = {
    ServiceErrorCode.NOT_FOUND: HTTPStatus.NOT_FOUND,
    ServiceErrorCode.ALREADY_EXISTS: HTTPStatus.CONFLICT,
    ServiceErrorCode.INVALID_ID: HTTPStatus.BAD_REQUEST,
}

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
        http_status = _SERVICE_ERROR_MAP.get(err.code, HTTPStatus.INTERNAL_SERVER_ERROR)
        return write_error(err.message, http_status)
    log_error(err)
    return write_error(str(ErrInternal), HTTPStatus.INTERNAL_SERVER_ERROR)
