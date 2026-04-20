CREATE_TABLE_RECORDS = "CREATE_TABLE_RECORDS"
GET_RECORD_BY_ID = "GET_RECORD_BY_ID"
INSERT_RECORD = "INSERT_RECORD"
UPDATE_RECORD = "UPDATE_RECORD"
GET_TABLES = "GET_TABLES"

queries = {
    "v1":
        {
            CREATE_TABLE_RECORDS: "CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY, data TEXT NOT NULL)",
            GET_RECORD_BY_ID : "SELECT data FROM records WHERE id = ?",
            INSERT_RECORD : "INSERT OR IGNORE INTO records (id, data) VALUES (?, ?)",
            UPDATE_RECORD : "UPDATE records SET data = ? WHERE id = ?",
            GET_TABLES: "SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name;"
        }
    
}