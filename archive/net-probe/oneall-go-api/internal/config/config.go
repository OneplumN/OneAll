package config

import "os"

type Config struct {
	ListenAddr  string
	DatabaseURL string
	JWTSecret   string
}

func Load() Config {
	return Config{
		ListenAddr:  valueOrDefault(os.Getenv("ONEALL_LISTEN_ADDR"), "127.0.0.1:5184"),
		DatabaseURL: os.Getenv("DATABASE_URL"),
		JWTSecret:   valueOrDefault(os.Getenv("ONEALL_JWT_SECRET"), "dev-secret-change-me"),
	}
}

func valueOrDefault(value string, fallback string) string {
	if value == "" {
		return fallback
	}
	return value
}
