package main

import (
	"log"

	"oneall-go-api/internal/config"
	"oneall-go-api/internal/httpapi"
)

func main() {
	cfg := config.Load()
	router := httpapi.NewRouter(cfg)
	log.Printf("OneAll Go API listening on %s", cfg.ListenAddr)
	if err := router.Run(cfg.ListenAddr); err != nil {
		log.Fatal(err)
	}
}
