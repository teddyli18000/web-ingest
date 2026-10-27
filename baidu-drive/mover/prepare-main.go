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
	runtimepath "github.com/teddyli18000/baidu-drive-mover/internal/runtime"
	"github.com/teddyli18000/baidu-drive-mover/internal/state"
)

type prepareBlockedBrowser struct{}

func (prepareBlockedBrowser) Login(context.Context) (string, error) {
	return "", errors.New("interactive Baidu login is disabled in the Actions relay bridge")
}

type prepareResult struct {
	MoverTaskID   string               `json:"mover_task_id,omitempty"`
	Status        string               `json:"status,omitempty"`
	ScanCompleted bool                 `json:"scan_completed"`
	DriveRootID   string               `json:"drive_root_id,omitempty"`
	DriveRootName string               `json:"drive_root_name,omitempty"`
	Progress      state.ActionProgress `json:"progress"`
	LastError     string               `json:"last_error,omitempty"`
}

func main() {
	os.Exit(runPrepare())
}

func runPrepare() int {
	fs := flag.NewFlagSet("baidu-drive-prepare", flag.ContinueOnError)
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
	relayManifestJSON := fs.String("relay-manifest-json", "", "public relay manifest output path")
	relayResultsJSON := fs.String("relay-results-json", "", "optional verified relay results input path")
	stageWindowBytes := fs.Int64("stage-window-bytes", defaultRelayStageWindowBytes, "maximum aggregate bytes in a normal staged batch")
	if err := fs.Parse(os.Args[1:]); err != nil {
		return 2
	}
	if fs.NArg() != 0 || strings.TrimSpace(*runtimeBase) == "" || strings.TrimSpace(*stateDBPath) == "" || strings.TrimSpace(*resultJSON) == "" || strings.TrimSpace(*relayManifestJSON) == "" {
		fmt.Fprintln(os.Stderr, "runtime-base, state-db, result-json and relay-manifest-json are required")
		return 2
	}
	if strings.TrimSpace(*resumeTaskID) == "" && strings.TrimSpace(*shareURL) == "" {
		fmt.Fprintln(os.Stderr, "share-url is required when no mover task is being resumed")
		return 2
	}
	if *stageWindowBytes <= 0 {
		fmt.Fprintln(os.Stderr, "stage-window-bytes must be positive")
		return 2
	}

	layout, err := runtimepath.New(*runtimeBase)
	if err != nil {
		return prepareFailBeforeStore(*resultJSON, fmt.Errorf("create runtime layout: %w", err))
	}
	if err := layout.Ensure(); err != nil {
		return prepareFailBeforeStore(*resultJSON, fmt.Errorf("initialize runtime layout: %w", err))
	}
	if err := prepareRestoreOptional(*stateDBPath, layout.StateDB, 0o600); err != nil {
		return prepareFailBeforeStore(*resultJSON, fmt.Errorf("restore state checkpoint: %w", err))
	}
	if err := prepareRequireAndCopy(*baiduCookieFile, filepath.Join(layout.Auth, "baidu.cookies"), 0o600, "Baidu session"); err != nil {
		return prepareFailBeforeStore(*resultJSON, err)
	}
	if err := prepareRequireAndCopy(*rcloneConfigFile, layout.RcloneConfig, 0o600, "Google Drive rclone config"); err != nil {
		return prepareFailBeforeStore(*resultJSON, err)
	}
	if err := prepareRequireAndCopy(*rcloneBinary, layout.RcloneExe, 0o700, "rclone executable"); err != nil {
		return prepareFailBeforeStore(*resultJSON, err)
	}

	store, err := state.Open(layout.StateDB)
	if err != nil {
		return prepareFailBeforeStore(*resultJSON, fmt.Errorf("open state checkpoint: %w", err))
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
			return prepareFinish(store, &closed, layout, *stateDBPath, *resultJSON, moverTaskID, err)
		}
	}

	cookieStore := baidu.NewCookieStore(layout)
	browser := prepareBlockedBrowser{}
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
	if err == nil {
		err = runRelayPreparation(ctx, moverTaskID, relayPrepareConfig{
			Layout:            layout,
			Store:             store,
			CookieStore:       cookieStore,
			Browser:           browser,
			Logger:            logger,
			RelayResultsPath:  *relayResultsJSON,
			RelayManifestPath: *relayManifestJSON,
			StageWindowBytes:  *stageWindowBytes,
		})
	}
	return prepareFinish(store, &closed, layout, *stateDBPath, *resultJSON, moverTaskID, err)
}

func prepareFinish(store *state.Store, closed *bool, layout *runtimepath.Layout, checkpointPath, resultPath, moverTaskID string, runErr error) int {
	result := prepareResult{MoverTaskID: moverTaskID}
	if moverTaskID != "" {
		if task, err := store.GetTask(context.Background(), moverTaskID); err == nil {
			result.Status = string(task.Status)
			result.ScanCompleted = task.ScanCompleted
			result.DriveRootID = task.DriveRootID
			result.DriveRootName = task.DriveRootName
			if runErr == nil {
				result.LastError = task.LastError
			}
		}
		if progress, err := store.ActionProgressForTask(context.Background(), moverTaskID); err == nil {
			result.Progress = progress
		}
	}
	if runErr != nil {
		result.LastError = prepareSafeMessage(runErr)
	}
	closeErr := store.Close()
	*closed = true
	if closeErr != nil && runErr == nil {
		runErr = fmt.Errorf("close state database: %w", closeErr)
		result.LastError = prepareSafeMessage(runErr)
	}
	if err := prepareCopyFile(layout.StateDB, checkpointPath, 0o600); err != nil && runErr == nil {
		runErr = fmt.Errorf("persist state checkpoint: %w", err)
		result.LastError = prepareSafeMessage(runErr)
	}
	if err := prepareWriteResult(resultPath, result); err != nil {
		fmt.Fprintln(os.Stderr, "write result:", err)
		return 1
	}
	if runErr != nil {
		fmt.Fprintln(os.Stderr, "relay preparation stopped safely:", prepareSafeMessage(runErr))
		return 1
	}
	return 0
}

func prepareFailBeforeStore(resultPath string, err error) int {
	_ = prepareWriteResult(resultPath, prepareResult{LastError: prepareSafeMessage(err)})
	fmt.Fprintln(os.Stderr, "relay preparation setup failed:", prepareSafeMessage(err))
	return 1
}

func prepareWriteResult(path string, result prepareResult) error {
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

func prepareRestoreOptional(source, target string, mode os.FileMode) error {
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
	return prepareCopyFile(source, target, mode)
}

func prepareRequireAndCopy(source, target string, mode os.FileMode, label string) error {
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
	return prepareCopyFile(source, target, mode)
}

func prepareCopyFile(source, target string, mode os.FileMode) error {
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

func prepareSafeMessage(err error) string {
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
