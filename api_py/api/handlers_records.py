from collections.abc import Callable
from http import HTTPStatus

from fastapi import Request
from fastapi.responses import JSONResponse

from api.helpers import log_error, write_error, write_service_error
from entity.record import Record
from service.record_service import RecordService, ServiceError


def make_get_records(records: RecordService) -> Callable:
    """Returns a GET /records/{id} handler bound to the given service."""

    async def get_records(id: int) -> JSONResponse:
        try:
            record = await records.get_record(id)
        except ServiceError as err:
            if err.code == HTTPStatus.NOT_FOUND:
                return write_error(f"record of id {id} does not exist", HTTPStatus.NOT_FOUND)
            return write_service_error(err)
        except Exception as err:
            return write_service_error(err)

        log_error(None)
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

        record: Record | None = None
        err: Exception | None = None

        try:
            existing = await records.get_record(id)
        except ServiceError as get_err:
            if get_err.code == HTTPStatus.NOT_FOUND:  # record does not exist, create it
                # exclude the delete updates
                record_map = {k: v for k, v in body.items() if v is not None}
                record = Record(id=id, data=record_map)
                try:
                    await records.create_record(record)
                except Exception as create_err:
                    err = create_err
            else:
                err = get_err
        except Exception as get_err:
            err = get_err
        else:  # record exists, update it
            try:
                record = await records.update_record(id, body)
            except Exception as update_err:
                err = update_err
            _ = existing  # consumed by update

        if err is not None:
            return write_service_error(err)

        return JSONResponse(content=record.model_dump() if record else {}, status_code=HTTPStatus.OK)

    return post_records

#TODO add all other endpoints, maybe consider adding a layer for record reconciliation