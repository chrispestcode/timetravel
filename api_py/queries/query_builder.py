from collections.abc import Iterable

from entity.record_v2 import RecordV2, RecordV2Field

_TABLE = "records_v2"
_ID_COL = "record_id"
_INSERT_COLS = list(RecordV2Field)


class RecordV2QueryBuilder:
    """Builds parameterised SQL for records_v2 from RecordV2Field members.

    Column names are sourced from RecordV2Field so any rename there propagates
    automatically. Each method returns a (sql, values) tuple ready for aiosqlite.

    Example:
        builder = RecordV2QueryBuilder()
        sql, values = builder.insert(record)
        await conn.execute(sql, values)

        sql, values = builder.update(
            {RecordV2Field.POLICY_STATUS, RecordV2Field.LAST_UPDATED},
            record_id=20,
            data={RecordV2Field.POLICY_STATUS: "CANCELLED",
                  RecordV2Field.LAST_UPDATED: "2026-04-27T00:00:00"},
        )
        await conn.execute(sql, values)
    """

    def insert(self, record: RecordV2) -> tuple[str, tuple]:
        """Builds an INSERT for all non-None RecordV2Field columns.

        None-valued optional fields (e.g. created_at, last_updated) are omitted so
        SQLite applies the column DEFAULT rather than violating NOT NULL.

        Args:
            record: The RecordV2 instance to insert.

        Returns:
            A (sql, values) tuple where values are ISO-serialised and ordered to
            match the column list.
        """
        dump = record.model_dump(mode="json")
        present = [(col, dump[col]) for col in _INSERT_COLS if dump[col] is not None]
        cols = ", ".join(col for col, _ in present)
        placeholders = ", ".join("?" * len(present))
        values = tuple(val for _, val in present)
        sql = f"INSERT INTO {_TABLE} ({cols}) VALUES ({placeholders});"
        return sql, values

    def update(
        self,
        fields: Iterable[RecordV2Field],
        record_id: int,
        data: dict[RecordV2Field, str],
    ) -> tuple[str, tuple]:
        """Builds a partial UPDATE for the specified fields only.

        Args:
            fields: RecordV2Field members to include in the SET clause.
            record_id: The record_id to match in the WHERE clause.
            data: Mapping of field → value for each field in fields.

        Returns:
            A (sql, values) tuple. Values are field values in sorted order,
            with record_id appended last.

        Raises:
            ValueError: If fields is empty or data is missing a required field.
        """
        ordered = sorted(fields, key=lambda f: f.value)
        if not ordered:
            raise ValueError("At least one field must be specified for update.")
        missing = [f for f in ordered if f not in data]
        if missing:
            raise ValueError(f"Missing values for fields: {missing}")
        set_clause = ", ".join(f"{field} = ?" for field in ordered)
        sql = f"UPDATE {_TABLE} SET {set_clause} WHERE {_ID_COL} = ?;"
        values = tuple(data[field] for field in ordered) + (record_id,)
        return sql, values
    
    def get_latest_record_version(self, record_id: int) -> tuple[str, tuple]:
        return f"SELECT * FROM {_TABLE} WHERE record_id = ? AND policy_status = 'ACTIVE'  LIMIT 1;", (record_id,)
    
    def get_record_history(self, record_id: int) -> tuple[str, tuple]:
        return f"SELECT * FROM {_TABLE} WHERE record_id = ? ORDER BY policy_end_date ASC;", (record_id,)

    def get_by_row_id(self, record_id: int, row_id: int) -> tuple[str, tuple]:
        """Gets a specific version by its autoincrement id, scoped to record_id."""
        return f"SELECT * FROM {_TABLE} WHERE id = ? AND record_id = ?;", (row_id, record_id)
