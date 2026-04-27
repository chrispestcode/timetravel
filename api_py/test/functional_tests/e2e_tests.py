import pytest_asyncio
from typing import AsyncGenerator
from http import HTTPStatus

import httpx
from fastapi import FastAPI

from entity.record import Record
from entity.record_v2 import RecordV2
from service.sqlite_record_service import SQLiteRecordService
from api.api import API


class TestE2E:

    @pytest_asyncio.fixture
    async def client(self) -> AsyncGenerator[httpx.AsyncClient, None]:
        record_service = SQLiteRecordService(":memory:")

        await record_service.create_record(Record(id=1, data={"company_name": "Acme Corp"}))

        await record_service.create_record_v2(RecordV2(
            record_id=10, company_id=5,
            policy_start_date="2020-01-01", policy_end_date="2021-12-31",
            policy_status="CANCELLED", policy_tier="BRONZE", policy_domain="retail",
        ))
        await record_service.create_record_v2(RecordV2(
            record_id=10, company_id=5,
            policy_start_date="2022-01-01", policy_end_date="2026-12-31",
            policy_status="ACTIVE", policy_tier="SILVER", policy_domain="retail",
        ))

        app = FastAPI()
        api = API(records=record_service)
        app.include_router(api.router, prefix="/api/v2")

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as c:
            yield c

        if record_service._db is not None:
            await record_service._db.close()

    async def test_get_v1_record(self, client: httpx.AsyncClient) -> None:
        response = await client.get("/api/v2/records/1")
        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert body["id"] == 1
        assert body["data"]["company_name"] == "Acme Corp"

    async def test_create_v1_record(self, client: httpx.AsyncClient) -> None:
        response = await client.post("/api/v2/records/99", json={"company_name": "New Corp"})
        assert response.status_code == HTTPStatus.OK
        get_response = await client.get("/api/v2/records/99")
        assert get_response.json()["data"]["company_name"] == "New Corp"

    async def test_update_v1_record(self, client: httpx.AsyncClient) -> None:
        await client.post("/api/v2/records/1", json={"company_name": "Acme Updated"})
        response = await client.get("/api/v2/records/1")
        assert response.json()["data"]["company_name"] == "Acme Updated"

    async def test_get_latest_record_version(self, client: httpx.AsyncClient) -> None:
        response = await client.get("/api/v2/records/v2/latest?record_id=10")
        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert body["record_id"] == 10
        assert body["policy_status"] == "ACTIVE"

    async def test_get_record_history(self, client: httpx.AsyncClient) -> None:
        response = await client.get("/api/v2/records/v2/history?record_id=10")
        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert len(body) == 2
        assert body[0]["policy_status"] == "CANCELLED"
        assert body[1]["policy_status"] == "ACTIVE"

    async def test_get_specific_version(self, client: httpx.AsyncClient) -> None:
        # version_id=1 is the autoincrement id of the first inserted v2 record (CANCELLED)
        response = await client.get("/api/v2/records/v2/version/1?record_id=10")
        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert body["record_id"] == 10
        assert body["policy_status"] == "CANCELLED"
