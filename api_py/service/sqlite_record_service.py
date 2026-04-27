import json

import aiosqlite

from entity.record import Record
from service.record_service import RecordService, ServiceError
from util.log import log_error
from service.queries import *

class SQLiteRecordService(RecordService):
    """SQLite-backed implementation of RecordService.

    Example:
        service = SQLiteRecordService("timetravel.db")
    """

    def __init__(self, path: str) -> None:
        self._path = path
        self._db: aiosqlite.Connection | None = None

    async def _get_db(self) -> aiosqlite.Connection:
        """Returns the open DB connection, initialising it on first call."""
        if self._db is None:
            try:
                self._db = await aiosqlite.connect(self._path)
                await self._db.execute(queries.get('v1').get(CREATE_TABLE_RECORDS))
                await self._db.execute(queries.get('v2').get(CREATE_TABLE_RECORDS))
                await self._db.commit()
            except Exception as err:
                log_error(err)
                raise
        return self._db

    async def get_record(self, id: int) -> Record | None:
        try:
            db = await self._get_db()
            async with db.execute(queries.get('v1').get(GET_RECORD_BY_ID), (id,)) as cursor:
                row = await cursor.fetchone()
        except Exception as err:
            log_error(err)
            raise

        if row is None:
            return None

        try:
            data: dict[str, str] = json.loads(row[0])
        except Exception as err:
            log_error(err)
            raise

        return Record(id=id, data=data)

    async def create_record(self, record: Record) -> None:
        if record.id <= 0:
            err = ServiceError.invalid_id()
            log_error(err)
            raise err

        try:
            data_json = json.dumps(record.data)
            db = await self._get_db()
            cursor = await db.execute(
                queries.get('v1').get(INSERT_RECORD),
                (record.id, data_json),
            )
            await db.commit()
            rows_affected = cursor.rowcount
        except Exception as err:
            log_error(err)
            raise

        if rows_affected == 0:
            err = ServiceError.already_exists()
            log_error(err)
            raise err
        return rows_affected

    async def update_record(self, id: int, updates: dict[str, str | None]) -> Record:
        record = await self.get_record(id)
        if record is None:
            raise ServiceError.not_found()

        #TODO: Is it better to have a fallback to create if record doesn't exist
        for key, value in updates.items():
            if value is None:  # deletion update
                record.data.pop(key, None)
            else:
                record.data[key] = value

        try:
            data_json = json.dumps(record.data)
            db = await self._get_db()
            await db.execute(
                queries.get('v1').get(UPDATE_RECORD),
                (data_json, id),
            )
            await db.commit()
            db.close()
        except Exception as err:
            log_error(err)
            raise

        return record

    async def get_record_history(self) -> list[Record]:
        try:
            with await self._get_db() as conn:
                cursor = conn.execute(queries.get('v1').get(GET_RECORD_HISTORY), (id))
                rows = cursor.fetchall()
                return [Record.model_validate_json(record) for record in rows]
        except Exception as err:
            log_error(err)
            raise
        return

    async def get_latest_record_version(self):
        pass

    async def get_record_version(self):
        pass