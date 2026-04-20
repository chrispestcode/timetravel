import pytest
from entity.record import Record
import pytest_asyncio
from service.sqlite_record_service import SQLiteRecordService
from service.queries import *
from typing import AsyncGenerator, Any
import aiosqlite
import json

class TestDatabase:
    @pytest_asyncio.fixture
    async def db_conn(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        db = SQLiteRecordService(":memory:")
        yield db

    @pytest_asyncio.fixture
    async def db_with_records(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        db = SQLiteRecordService(":memory:")
        conn = await db._get_db()
        yield conn
        await conn.close()

    @pytest_asyncio.fixture
    async def db_with_records_saturated(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        db = SQLiteRecordService(":memory:")
        conn = await db._get_db()
        for record in self.records:
            cursor = await conn.execute(queries["v1"][INSERT_RECORD], (record.id, json.dumps(record.data)))
            await conn.commit()
        yield conn
        await conn.close()

    records: list[Record] = [
        Record(id=1,data={"company_name": "Company X"}),
        Record(id=2,data={"company_name": "Company Y"}),
        Record(id=3,data={"company_name": "Company Z"}),
        Record(id=100,data={"company_name": "Company Alpha"}),
        Record(id=200,data={"company_name": "Company Beta"}),
        Record(id=300, data={"company_name": "Company Charlie"}),
    ]

    @pytest.mark.timeout(2)
    async def test_get_database(self, db_conn) -> None:
        assert db_conn is not None
        conn = await db_conn._get_db()
        assert conn is not None
        async with conn.execute(queries["v1"][GET_TABLES]) as cursor:
            rows = await cursor.fetchall()
            assert len(rows) == 1
            assert('records' == rows[0][0])

    async def test_insert_record(self, db_with_records) -> None:
        record = self.records[0]
        conn = db_with_records
        cursor = await conn.execute(queries["v1"][INSERT_RECORD], (record.id, json.dumps(record.data)))
        await conn.commit()
        assert(cursor.rowcount == 1)

    async def test_get_record(self, db_with_records_saturated) -> None:
        test_record = self.records[-1]
        conn = db_with_records_saturated
        async with conn.execute(queries["v1"][GET_RECORD_BY_ID], (test_record.id,)) as cursor:
            rows = await cursor.fetchall()
            assert len(rows) == 1
            assert json.loads(rows[0][0]) == test_record.data

    async def test_update_record(self, db_with_records_saturated) -> None:
        target = self.records[0]
        updated_data = {"company_name": "Updated Company"}
        conn = db_with_records_saturated
        cursor = await conn.execute(queries["v1"][UPDATE_RECORD], (json.dumps(updated_data), target.id))
        await conn.commit()
        assert cursor.rowcount == 1
        async with conn.execute(queries["v1"][GET_RECORD_BY_ID], (target.id,)) as cursor:
            rows = await cursor.fetchall()
            assert json.loads(rows[0][0]) == updated_data

    async def test_insert_record_v2(self, db_with_records_saturated) -> None:
        duplicate = self.records[0]
        conn = db_with_records_saturated
        cursor = await conn.execute(queries["v2"][INSERT_RECORD], (duplicate.id, json.dumps(duplicate.data)))
        await conn.commit()
        assert cursor.rowcount == 1

    async def test_get_record_v2(self, db_with_records_saturated) -> None:
        conn = db_with_records_saturated
        async with conn.execute(queries["v2"][GET_RECORD_BY_ID], (999,)) as cursor:
            rows = await cursor.fetchall()
            assert len(rows) == 1

    async def test_update_record_v2(self, db_with_records_saturated) -> None:
        conn = db_with_records_saturated
        cursor = await conn.execute(queries["v2"][UPDATE_RECORD], (json.dumps({"company_name": "Ghost"}), 999))
        await conn.commit()
        assert cursor.rowcount == 1

    @pytest.mark.skip(reason="no history queries defined yet")
    async def test_get_record_history(self) -> None:
        pass

    @pytest.mark.skip(reason="no version queries defined yet")
    async def test_get_record_version(self) -> None:
        pass

    @pytest.mark.skip(reason="no version queries defined yet")
    async def test_get_latest_record_version(self) -> None:
        pass

