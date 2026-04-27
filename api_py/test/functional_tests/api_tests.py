import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import AsyncGenerator
from http import HTTPStatus

import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from entity.record import Record
from entity.record_v2 import RecordV2
from service.record_service import RecordService
from api.api import API


class TestAPI:
    record = Record(id=1, data={"company_name": "Test Inc", "company_id": "1"})
    record_v2 = RecordV2(
        record_id=10, company_id=1,
        policy_start_date="2020-01-01", policy_end_date="2026-07-31",
        policy_status="ACTIVE", policy_tier="BRONZE", policy_domain="shops",
    )

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
        app.include_router(api.router, prefix="/api/v2")

        @app.get("/api/v1/health")
        async def health() -> JSONResponse:
            return JSONResponse(content={"ok": True})

        @app.get("/api/v2/health")
        async def health() -> JSONResponse:
            return JSONResponse(content={"ok": True})
        
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as c:
            yield c
    
    @pytest.fixture
    def api_version(self, request: pytest.FixtureRequest) -> str:
        return f'/api/v{request.param}'

    async def test_get_record_at_base_url(self, client: httpx.AsyncClient) -> None:
        response = await client.get("/")
        assert response.status_code == HTTPStatus.NOT_FOUND

    @pytest.mark.parametrize("api_version", [1,2], indirect=True)
    async def test_server_health_check(self, client: httpx.AsyncClient, api_version) -> None:
        response = await client.get(f"{api_version}/health")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"ok": True}

    @pytest.mark.parametrize("api_version", [1,2], indirect=True)
    async def test_get_record(self, client: httpx.AsyncClient, mock_service: RecordService, api_version: str) -> None:
        response = await client.get(f"{api_version}/records/1")
        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert body["id"] == self.record.id
        assert body["data"] == self.record.data
        mock_service.get_record.assert_called_once_with(1)
    
    @pytest.mark.parametrize("api_version", [1,2], indirect=True)
    async def test_get_record_not_found(self, client: httpx.AsyncClient, mock_service: RecordService, api_version: str) -> None:
        mock_service.get_record = AsyncMock(return_value=None)
        response = await client.get(f"{api_version}/records/999")
        assert response.status_code == HTTPStatus.OK
        mock_service.get_record.assert_called_once_with(999)
        assert response.json() == {}

    @pytest.mark.parametrize("api_version", [1,2], indirect=True)
    async def test_create_record(self, client: httpx.AsyncClient, mock_service: RecordService, api_version: str) -> None:
        mock_service.get_record = AsyncMock(return_value=None)
        data = {"company_name": "Test Inc", "company_id": "2"}
        response = await client.post(f"{api_version}/records/2", json=data)
        assert response.status_code == HTTPStatus.OK
        mock_service.create_record.assert_called_once()

    @pytest.mark.parametrize("api_version", [1,2], indirect=True)
    async def test_update_record(self, client: httpx.AsyncClient, mock_service: RecordService, api_version: str) -> None:
        updates = {"company_name": "Updated Inc"}
        response = await client.post(f"{api_version}/records/1", json=updates)
        assert response.status_code == HTTPStatus.OK
        assert response.json()["id"] == self.record.id
        mock_service.update_record.assert_called_once_with(1, updates)

    @pytest.mark.parametrize("api_version", [2], indirect=True)
    async def test_get_latest_record_version(
        self, client: httpx.AsyncClient, mock_service: RecordService, api_version: str
    ) -> None:
        mock_service.get_latest_record_version = AsyncMock(return_value=self.record_v2)
        response = await client.get(f"{api_version}/records/v2/latest?record_id=10")
        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert body["record_id"] == self.record_v2.record_id
        assert body["policy_status"] == self.record_v2.policy_status
        mock_service.get_latest_record_version.assert_called_once_with(10)

    @pytest.mark.parametrize("api_version", [2], indirect=True)
    async def test_get_historical_view_of_record(
        self, client: httpx.AsyncClient, mock_service: RecordService, api_version: str
    ) -> None:
        history = [
            self.record_v2,
            RecordV2(
                record_id=10, company_id=1,
                policy_start_date="2018-01-01", policy_end_date="2019-12-31",
                policy_status="CANCELLED", policy_tier="BRONZE", policy_domain="shops",
            ),
        ]
        mock_service.get_record_history = AsyncMock(return_value=history)
        response = await client.get(f"{api_version}/records/v2/history?record_id=10")
        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert len(body) == 2
        assert all(item["record_id"] == 10 for item in body)
        mock_service.get_record_history.assert_called_once_with(10)

    @pytest.mark.parametrize("api_version", [2], indirect=True)
    async def test_get_specific_version_of_record(
        self, client: httpx.AsyncClient, mock_service: RecordService, api_version: str
    ) -> None:
        mock_service.get_record_version = AsyncMock(return_value=self.record_v2)
        response = await client.get(f"{api_version}/records/v2/version/3?record_id=10")
        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert body["record_id"] == self.record_v2.record_id
        mock_service.get_record_version.assert_called_once_with(10, 3)

    @pytest.mark.skip(reason="endpoint not implemented yet")
    @pytest.mark.parametrize("api_version", [2], indirect=True)
    async def test_reconcile_record_history(self, client: httpx.AsyncClient, api_version: str) -> None:
        pass

    @pytest.mark.skip(reason="endpoint not implemented yet")
    async def test_get_v1_record_via_v2_api(self) -> None:
        pass

