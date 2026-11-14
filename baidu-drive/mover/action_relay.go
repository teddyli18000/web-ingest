package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log/slog"
	"os"
	"path/filepath"
	"strings"

	"github.com/teddyli18000/baidu-drive-mover/internal/app"
	"github.com/teddyli18000/baidu-drive-mover/internal/baidu"
	cleanupengine "github.com/teddyli18000/baidu-drive-mover/internal/cleanup"
	"github.com/teddyli18000/baidu-drive-mover/internal/drive"
	"github.com/teddyli18000/baidu-drive-mover/internal/drive/rclone"
	runtimepath "github.com/teddyli18000/baidu-drive-mover/internal/runtime"
	"github.com/teddyli18000/baidu-drive-mover/internal/state"
)

const (
	defaultRelayStageWindowBytes = int64(8 << 30)
	relayStageBatchFiles         = 3
	relayStageTargetFiles        = 3
)

type relayPrepareConfig struct {
	Layout            *runtimepath.Layout
	Store             *state.Store
	CookieStore       baidu.CookieStore
	Browser           app.BrowserLogin
	Logger            *slog.Logger
	RelayResultsPath  string
	RelayManifestPath string
	StageWindowBytes  int64
	NewStagingClient func(string)(app.StagingBaiduAPI,error)
	NewCleanupClient func(string)(app.CleanupBaiduAPI,error)
}

func runRelayPreparation(ctx context.Context, taskID string, cfg relayPrepareConfig) error {
	if cfg.Layout == nil || cfg.Store == nil || cfg.Browser == nil {
		return fmt.Errorf("relay preparation is not fully configured")
	}
	if strings.TrimSpace(cfg.RelayManifestPath) == "" {
		return fmt.Errorf("relay manifest output path is required")
	}
	if err := importRelayResults(ctx, cfg.Store, taskID, cfg.RelayResultsPath); err != nil {
		return err
	}

	// Cleanup is always attempted before staging another batch. This keeps the
	// Baidu account staging footprint bounded by verified downstream progress.
	cleanupRunner := &app.CleanupRunner{
		Layout:      cfg.Layout,
		Store:       cfg.Store,
		Browser:     cfg.Browser,
		Output:      io.Discard,
		Logger:      cfg.Logger,
		CookieStore: cfg.CookieStore,
		MaxBatches:  32,
		NewClient: cfg.NewCleanupClient,
	}
	if _, err := cleanupRunner.Run(ctx, taskID); err != nil {
		return fmt.Errorf("relay cleanup pass: %w", err)
	}
	if complete, err := finishRelayTaskIfComplete(ctx, cfg.Store, taskID); err != nil {
		return err
	} else if complete {
		return writeRelayManifest(cfg.RelayManifestPath, nil)
	}

	// The prepared rclone configuration is used only to reconcile the task root
	// and logical directory IDs. Actual file bytes use the direct Drive
	// resumable relay path.
	process := rclone.OSRunner{}
	client, err := rclone.NewClient(cfg.Layout, process)
	if err != nil {
		return fmt.Errorf("create Drive tree client: %w", err)
	}
	if err := client.ProbeDrive(ctx); err != nil {
		return fmt.Errorf("probe prepared Drive authorization: %w", err)
	}
	builder := &drive.TreeBuilder{State: cfg.Store, Remote: client}
	if _, err := builder.Ensure(ctx, taskID); err != nil {
		return fmt.Errorf("reconcile Drive directory tree: %w", err)
	}


	// Keep the three independent file-worker slots supplied. Previously one
	// staged file prevented another batch from being staged until it completed.
	// Each preparation pass can fill at most three staged batches, with the
	// same per-batch byte bound and mover provenance/cleanup rules.
	files, err := cfg.Store.ActionRelayFiles(ctx, taskID)
	if err != nil {
		return err
	}
	window := cfg.StageWindowBytes
	if window <= 0 {
		window = defaultRelayStageWindowBytes
	}
	for stagePass := 0; stagePass < relayStageTargetFiles && len(files) < relayStageTargetFiles; stagePass++ {
		if _, err := cfg.Store.PlanBatchesBounded(ctx, taskID, relayStageBatchFiles, window); err != nil {
			return fmt.Errorf("plan relay staging batch: %w", err)
		}
		pending, err := cfg.Store.StagingBatches(ctx, taskID)
		if err != nil {
			return fmt.Errorf("read relay staging batches: %w", err)
		}
		if len(pending) == 0 {
			break
		}

		// A single file may exceed the byte target; its isolated batch is
		// allowed because bytes remain remote until streamed to Drive.
		allowed := window
		if pending[0].TotalBytes > allowed {
			if pending[0].FileCount != 1 {
				return fmt.Errorf("oversized relay batch contains %d files", pending[0].FileCount)
			}
			allowed = pending[0].TotalBytes
		}
		stageRunner := &app.StageRunner{
			Store:         cfg.Store,
			Browser:       cfg.Browser,
			Output:        io.Discard,
			Logger:        cfg.Logger,
			CookieStore:   cfg.CookieStore,
			BatchSize:     relayStageBatchFiles,
			MaxBatches:    1,
			MaxCacheBytes: 0,
			MaxBatchBytes: allowed,
			NewClient: cfg.NewStagingClient,
		}
		if _, err := stageRunner.Run(ctx, taskID); err != nil {
			return fmt.Errorf("stage relay batch: %w", err)
		}
		nextFiles, err := cfg.Store.ActionRelayFiles(ctx, taskID)
		if err != nil {
			return err
		}
		if len(nextFiles) <= len(files) {
			return fmt.Errorf("staging pass produced no additional relay files")
		}
		files = nextFiles
	}
	if len(files) == 0 {
		return fmt.Errorf("no staged relay files and no pending staging batch")
	}
	if err := cfg.Store.UpdateTaskStatus(ctx, taskID, state.TaskPaused, ""); err != nil {
		return err
	}
	return writeRelayManifest(cfg.RelayManifestPath, files)
}

func importRelayResults(ctx context.Context, store *state.Store, taskID, path string) error {
	path = strings.TrimSpace(path)
	if path == "" {
		return nil
	}
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		return fmt.Errorf("read relay results: %w", err)
	}
	if len(strings.TrimSpace(string(data))) == 0 {
		return nil
	}
	var values []state.ActionRelayVerification
	if err := json.Unmarshal(data, &values); err != nil {
		return fmt.Errorf("parse relay results: %w", err)
	}
	if err := store.ApplyActionRelayVerifications(ctx, taskID, values); err != nil {
		return fmt.Errorf("import relay results: %w", err)
	}
	return nil
}

func finishRelayTaskIfComplete(ctx context.Context, store *state.Store, taskID string) (bool, error) {
	progress, err := store.PipelineProgress(ctx, taskID)
	if err != nil {
		return false, fmt.Errorf("read relay pipeline progress: %w", err)
	}
	if !progress.Complete() {
		return false, nil
	}
	if err := store.UpdateTaskStatus(ctx, taskID, state.TaskCompleted, ""); err != nil {
		return false, err
	}
	return true, nil
}

func writeRelayManifest(path string, files []state.ActionRelayFile) error {
	if files == nil {
		files = []state.ActionRelayFile{}
	}
	blob, err := json.MarshalIndent(files, "", "  ")
	if err != nil {
		return fmt.Errorf("encode relay manifest: %w", err)
	}
	blob = append(blob, '\n')
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return fmt.Errorf("create relay manifest directory: %w", err)
	}
	if err := os.WriteFile(path, blob, 0o600); err != nil {
		return fmt.Errorf("write relay manifest: %w", err)
	}
	return nil
}

// Keep the cleanup package linked in the integration build. This compile-time
// assertion also documents that the relay path intentionally reuses the
// existing provenance-guarded destructive stage rather than replacing it.
var _ cleanupengine.Summary
