import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import AsyncGenerator
from http import HTTPStatus

import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from entity.record import Record
from service.record_service import RecordService, ServiceError
from api.api import API


class TestAPI:
    record = Record(id=1, data={"company_name": "Test Inc", "company_id": "1"})

    @pytest.fixture
    def mock_service(self) -> RecordService:
        service = MagicMock(spec=RecordService)
        service.get_record = AsyncMock(return_value=self.record)
        service.create_record = AsyncMock(return_value=None)
        service.update_record = AsyncMock(return_value=self.record)
        return service

    @pytest_asyncio.fixture(scope="function")
    async def client(self, mock_service: RecordService) -> AsyncGenerator[httpx.AsyncClient, None]:
        app = FastAPI()
        api = API(records=mock_service)
        app.include_router(api.router, prefix="/api/v1")

        @app.get("/api/v1/health")
        async def health() -> JSONResponse:
            return JSONResponse(content={"ok": True})

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as c:
            yield c

    async def test_get_record_at_base_url(self, client: httpx.AsyncClient) -> None:
        response = await client.get("/")
        assert response.status_code == HTTPStatus.NOT_FOUND

    async def test_server_health_check(self, client: httpx.AsyncClient) -> None:
        response = await client.get("/api/v1/health")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"ok": True}

    async def test_get_record(self, client: httpx.AsyncClient, mock_service: RecordService) -> None:
        response = await client.get("/api/v1/records/1")
        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert body["id"] == self.record.id
        assert body["data"] == self.record.data
        mock_service.get_record.assert_called_once_with(1)

    async def test_get_record_not_found(self, client: httpx.AsyncClient, mock_service: RecordService) -> None:
        mock_service.get_record.side_effect = ServiceError.not_found()
        response = await client.get("/api/v1/records/999")
        assert response.status_code == HTTPStatus.NOT_FOUND

    async def test_create_record(self, client: httpx.AsyncClient, mock_service: RecordService) -> None:
        data = {"company_name": "Test Inc", "company_id": "1"}
        response = await client.post("/api/v1/records", json=data)
        assert response.status_code == HTTPStatus.OK
        assert response.json()["id"] == 1
        mock_service.create_record.assert_called_with(1, data)

    async def test_update_record(self, client: httpx.AsyncClient, mock_service: RecordService) -> None:
        updates = {"company_name": "Updated Inc"}
        response = await client.post("/api/v1/records/1", json=updates)
        assert response.status_code == HTTPStatus.OK
        assert response.json()["id"] == self.record.id
        mock_service.update_record.assert_called_once_with(1, updates)

    async def test_get_latest_record_version(self, client: httpx.AsyncClient, mock_service: RecordService) -> None:
        response = await client.get("/api/v1/records/1/latest")
        assert response.status_code == HTTPStatus.OK
        assert response.json()["id"] == self.record.id
        mock_service.get_latest_record_version.assert_called_once()

    @pytest.mark.skip(reason="endpoint not implemented yet")
    async def test_get_historical_view_of_record(self) -> None:
        pass

    @pytest.mark.skip(reason="endpoint not implemented yet")
    async def test_get_specific_version_of_record(self) -> None:
        pass

    @pytest.mark.skip(reason="endpoint not implemented yet")
    async def test_reconcile_record_history(self) -> None:
        pass

    @pytest.mark.skip(reason="endpoint not implemented yet")
    async def test_get_v1_record_via_v2_api(self) -> None:
        pass

    @pytest.mark.skip(reason="endpoint not implemented yet")
    async def test_compare_diff_records(self) -> None:
        pass

    @pytest.mark.skip(reason="endpoint not implemented yet")
    async def test_migrate_v1_record_to_v2(self) -> None:
        pass

    @pytest.mark.skip(reason="endpoint not implemented yet")
    async def test_migrate_v2_record_to_v1(self) -> None:
        pass
