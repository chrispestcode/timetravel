package api

import (
	"github.com/gorilla/mux"
	"timetravel/service"
)

type API struct {
	records service.RecordService
}

func NewAPI(records service.RecordService) *API {
	return &API{records}
}

// generates all api routes
func (api *API) CreateRoutes(routes *mux.Router) {
	routes.Path("/records/{id}").HandlerFunc(api.GetRecords).Methods("GET")
	routes.Path("/records/{id}").HandlerFunc(api.PostRecords).Methods("POST")
}
