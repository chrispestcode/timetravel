import pytest
import pytest_asyncio
from service.sqlite_record_service import SQLiteRecordService
from service.queries import queries, GET_TABLES
from typing import AsyncGenerator


class TestDatabase:
    @pytest_asyncio.fixture
    def db_conn(self):
        db = SQLiteRecordService(":memory:")
        yield db

    
    async def test_get_database(self, db_conn) -> None:
        assert db_conn is not None
        conn = await db_conn._get_db()
        assert conn is not None
        async with conn.execute(queries["v1"][GET_TABLES]) as cursor:
            rows = await cursor.fetchall()
            assert len(rows) == 1
    
    async def test_insert_record(self): 
        pass
    
    async def test_get_record(self):
        pass
    
    async def test_update_record(self):
        pass
    
    async def test_insert_record_v2(self):
        pass

    async def test_get_record_v2(self):
        pass
    
    async def test_update_record_v2(self):
        pass
    
    async def test_get_record_history(self):
        pass
    
    async def test_get_record_version(self):
        pass
    
    async def test_get_latest_record_version(self):
        pass
    
    