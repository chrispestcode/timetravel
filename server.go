package main

import (
	"encoding/json"
	"log"
	"net/http"
	"time"

	"timetravel/api"
	"timetravel/service"
	"timetravel/util"

	"github.com/gorilla/mux"
)

func main() {
	router := mux.NewRouter()

	service := service.NewSQLiteRecordService("timetravel.db")
	api := api.NewAPI(&service)

	apiRoute := router.PathPrefix("/api/v1").Subrouter()
	apiRoute.Path("/health").HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		err := json.NewEncoder(w).Encode(map[string]bool{"ok": true})
		util.LogError(err)
	})
	api.CreateRoutes(apiRoute)

	address := "127.0.0.1:8000"
	srv := &http.Server{
		Handler:      router,
		Addr:         address,
		WriteTimeout: 15 * time.Second,
		ReadTimeout:  15 * time.Second,
	}

	log.Printf("listening on %s", address)
	log.Fatal(srv.ListenAndServe())
}
