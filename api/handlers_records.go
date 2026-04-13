package api

import (
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"strconv"

	"github.com/gorilla/mux"
	"timetravel/entity"
	"timetravel/service"
)

// writeServiceError writes the appropriate HTTP response for a service error.
func writeServiceError(writer http.ResponseWriter, err error) {
	var svcErr *service.ServiceError
	if errors.As(err, &svcErr) {
		logError(writeError(writer, svcErr.Message, svcErr.Code))
	} else {
		logError(writeError(writer, ErrInternal.Error(), http.StatusInternalServerError))
	}
}

// GET /records/{id}
// GetRecords retrieves the record.
func (api *API) GetRecords(writer http.ResponseWriter, request *http.Request) {
	ctx := request.Context()
	id := mux.Vars(request)["id"]

	idNumber, err := strconv.ParseInt(id, 10, 32)
	if err != nil || idNumber <= 0 {
		logError(writeError(writer, "invalid id; id must be a positive number", http.StatusBadRequest))
		return
	}

	record, err := api.records.GetRecord(ctx, int(idNumber))
	if err != nil {
		if errors.Is(err, service.ErrRecordDoesNotExist) {
			logError(writeError(writer, fmt.Sprintf("record of id %v does not exist", idNumber), http.StatusNotFound))
		} else {
			writeServiceError(writer, err)
		}
		return
	}

	logError(writeJSON(writer, record, http.StatusOK))
}

// POST /records/{id}
// if the record exists, the record is updated.
// if the record doesn't exist, the record is created.
func (api *API) PostRecords(writer http.ResponseWriter, request *http.Request) {
	ctx := request.Context()
	id := mux.Vars(request)["id"]

	idNumber, err := strconv.ParseInt(id, 10, 32)
	if err != nil || idNumber <= 0 {
		logError(writeError(writer, "invalid id; id must be a positive number", http.StatusBadRequest))
		return
	}

	var body map[string]*string
	if err = json.NewDecoder(request.Body).Decode(&body); err != nil {
		logError(writeError(writer, "invalid input; could not parse json", http.StatusBadRequest))
		return
	}

	// first retrieve the record
	record, err := api.records.GetRecord(ctx, int(idNumber))

	if errors.Is(err, service.ErrRecordDoesNotExist) { // record does not exist, create it
		// exclude the delete updates
		recordMap := map[string]string{}
		for key, value := range body {
			if value != nil {
				recordMap[key] = *value
			}
		}
		record = entity.Record{ID: int(idNumber), Data: recordMap}
		err = api.records.CreateRecord(ctx, record)
	} else if err == nil { // record exists, update it
		record, err = api.records.UpdateRecord(ctx, int(idNumber), body)
	}

	if err != nil {
		writeServiceError(writer, err)
		return
	}

	logError(writeJSON(writer, record, http.StatusOK))
}
