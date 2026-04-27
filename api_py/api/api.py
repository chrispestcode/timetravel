from typing import cast

from fastapi import APIRouter

from api.handlers_records import (
    make_get_records,
    make_get_latest_record_version,
    make_get_record_history,
    make_get_record_version,
    make_post_records,
)
from service.record_service import RecordService, RecordV2Protocol


class API:
    """Wires RecordService handlers onto a FastAPI router.

    Example:
        api = API(records=service)
        app.include_router(api.router, prefix="/api/v1")
    """

    def __init__(self, records: RecordService) -> None:
        self.records = records
        self.router = APIRouter()
        self._register_routes()

    def _register_routes(self) -> None:
        """Generates all API routes."""
        v2 = cast(RecordV2Protocol, self.records)
        self.router.add_api_route("/records/v2/latest", make_get_latest_record_version(v2), methods=["GET"])
        self.router.add_api_route("/records/v2/history", make_get_record_history(v2), methods=["GET"])
        self.router.add_api_route("/records/v2/version/{version_id}", make_get_record_version(v2), methods=["GET"])
        self.router.add_api_route("/records/{id}", make_get_records(self.records), methods=["GET"])
        self.router.add_api_route("/records/{id}", make_post_records(self.records), methods=["POST"])
