import pytest
import pytest_asyncio
from typing import AsyncGenerator

from entity.record import Record
from entity.record_v2 import RecordV2, RecordV2Field
from service.sqlite_record_service import SQLiteRecordService
from service.queries import RECORDS_V1_TABLE, RECORDS_V2_TABLE, GET_TABLES, queries


class TestDatabase:
    @pytest_asyncio.fixture
    async def service(self) -> AsyncGenerator[SQLiteRecordService, None]:
        svc = SQLiteRecordService(":memory:")
        yield svc
        if svc._db is not None:
            await svc._db.close()

    @pytest_asyncio.fixture
    async def service_with_records(self) -> AsyncGenerator[SQLiteRecordService, None]:
        svc = SQLiteRecordService(":memory:")
        for record in self.records:
            await svc.create_record(record)
        yield svc
        if svc._db is not None:
            await svc._db.close()

    @pytest_asyncio.fixture
    async def service_with_v2_records(self) -> AsyncGenerator[SQLiteRecordService, None]:
        svc = SQLiteRecordService(":memory:")
        for record in self.records_v2:
            await svc.create_record_v2(record)
        yield svc
        if svc._db is not None:
            await svc._db.close()

    @pytest_asyncio.fixture
    async def service_with_history(self) -> AsyncGenerator[SQLiteRecordService, None]:
        svc = SQLiteRecordService(":memory:")
        for record in self.history_records_v2:
            await svc.create_record_v2(record)
        yield svc
        if svc._db is not None:
            await svc._db.close()

    records: list[Record] = [
        Record(id=1, data={"company_name": "Company X"}),
        Record(id=2, data={"company_name": "Company Y"}),
        Record(id=3, data={"company_name": "Company Z"}),
        Record(id=100, data={"company_name": "Company Alpha"}),
        Record(id=200, data={"company_name": "Company Beta"}),
        Record(id=300, data={"company_name": "Company Charlie"}),
    ]

    # Three versions of record_id=50: two closed periods then one still-active.
    # Inserted out of chronological order to verify the query sorts by policy_end_date.
    history_records_v2: list[RecordV2] = [
        RecordV2(
            record_id=50, company_id=5,
            policy_start_date="01-01-2022", policy_end_date="12-31-2022",
            policy_status="CANCELLED", policy_tier="SILVER", policy_domain="retail",
        ),
        RecordV2(
            record_id=50, company_id=5,
            policy_start_date="01-01-2020", policy_end_date="12-31-2020",
            policy_status="CANCELLED", policy_tier="BRONZE", policy_domain="retail",
        ),
        RecordV2(
            record_id=50, company_id=5,
            policy_start_date="01-01-2023", policy_end_date="12-31-2026",
            policy_status="ACTIVE", policy_tier="GOLD", policy_domain="retail",
        ),
    ]

    records_v2: list[RecordV2] = [
        RecordV2(
            record_id=10, company_id=1,
            policy_start_date="01-01-2020", policy_end_date="07-31-2026",
            policy_status="ACTIVE", policy_tier="BRONZE", policy_domain="shops",
            created_at="2020-01-01T00:00:00", last_updated="2020-01-01T00:00:00",
        ),
        RecordV2(
            record_id=14, company_id=1,
            policy_start_date="01-01-2020", policy_end_date="07-31-2026",
            policy_status="ACTIVE", policy_tier="BRONZE", policy_domain="shops",
            created_at="2020-01-01T00:00:00", last_updated="2020-01-01T00:00:00",
        ),
        RecordV2(
            record_id=19, company_id=1,
            policy_start_date="01-01-2020", policy_end_date="07-31-2026",
            policy_status="ACTIVE", policy_tier="BRONZE", policy_domain="shops",
            created_at="2020-01-01T00:00:00", last_updated="2020-01-01T00:00:00",
        ),
        RecordV2(
            record_id=23, company_id=1,
            policy_start_date="01-01-2020", policy_end_date="07-31-2026",
            policy_status="ACTIVE", policy_tier="BRONZE", policy_domain="shops",
            created_at="2020-01-01T00:00:00", last_updated="2020-01-01T00:00:00",
        ),
    ]

    # --- schema tests (SQL-level, no service logic to test) ---

    @pytest.mark.timeout(2)
    async def test_get_database(self, service) -> None:
        '''Both v1 and v2 tables are created on first connection.'''
        conn = await service._get_db()
        async with conn.execute(queries["v1"][GET_TABLES]) as cursor:
            rows = await cursor.fetchall()
        assert any(row[0] == RECORDS_V1_TABLE for row in rows)
        assert any(row[0] == RECORDS_V2_TABLE for row in rows)

    async def test_create_table_v2(self, service) -> None:
        '''The v2 table schema matches the RecordV2 model fields exactly.'''
        conn = await service._get_db()
        async with conn.execute(f"PRAGMA table_info({RECORDS_V2_TABLE})") as cursor:
            rows = await cursor.fetchall()
        actual_columns = {row[1] for row in rows}
        expected_columns = set(RecordV2.model_fields.keys())
        assert actual_columns == expected_columns

    # --- v1 service tests ---

    async def test_insert_record(self, service) -> None:
        '''A v1 record can be created and immediately retrieved.'''
        record = self.records[0]
        await service.create_record(record)
        result = await service.get_record(record.id)
        assert result is not None
        assert result.id == record.id
        assert result.data == record.data

    async def test_get_record(self, service_with_records) -> None:
        '''A v1 record is retrievable by id after bulk insert.'''
        target = self.records[-1]
        result = await service_with_records.get_record(target.id)
        assert result is not None
        assert result.data == target.data

    async def test_get_record_not_found(self, service) -> None:
        '''get_record returns None for an id that does not exist.'''
        result = await service.get_record(9999)
        assert result is None

    async def test_update_record(self, service_with_records) -> None:
        '''update_record patches data and returns the updated record.'''
        target = self.records[0]
        updates = {"company_name": "Updated Company"}
        result = await service_with_records.update_record(target.id, updates)
        assert result.data["company_name"] == "Updated Company"
        persisted = await service_with_records.get_record(target.id)
        assert persisted is not None
        assert persisted.data["company_name"] == "Updated Company"

    # --- v2 service tests ---

    async def test_insert_record_v2(self, service) -> None:
        '''A v2 record can be created and immediately retrieved.'''
        record = self.records_v2[0]
        await service.create_record_v2(record)
        result = await service.get_record_v2(record.record_id)
        assert result is not None
        assert result.record_id == record.record_id
        assert result.policy_status == record.policy_status

    async def test_get_record_v2(self, service_with_v2_records) -> None:
        '''A v2 record is retrievable by record_id after bulk insert.'''
        result = await service_with_v2_records.get_record_v2(19)
        assert result is not None
        assert result.record_id == 19

    async def test_get_record_v2_not_found(self, service) -> None:
        '''get_record_v2 returns None for a record_id that does not exist.'''
        result = await service.get_record_v2(9999)
        assert result is None

    async def test_update_record_v2(self, service_with_v2_records) -> None:
        '''update_record_v2 patches a single field and returns the updated record.'''
        result = await service_with_v2_records.update_record_v2(
            record_id=19,
            fields={RecordV2Field.POLICY_START_DATE},
            data={RecordV2Field.POLICY_START_DATE: "2021-03-01"},
        )
        assert result.policy_start_date.isoformat() == "2021-03-01"

    async def test_get_latest_record_version(self, service) -> None:
        '''get_latest_record_version returns only the ACTIVE record when multiple exist.'''
        cancelled = RecordV2(
            record_id=10, company_id=1,
            policy_start_date="01-01-2019", policy_end_date="12-31-2019",
            policy_status="CANCELLED", policy_tier="BRONZE", policy_domain="shops",
        )
        active = RecordV2(
            record_id=10, company_id=1,
            policy_start_date="01-01-2020", policy_end_date="07-31-2026",
            policy_status="ACTIVE", policy_tier="BRONZE", policy_domain="shops",
        )
        await service.create_record_v2(cancelled)
        await service.create_record_v2(active)

        result = await service.get_latest_record_version(10)
        assert result is not None
        assert result.policy_status == "ACTIVE"


    async def test_get_record_history(self, service_with_history) -> None:
        '''get_record_history returns all versions ordered by policy_end_date ascending.'''
        results = await service_with_history.get_record_history(50)
        assert len(results) == 3
        end_dates = [r.policy_end_date for r in results]
        assert end_dates == sorted(end_dates)
        assert results[-1].policy_status == "ACTIVE"
