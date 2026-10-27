package main

import (
	"bufio"
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"log/slog"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"syscall"

	"github.com/teddyli18000/baidu-drive-mover/internal/app"
	"github.com/teddyli18000/baidu-drive-mover/internal/baidu"
	downloadengine "github.com/teddyli18000/baidu-drive-mover/internal/download"
	"github.com/teddyli18000/baidu-drive-mover/internal/drive/rclone"
	runtimepath "github.com/teddyli18000/baidu-drive-mover/internal/runtime"
	"github.com/teddyli18000/baidu-drive-mover/internal/state"
)

// This file is copied into a pinned checkout of baidu-drive-mover at build
// time. Living under that module lets it reuse the mover's internal packages
// without duplicating the transfer implementation in web-ingest.

type blockedBrowser struct{}

func (blockedBrowser) Login(context.Context) (string, error) {
	return "", errors.New("interactive Baidu login is disabled in the Actions bridge")
}

type actionResult struct {
	MoverTaskID    string               `json:"mover_task_id,omitempty"`
	Status         string               `json:"status,omitempty"`
	ScanCompleted  bool                 `json:"scan_completed"`
	DriveRootID    string               `json:"drive_root_id,omitempty"`
	DriveRootName  string               `json:"drive_root_name,omitempty"`
	Progress       state.ActionProgress `json:"progress"`
	LastError      string               `json:"last_error,omitempty"`
	PipelinePaused bool                 `json:"pipeline_paused"`
}

func main() {
	os.Exit(run())
}

func run() int {
	fs := flag.NewFlagSet("baidu-drive-action", flag.ContinueOnError)
	fs.SetOutput(os.Stderr)
	shareURL := fs.String("share-url", "", "public Baidu share URL for a new task")
	extractionCode := fs.String("extraction-code", "", "share extraction code, if required")
	resumeTaskID := fs.String("resume", "", "existing mover task ID to resume")
	runtimeBase := fs.String("runtime-base", "", "ephemeral runner directory owned by this invocation")
	stateDBPath := fs.String("state-db", "", "checkpoint SQLite file copied in/out by the caller")
	baiduCookieFile := fs.String("baidu-cookie-file", "", "prepared Baidu session file")
	rcloneConfigFile := fs.String("rclone-config-file", "", "prepared rclone config file")
	rcloneBinary := fs.String("rclone-bin", "", "prepared platform rclone executable")
	resultJSON := fs.String("result-json", "", "machine-readable result output path")
	maxCacheBytes := fs.Int64("max-cache-bytes", 6<<30, "runner-local cache high-water mark")
	if err := fs.Parse(os.Args[1:]); err != nil {
		return 2
	}
	if fs.NArg() != 0 || strings.TrimSpace(*runtimeBase) == "" || strings.TrimSpace(*stateDBPath) == "" || strings.TrimSpace(*resultJSON) == "" {
		fmt.Fprintln(os.Stderr, "runtime-base, state-db and result-json are required; positional arguments are not accepted")
		return 2
	}
	if strings.TrimSpace(*resumeTaskID) == "" && strings.TrimSpace(*shareURL) == "" {
		fmt.Fprintln(os.Stderr, "share-url is required when no mover task is being resumed")
		return 2
	}
	if *maxCacheBytes <= 0 {
		fmt.Fprintln(os.Stderr, "max-cache-bytes must be positive")
		return 2
	}

	layout, err := runtimepath.New(*runtimeBase)
	if err != nil {
		return failBeforeStore(*resultJSON, fmt.Errorf("create runtime layout: %w", err))
	}
	if err := layout.Ensure(); err != nil {
		return failBeforeStore(*resultJSON, fmt.Errorf("initialize runtime layout: %w", err))
	}
	if err := restoreOptional(*stateDBPath, layout.StateDB, 0o600); err != nil {
		return failBeforeStore(*resultJSON, fmt.Errorf("restore state checkpoint: %w", err))
	}
	if err := requireAndCopy(*baiduCookieFile, filepath.Join(layout.Auth, "baidu.cookies"), 0o600, "Baidu session"); err != nil {
		return failBeforeStore(*resultJSON, err)
	}
	if err := requireAndCopy(*rcloneConfigFile, layout.RcloneConfig, 0o600, "Google Drive rclone config"); err != nil {
		return failBeforeStore(*resultJSON, err)
	}
	if err := requireAndCopy(*rcloneBinary, layout.RcloneExe, 0o700, "rclone executable"); err != nil {
		return failBeforeStore(*resultJSON, err)
	}

	store, err := state.Open(layout.StateDB)
	if err != nil {
		return failBeforeStore(*resultJSON, fmt.Errorf("open state checkpoint: %w", err))
	}
	closed := false
	defer func() {
		if !closed {
			_ = store.Close()
		}
	}()

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	moverTaskID := strings.TrimSpace(*resumeTaskID)
	if moverTaskID != "" {
		if err := store.ResetEphemeralCacheStates(ctx, moverTaskID); err != nil {
			return finish(store, &closed, layout, *stateDBPath, *resultJSON, moverTaskID, err, false)
		}
	}

	cookieStore := baidu.NewCookieStore(layout)
	browser := blockedBrowser{}
	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	input := strings.TrimSpace(*extractionCode)
	if input != "" {
		input += "\n"
	}
	scanRunner := &app.ScanRunner{
		Layout:      layout,
		Store:       store,
		Browser:     browser,
		Input:       bufio.NewReader(strings.NewReader(input)),
		Output:      io.Discard,
		Logger:      logger,
		CookieStore: cookieStore,
		NewClient: func(cookieHeader string) (app.BaiduAPI, error) {
			return baidu.NewClient(cookieHeader)
		},
	}

	if moverTaskID == "" {
		moverTaskID, _, err = scanRunner.Run(ctx, strings.TrimSpace(*shareURL))
	} else {
		var task state.Task
		task, err = store.GetTask(ctx, moverTaskID)
		if err == nil && !task.ScanCompleted {
			moverTaskID, _, err = scanRunner.Resume(ctx, task)
		}
	}
	if err != nil {
		return finish(store, &closed, layout, *stateDBPath, *resultJSON, moverTaskID, err, false)
	}

	stageRunner := &app.StageRunner{
		Store:         store,
		Browser:       browser,
		Output:        io.Discard,
		Logger:        logger,
		CookieStore:   cookieStore,
		BatchSize:     200,
		MaxBatches:    1,
		MaxCacheBytes: *maxCacheBytes,
		NewClient: func(cookieHeader string) (app.StagingBaiduAPI, error) {
			return baidu.NewClient(cookieHeader)
		},
	}
	downloadRunner := &app.DownloadRunner{
		Layout:        layout,
		Store:         store,
		Browser:       browser,
		Output:        io.Discard,
		Logger:        logger,
		CookieStore:   cookieStore,
		MaxCacheBytes: *maxCacheBytes,
		NewClient: func(cookieHeader string) (app.DownloadBaiduAPI, error) {
			return baidu.NewClient(cookieHeader)
		},
	}
	driveRunner := &app.DriveRunner{
		Layout:     layout,
		Store:      store,
		Output:     io.Discard,
		Logger:     logger,
		Process:    rclone.OSRunner{},
		HTTPClient: rclone.SecureHTTPClient(),
		Provision: func(context.Context, *runtimepath.Layout, rclone.Runner, rclone.HTTPDoer) error {
			// The Actions wrapper installs a platform-native rclone binary into
			// Layout.RcloneExe. Skip the Windows-only pinned helper provisioner.
			if info, statErr := os.Stat(layout.RcloneExe); statErr != nil || info.IsDir() {
				if statErr != nil {
					return fmt.Errorf("prepared rclone executable is unavailable: %w", statErr)
				}
				return fmt.Errorf("prepared rclone executable is not a regular file")
			}
			return nil
		},
	}
	cleanupRunner := &app.CleanupRunner{
		Layout:      layout,
		Store:       store,
		Browser:     browser,
		Output:      io.Discard,
		Logger:      logger,
		CookieStore: cookieStore,
		MaxBatches:  8,
		NewClient: func(cookieHeader string) (app.CleanupBaiduAPI, error) {
			return baidu.NewClient(cookieHeader)
		},
	}
	pipeline := &app.PipelineRunner{
		State:         store,
		Logger:        logger,
		MaxCacheBytes: *maxCacheBytes,
		Cleanup:       cleanupRunner.Run,
		Drive:         driveRunner.Run,
		Download:      downloadRunner.Run,
		Stage: func(passCtx context.Context, taskID string, available int64) (app.StageSummary, error) {
			stageRunner.MaxBatchBytes = available
			return stageRunner.Run(passCtx, taskID)
		},
	}

	_, err = pipeline.Run(ctx, moverTaskID)
	paused := errors.Is(err, context.Canceled) || errors.Is(err, context.DeadlineExceeded) || errors.Is(err, app.ErrPipelineCacheWatermark)
	var deferred *app.StagingDeferredByWatermarkError
	paused = paused || errors.As(err, &deferred)
	return finish(store, &closed, layout, *stateDBPath, *resultJSON, moverTaskID, err, paused)
}

func finish(store *state.Store, closed *bool, layout *runtimepath.Layout, checkpointPath, resultPath, moverTaskID string, runErr error, paused bool) int {
	result := actionResult{MoverTaskID: moverTaskID, PipelinePaused: paused}
	if moverTaskID != "" {
		if task, err := store.GetTask(context.Background(), moverTaskID); err == nil {
			result.Status = string(task.Status)
			result.ScanCompleted = task.ScanCompleted
			result.DriveRootID = task.DriveRootID
			result.DriveRootName = task.DriveRootName
			if result.LastError == "" {
				result.LastError = task.LastError
			}
		}
		if progress, err := store.ActionProgressForTask(context.Background(), moverTaskID); err == nil {
			result.Progress = progress
		}
	}
	if runErr != nil {
		result.LastError = safeMessage(runErr)
	}
	closeErr := store.Close()
	*closed = true
	if closeErr != nil && runErr == nil {
		runErr = fmt.Errorf("close state database: %w", closeErr)
		result.LastError = safeMessage(runErr)
	}
	if err := copyFile(layout.StateDB, checkpointPath, 0o600); err != nil && runErr == nil {
		runErr = fmt.Errorf("persist state checkpoint: %w", err)
		result.LastError = safeMessage(runErr)
	}
	if err := writeResult(resultPath, result); err != nil {
		fmt.Fprintln(os.Stderr, "write result:", err)
		return 1
	}
	if runErr != nil {
		fmt.Fprintln(os.Stderr, "Actions bridge stopped safely:", safeMessage(runErr))
		return 1
	}
	return 0
}

func failBeforeStore(resultPath string, err error) int {
	_ = writeResult(resultPath, actionResult{LastError: safeMessage(err)})
	fmt.Fprintln(os.Stderr, "Actions bridge setup failed:", safeMessage(err))
	return 1
}

func writeResult(path string, result actionResult) error {
	if strings.TrimSpace(path) == "" {
		return nil
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return err
	}
	blob, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		return err
	}
	blob = append(blob, '\n')
	return os.WriteFile(path, blob, 0o600)
}

func restoreOptional(source, target string, mode os.FileMode) error {
	if strings.TrimSpace(source) == "" {
		return nil
	}
	info, err := os.Stat(source)
	if errors.Is(err, os.ErrNotExist) {
		return nil
	}
	if err != nil {
		return err
	}
	if !info.Mode().IsRegular() {
		return fmt.Errorf("checkpoint is not a regular file")
	}
	return copyFile(source, target, mode)
}

func requireAndCopy(source, target string, mode os.FileMode, label string) error {
	if strings.TrimSpace(source) == "" {
		return fmt.Errorf("%s input is not configured", label)
	}
	info, err := os.Stat(source)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return fmt.Errorf("%s input is not configured", label)
		}
		return fmt.Errorf("inspect %s input: %w", label, err)
	}
	if !info.Mode().IsRegular() {
		return fmt.Errorf("%s input is not a regular file", label)
	}
	return copyFile(source, target, mode)
}

func copyFile(source, target string, mode os.FileMode) error {
	input, err := os.Open(source)
	if err != nil {
		return err
	}
	defer input.Close()
	if err := os.MkdirAll(filepath.Dir(target), 0o700); err != nil {
		return err
	}
	output, err := os.OpenFile(target, os.O_CREATE|os.O_TRUNC|os.O_WRONLY, mode)
	if err != nil {
		return err
	}
	_, copyErr := io.Copy(output, input)
	syncErr := output.Sync()
	closeErr := output.Close()
	if copyErr != nil {
		return copyErr
	}
	if syncErr != nil {
		return syncErr
	}
	return closeErr
}

func safeMessage(err error) string {
	if err == nil {
		return ""
	}
	text := strings.ReplaceAll(err.Error(), "\n", " ")
	text = strings.ReplaceAll(text, "\r", " ")
	if len(text) > 300 {
		text = text[:300]
	}
	return text
}

var _ = downloadengine.DefaultMaxCacheBytes
