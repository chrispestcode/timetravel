from fastapi import APIRouter

from api.handlers_records import make_get_records, make_post_records
from service.record import RecordService


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
        self.router.add_api_route("/records/{id}", make_get_records(self.records), methods=["GET"])
        self.router.add_api_route("/records/{id}", make_post_records(self.records), methods=["POST"])

# update routes
