package service

import (
	"context"
	"net/http"

	"timetravel/entity"
)

// ServiceError is a domain error with an associated HTTP status code.
type ServiceError struct {
	Code    int
	Message string
}

func (e *ServiceError) Error() string { return e.Message }

var (
	ErrRecordDoesNotExist  = &ServiceError{Code: http.StatusNotFound, Message: "record with that id does not exist"}
	ErrRecordIDInvalid     = &ServiceError{Code: http.StatusBadRequest, Message: "record id must be > 0"}
	ErrRecordAlreadyExists = &ServiceError{Code: http.StatusConflict, Message: "record already exists"}
)

// Implements methods to get, create, and update record data.
type RecordService interface {

	// GetRecord will retrieve a record.
	GetRecord(ctx context.Context, id int) (entity.Record, error)

	// CreateRecord will insert a new record.
	//
	// If a record with that id already exists it will fail.
	// If id <= 0 it will fail.
	CreateRecord(ctx context.Context, record entity.Record) error

	// UpdateRecord will change the internal `Map` values of the record if they exist.
	// If the update[key] is null it will delete that key from the record's Map.
	//
	// UpdateRecord will error if the record does not exist with that id.
	UpdateRecord(ctx context.Context, id int, updates map[string]*string) (entity.Record, error)
}
