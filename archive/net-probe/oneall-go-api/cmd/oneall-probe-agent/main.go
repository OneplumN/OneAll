package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"oneall-go-api/internal/probeagent"
)

func main() {
	config := probeagent.ConfigFromEnv()
	once := flag.Bool("once", false, "run one claim/execute/report cycle and exit")
	flag.StringVar(&config.BaseURL, "api", config.BaseURL, "OneAll API base URL")
	flag.StringVar(&config.ProbeID, "probe-id", config.ProbeID, "registered probe id")
	flag.StringVar(&config.Token, "token", config.Token, "registered probe token")
	flag.StringVar(&config.Version, "version", config.Version, "agent version")
	flag.DurationVar(&config.PollInterval, "poll-interval", config.PollInterval, "task polling interval")
	flag.DurationVar(&config.Timeout, "timeout", config.Timeout, "probe execution timeout")
	flag.IntVar(&config.TaskLimit, "limit", config.TaskLimit, "max tasks to claim per cycle")
	flag.StringVar(&config.SpoolPath, "spool-path", config.SpoolPath, "local file for unsent probe results")
	capabilities := flag.String("capabilities", strings.Join(config.Capabilities, ","), "comma separated probe capabilities")
	flag.Parse()
	config.Capabilities = splitCSV(*capabilities)

	agent, err := probeagent.New(config)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	if *once {
		ctx, cancel := context.WithTimeout(ctx, config.Timeout+10*time.Second)
		defer cancel()
		if err := agent.RunOnce(ctx); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		return
	}
	if err := agent.Run(ctx); err != nil && err != context.Canceled {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func splitCSV(value string) []string {
	if value == "" {
		return nil
	}
	parts := strings.Split(value, ",")
	items := make([]string, 0, len(parts))
	for _, part := range parts {
		part = strings.TrimSpace(part)
		if part != "" {
			items = append(items, strings.ToUpper(part))
		}
	}
	return items
}
