import pytest
from entity.record import Record
from entity.record_v2 import RecordV2, RecordV2Field
import pytest_asyncio
from queries.query_builder import RecordV2QueryBuilder
from service.sqlite_record_service import SQLiteRecordService
from service.queries import *
from typing import AsyncGenerator
import aiosqlite
import json

_v2 = RecordV2QueryBuilder()

class TestDatabase:
    @pytest_asyncio.fixture
    async def db_conn(self) -> AsyncGenerator[SQLiteRecordService, None]:
        db = SQLiteRecordService(":memory:")
        yield db
        if db._db is not None:
            await db._db.close()

    @pytest_asyncio.fixture
    async def db_with_records(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        db = SQLiteRecordService(":memory:")
        conn = await db._get_db()
        yield conn
        await conn.close()

    @pytest_asyncio.fixture
    async def db_with_v2_records(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        db = SQLiteRecordService(":memory:")
        conn = await db._get_db()
        for record in self.records_v2:
            sql, values = _v2.insert(record)
            await conn.execute(sql, values)
            await conn.commit()
        yield conn
        await conn.close()

    @pytest_asyncio.fixture
    async def db_with_records_saturated(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        db = SQLiteRecordService(":memory:")
        conn = await db._get_db()
        for record in self.records:
            await conn.execute(queries["v1"][INSERT_RECORD], (record.id, json.dumps(record.data)))
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
    
    records_v2: list[RecordV2] = [
        RecordV2(
            record_id=20, company_id=1,
            policy_start_date="01-01-2020", policy_end_date="07-31-2026",
            policy_status="ACTIVE", policy_tier="BRONZE", policy_domain="shops",
            created_at="2020-01-01T00:00:00", last_updated="2020-01-01T00:00:00",
        )
    ]

    @pytest.mark.timeout(2)
    async def test_get_database(self, db_conn) -> None:
        assert db_conn is not None
        conn = await db_conn._get_db()
        assert conn is not None
        async with conn.execute(queries["v1"][GET_TABLES]) as cursor:
            rows = await cursor.fetchall()
            assert any(row[0] == RECORDS_V1_TABLE for row in rows)
            assert any(row[0] == RECORDS_V2_TABLE for row in rows)

    async def test_insert_record(self, db_with_records) -> None:
        ''' Can a v1 record be inserted into the SQLite database ? '''
        record = self.records[0]
        conn = db_with_records
        cursor = await conn.execute(queries["v1"][INSERT_RECORD], (record.id, json.dumps(record.data)))
        await conn.commit()
        assert(cursor.rowcount == 1)

    async def test_get_record(self, db_with_records_saturated) -> None:
        ''' Can a v1 Record be retrieved from the SQLite database ? '''
        
        test_record = self.records[-1]
        conn = db_with_records_saturated
        async with conn.execute(queries["v1"][GET_RECORD_BY_ID], (test_record.id,)) as cursor:
            rows = await cursor.fetchall()
            assert len(rows) == 1
            assert json.loads(rows[0][0]) == test_record.data

    async def test_update_record(self, db_with_records_saturated) -> None:
        ''' Can an existing v1 record be updated in the SQLite database ? '''
        
        target = self.records[0]
        updated_data = {"company_name": "Updated Company"}
        conn = db_with_records_saturated
        cursor = await conn.execute(queries["v1"][UPDATE_RECORD], (json.dumps(updated_data), target.id))
        await conn.commit()
        assert cursor.rowcount == 1
        async with conn.execute(queries["v1"][GET_RECORD_BY_ID], (target.id,)) as cursor:
            rows = await cursor.fetchall()
            assert json.loads(rows[0][0]) == updated_data

    async def test_create_table_v2(self, db_conn) -> None:
        ''' Can a v2 record TABLE be created in SQLite database with all columns ? '''
        
        conn = await db_conn._get_db()
        await conn.execute(queries["v2"][CREATE_TABLE_RECORDS])

        async with conn.execute(f"PRAGMA table_info({RECORDS_V2_TABLE})") as cursor:
            rows = await cursor.fetchall()

        # column index 1 is the name in PRAGMA table_info output
        actual_columns = {row[1] for row in rows}
        expected_columns = set(RecordV2.model_fields.keys())

        assert actual_columns == expected_columns

    async def test_insert_record_v2(self, db_with_v2_records) -> None:
        ''' Can a second v2 record be inserted ? '''
        conn = db_with_v2_records
        record = RecordV2(
            record_id=21, company_id=2,
            policy_start_date="06-01-2024", policy_end_date="06-01-2025",
            policy_status="ACTIVE", policy_tier="SILVER", policy_domain="retail",
            created_at="2024-01-01T00:00:00", last_updated="2024-01-01T00:00:00",
        )
        sql, values = _v2.insert(record)
        cursor = await conn.execute(sql, values)
        await conn.commit()
        assert cursor.rowcount == 1

    async def test_get_record_v2(self, db_with_v2_records) -> None:
        ''' Can a v2 record be retrieved by record_id ? '''
        conn = db_with_v2_records
        async with conn.execute(
            f"SELECT * FROM {RECORDS_V2_TABLE} WHERE record_id = ?", (20,)
        ) as cursor:
            rows = await cursor.fetchall()
            assert len(rows) == 1

    async def test_update_record_v2(self, db_with_v2_records) -> None:
        ''' Can a v2 record field be updated ? '''
        conn = db_with_v2_records
        sql, values = _v2.update(
            fields={RecordV2Field.POLICY_START_DATE},
            record_id=20,
            data={RecordV2Field.POLICY_START_DATE: "2021-03-01"},
        )
        cursor = await conn.execute(sql, values)
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

