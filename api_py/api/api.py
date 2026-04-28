from typing import cast

from fastapi import APIRouter

from api.handlers_records import (
    make_get_records,
    make_get_records_v1,
    make_get_latest_record_version,
    make_get_record_history,
    make_get_record_version,
    make_post_records,
)
from service.record_service import RecordService, RecordV2Protocol


class API:
    """Wires RecordService handlers onto versioned FastAPI routers.

    Example:
        api = API(records=service)
        app.include_router(api.v1_router, prefix="/api/v1")
        app.include_router(api.v2_router, prefix="/api/v2")
    """

    def __init__(self, records: RecordService) -> None:
        self.records = records
        self.v1_router = APIRouter()
        self.v2_router = APIRouter()
        self._register_routes()

    def _register_routes(self) -> None:
        """Generates all API routes."""
        v2 = cast(RecordV2Protocol, self.records)
        # Static paths must be registered before /{id} to win route matching.
        self.v2_router.add_api_route("/records/latest", make_get_latest_record_version(v2), methods=["GET"])
        self.v2_router.add_api_route("/records/history", make_get_record_history(v2), methods=["GET"])
        self.v2_router.add_api_route("/records/version/{version_id}", make_get_record_version(v2), methods=["GET"])
        self.v2_router.add_api_route("/records/{id}", make_get_records(self.records), methods=["GET"])
        self.v2_router.add_api_route("/records/{id}", make_post_records(self.records), methods=["POST"])
        self.v1_router.add_api_route("/records/{id}", make_get_records_v1(self.records), methods=["GET"])
        self.v1_router.add_api_route("/records/{id}", make_post_records(self.records), methods=["POST"])
