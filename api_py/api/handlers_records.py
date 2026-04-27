from collections.abc import Callable
from http import HTTPStatus

from fastapi import Query, Request
from fastapi.responses import JSONResponse

from api.helpers import write_error, write_service_error
from entity.record import Record
from service.record_service import RecordService, RecordV2Protocol


def make_get_records(records: RecordService) -> Callable:
    """Returns a GET /records/{id} handler bound to the given service."""

    async def get_records(id: int) -> JSONResponse:
        try:
            record = await records.get_record(id)
        except Exception as err:
            return write_service_error(err)

        if record is None:
            return JSONResponse(content={}, status_code=HTTPStatus.OK)

        return JSONResponse(content=record.model_dump(), status_code=HTTPStatus.OK)

    return get_records


def make_post_records(records: RecordService) -> Callable:
    """Returns a POST /records/{id} handler bound to the given service.

    Creates the record if it does not exist; updates it if it does.
    """

    async def post_records(id: int, request: Request) -> JSONResponse:
        try:
            body: dict[str, str | None] = await request.json()
        except Exception:
            return write_error("invalid input; could not parse json", HTTPStatus.BAD_REQUEST)

        existing: Record | None = None
        try:
            existing = await records.get_record(id)
        except Exception as err:
            return write_service_error(err)

        if existing is None:
            record_map = {k: v for k, v in body.items() if v is not None}
            record = Record(id=id, data=record_map)
            try:
                await records.create_record(record)
            except Exception as err:
                return write_service_error(err)
        else:
            try:
                record = await records.update_record(id, body)
            except Exception as err:
                return write_service_error(err)

        return JSONResponse(content=record.model_dump(), status_code=HTTPStatus.OK)

    return post_records


def make_get_latest_record_version(records: RecordV2Protocol) -> Callable:
    """Returns a GET /records/v2/latest?record_id={id} handler bound to the given service."""
    ''' Query objects are inferred as Query Parameters by FastAPI '''
    
    async def get_latest_record_version(record_id: int = Query(..., description="record_id to look up")) -> JSONResponse:
        try:
            record = await records.get_latest_record_version(record_id)
        except Exception as err:
            return write_service_error(err)

        if record is None:
            return JSONResponse(content={}, status_code=HTTPStatus.OK)

        return JSONResponse(content=record.model_dump(mode="json"), status_code=HTTPStatus.OK)

    return get_latest_record_version


def make_get_record_history(records: RecordV2Protocol) -> Callable:
    """Returns a GET /records/v2/history?record_id={id} handler bound to the given service."""
    ''' Query objects are inferred as Query Parameters by FastAPI '''

    async def get_record_history(record_id: int = Query(..., description="record_id to look up")) -> JSONResponse:
        try:
            results = await records.get_record_history(record_id)
        except Exception as err:
            return write_service_error(err)

        return JSONResponse(
            content=[r.model_dump(mode="json") for r in results],
            status_code=HTTPStatus.OK,
        )

    return get_record_history


def make_get_record_version(records: RecordV2Protocol) -> Callable:
    """Returns a GET /records/v2/version/{version_id}?record_id={id} handler."""
    ''' Query objects are inferred as Query Parameters by FastAPI '''
    
    async def get_record_version(version_id: int, record_id: int = Query(..., description="record_id to look up")) -> JSONResponse:
        try:
            record = await records.get_record_version(record_id, version_id)
        except Exception as err:
            return write_service_error(err)

        if record is None:
            return JSONResponse(content={}, status_code=HTTPStatus.OK)

        return JSONResponse(content=record.model_dump(mode="json"), status_code=HTTPStatus.OK)

    return get_record_version
