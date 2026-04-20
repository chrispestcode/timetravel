package service

import (
	"context"
	"database/sql"
	"encoding/json"
	"timetravel/entity"
	"timetravel/util"

	_ "modernc.org/sqlite"
)

// SQLiteRecordService is a SQLite-backed implementation of RecordService.
type SQLiteRecordService struct {
	db *sql.DB
}

func NewSQLiteRecordService(path string) SQLiteRecordService {
	db, err := sql.Open("sqlite", path)
	if err != nil {
		util.LogError(err)
		return SQLiteRecordService{}
	}

	_, err = db.Exec(`CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY, data TEXT NOT NULL)`)
	if err != nil {
		util.LogError(err)
		return SQLiteRecordService{}
	}

	return SQLiteRecordService{db: db}
}

func (s *SQLiteRecordService) GetRecord(ctx context.Context, id int) (entity.Record, error) {
	row := s.db.QueryRowContext(ctx, `SELECT data FROM records WHERE id = ?`, id)

	var dataJSON string
	if err := row.Scan(&dataJSON); err != nil {
		if err == sql.ErrNoRows {
			util.LogError(ErrRecordDoesNotExist)
			return entity.Record{}, ErrRecordDoesNotExist
		}
		util.LogError(err)
		return entity.Record{}, err
	}

	var data map[string]string
	if err := json.Unmarshal([]byte(dataJSON), &data); err != nil {
		util.LogError(err)
		return entity.Record{}, err
	}

	return entity.Record{ID: id, Data: data}, nil
}

func (s *SQLiteRecordService) CreateRecord(ctx context.Context, record entity.Record) error {
	id := record.ID
	if id <= 0 {
		util.LogError(ErrRecordIDInvalid)
		return ErrRecordIDInvalid
	}

	dataJSON, err := json.Marshal(record.Data)
	if err != nil {
		util.LogError(err)
		return err
	}

	result, err := s.db.ExecContext(ctx, `INSERT OR IGNORE INTO records (id, data) VALUES (?, ?)`, id, string(dataJSON))
	if err != nil {
		util.LogError(err)
		return err
	}

	rows, err := result.RowsAffected()
	if err != nil {
		util.LogError(err)
		return err
	}
	if rows == 0 {
		util.LogError(ErrRecordAlreadyExists)
		return ErrRecordAlreadyExists
	}

	return nil
}

func (s *SQLiteRecordService) UpdateRecord(ctx context.Context, id int, updates map[string]*string) (entity.Record, error) {
	record, err := s.GetRecord(ctx, id)
	if err != nil {
		return entity.Record{}, err
	}

	for key, value := range updates {
		if value == nil { // deletion update
			delete(record.Data, key)
		} else {
			record.Data[key] = *value
		}
	}

	dataJSON, err := json.Marshal(record.Data)
	if err != nil {
		util.LogError(err)
		return entity.Record{}, err
	}

	_, err = s.db.ExecContext(ctx, `UPDATE records SET data = ? WHERE id = ?`, string(dataJSON), id)
	if err != nil {
		util.LogError(err)
		return entity.Record{}, err
	}

	return record, nil
}
