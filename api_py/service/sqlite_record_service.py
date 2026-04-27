import json

import aiosqlite

from entity.record import Record
from entity.record_v2 import RecordV2, RecordV2Field
from service.record_service import RecordService, ServiceError
from util.log import log_error
from service.queries import *
from queries.query_builder import RecordV2QueryBuilder

_qb = RecordV2QueryBuilder()


def _row_to_record_v2(cursor: aiosqlite.Cursor, row: aiosqlite.Row) -> RecordV2:
    columns = [desc[0] for desc in cursor.description]
    return RecordV2.model_validate(dict(zip(columns, row)))


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

    async def update_record(self, id: int, updates: dict[str, str | None]) -> Record:
        record = await self.get_record(id)
        if record is None:
            raise ServiceError.not_found()

        for key, value in updates.items():
            if value is None:
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
        except Exception as err:
            log_error(err)
            raise

        return record

    async def create_record_v2(self, record: RecordV2) -> None:
        """Inserts a new v2 record. Raises ServiceError if record_id already exists."""
        sql, values = _qb.insert(record)
        try:
            db = await self._get_db()
            await db.execute(sql, values)
            await db.commit()
        except Exception as err:
            log_error(err)
            raise

    async def get_record_v2(self, record_id: int) -> RecordV2 | None:
        """Retrieves a v2 record by record_id, or None if it does not exist."""
        try:
            db = await self._get_db()
            async with db.execute(
                queries["v2"][GET_V2_RECORD_BY_RECORD_ID], (record_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None
                return _row_to_record_v2(cursor, row)
        except Exception as err:
            log_error(err)
            raise

    async def update_record_v2(
        self,
        record_id: int,
        fields: set[RecordV2Field],
        data: dict[RecordV2Field, str],
    ) -> RecordV2:
        """Updates specific fields on a v2 record. Raises ServiceError if not found."""
        sql, values = _qb.update(fields, record_id, data)
        try:
            db = await self._get_db()
            cursor = await db.execute(sql, values)
            await db.commit()
        except Exception as err:
            log_error(err)
            raise

        if cursor.rowcount == 0:
            raise ServiceError.not_found()

        updated = await self.get_record_v2(record_id)
        assert updated is not None
        return updated

    async def get_latest_record_version(self, record_id: int) -> RecordV2 | None:
        """Returns the single ACTIVE v2 record for record_id, or None."""
        sql, values = _qb.get_latest_record_version(record_id)
        try:
            db = await self._get_db()
            async with db.execute(sql, values) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None
                return _row_to_record_v2(cursor, row)
        except Exception as err:
            log_error(err)
            raise

    async def get_record_version(self, record_id: int, version_id: int) -> RecordV2 | None:
        """Returns a specific version row by its autoincrement id, or None."""
        sql, values = _qb.get_by_row_id(record_id, version_id)
        try:
            db = await self._get_db()
            async with db.execute(sql, values) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None
                return _row_to_record_v2(cursor, row)
        except Exception as err:
            log_error(err)
            raise

    async def get_record_history(self, record_id: int) -> list[RecordV2]:
        """Returns all v2 records for record_id ordered by policy_end_date ascending."""
        sql, values = _qb.get_record_history(record_id)
        try:
            db = await self._get_db()
            async with db.execute(sql, values) as cursor:
                rows = await cursor.fetchall()
                return [_row_to_record_v2(cursor, row) for row in rows]
        except Exception as err:
            log_error(err)
            raise
