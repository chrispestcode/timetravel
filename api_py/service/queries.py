from entity.record_v2 import _ISO_DATE_FMT, _ISO_DATETIME_FMT

CREATE_TABLE_RECORDS = "CREATE_TABLE_RECORDS"
GET_RECORD_BY_ID = "GET_RECORD_BY_ID"
GET_V2_RECORD_BY_RECORD_ID = "GET_V2_RECORD_BY_RECORD_ID"
INSERT_RECORD = "INSERT_RECORD"
UPDATE_RECORD = "UPDATE_RECORD"
GET_TABLES = "GET_TABLES"
GET_RECORD_HISTORY = "GET_RECORD_HISTORY"
GET_LATEST_RECORD_VERSION = "GET_LATEST_RECORD_VERSION"
UPDATE_RECORD_POLICY_START_DATE = "UPDATE_RECORD_POLICY_START_DATE"

RECORDS_V1_TABLE = "records"
RECORDS_V2_TABLE = "records_v2"

queries = {
    "v1":
        {
            CREATE_TABLE_RECORDS: f"CREATE TABLE IF NOT EXISTS {RECORDS_V1_TABLE} (id INTEGER PRIMARY KEY, data TEXT NOT NULL);",
            GET_RECORD_BY_ID : f"SELECT data FROM {RECORDS_V1_TABLE} WHERE id = ?;",
            INSERT_RECORD : f"INSERT OR IGNORE INTO {RECORDS_V1_TABLE} (id, data) VALUES (?, ?);",
            UPDATE_RECORD : f"UPDATE {RECORDS_V1_TABLE} SET data = ? WHERE id = ?;",
            GET_TABLES: "SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name;"
        },
    "v2":
        {
            CREATE_TABLE_RECORDS: f"""CREATE TABLE IF NOT EXISTS {RECORDS_V2_TABLE} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id INTEGER NOT NULL,
                    company_id INTEGER NOT NULL,
                    policy_start_date TEXT NOT NULL,
                    policy_end_date TEXT NOT NULL,
                    policy_status TEXT CHECK(policy_status IN ('ACTIVE', 'CANCELLED', 'TERMINATED', 'PENDING')),
                    created_at DATETIME NOT NULL DEFAULT (strftime('{_ISO_DATETIME_FMT}', 'now')),
                    last_updated DATETIME NOT NULL DEFAULT (strftime('{_ISO_DATETIME_FMT}', 'now')),
                    policy_tier TEXT NOT NULL,
                    policy_domain TEXT NOT NULL);""",
            GET_RECORD_BY_ID: f"SELECT * FROM {RECORDS_V2_TABLE} WHERE id = ?;",
            GET_V2_RECORD_BY_RECORD_ID: f"SELECT * FROM {RECORDS_V2_TABLE} WHERE record_id = ?;",
            INSERT_RECORD: f"INSERT INTO {RECORDS_V2_TABLE} (record_id, company_id, policy_start_date, policy_end_date, policy_status, created_at, last_updated, policy_tier, policy_domain) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
            GET_TABLES: "SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name;"
        }
}
