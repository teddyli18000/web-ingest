package main

import (
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strings"

	"github.com/teddyli18000/baidu-drive-mover/internal/baidu"
)

var canonicalMD5 = regexp.MustCompile(`^[0-9a-fA-F]{32}$`)

type relayStepInput struct {
	TaskID           string `json:"task_id"`
	FileID           string `json:"file_id"`
	Name             string `json:"name"`
	Size             int64  `json:"size"`
	SourceMD5        string `json:"md5,omitempty"`
	BaiduStagingPath string `json:"baidu_staging_path"`
	DriveParentID    string `json:"drive_parent_id"`
	SessionSealed    string `json:"session_sealed,omitempty"`
	HashOffset       int64  `json:"hash_offset"`
	MD5State         string `json:"md5_state,omitempty"`
	ComputedMD5      string `json:"computed_md5,omitempty"`
}

type relayStepOutput struct {
	SessionSealed    string `json:"session_sealed,omitempty"`
	ConfirmedOffset int64  `json:"confirmed_offset"`
	HashOffset      int64  `json:"hash_offset"`
	MD5State        string `json:"md5_state,omitempty"`
	ComputedMD5     string `json:"computed_md5,omitempty"`
	Complete        bool   `json:"complete"`
	DriveFileID     string `json:"drive_file_id,omitempty"`
	DriveMD5        string `json:"drive_md5,omitempty"`
	ErrorKind       string `json:"error_kind,omitempty"`
	Message         string `json:"message,omitempty"`
}

func main() {
	os.Exit(runRelayStepCommand())
}

func runRelayStepCommand() int {
	fs := flag.NewFlagSet("baidu-drive-relay", flag.ContinueOnError)
	fs.SetOutput(os.Stderr)
	inputPath := fs.String("input-json", "", "runner-local relay state input")
	outputPath := fs.String("output-json", "", "runner-local relay step output")
	cookiePath := fs.String("baidu-cookie-file", "", "runner-local Baidu cookie file")
	tokenPath := fs.String("drive-access-token-file", "", "runner-local Drive access token file")
	keyPath := fs.String("state-key-file", "", "runner-local base64 AES-256 state key file")
	if err := fs.Parse(os.Args[1:]); err != nil {
		return 2
	}
	if fs.NArg() != 0 || strings.TrimSpace(*inputPath) == "" || strings.TrimSpace(*outputPath) == "" || strings.TrimSpace(*cookiePath) == "" || strings.TrimSpace(*tokenPath) == "" || strings.TrimSpace(*keyPath) == "" {
		fmt.Fprintln(os.Stderr, "input-json, output-json, baidu-cookie-file, drive-access-token-file and state-key-file are required")
		return 2
	}
	input, err := readRelayStepInput(*inputPath)
	if err != nil {
		return writeRelayStepFailure(*outputPath, "input", err)
	}
	cookie, err := readSecretFile(*cookiePath, 1<<20, "Baidu session")
	if err != nil {
		return writeRelayStepFailure(*outputPath, "auth", err)
	}
	accessToken, err := readSecretFile(*tokenPath, 1<<20, "Drive access token")
	if err != nil {
		return writeRelayStepFailure(*outputPath, "auth", err)
	}
	stateKey, err := readSecretFile(*keyPath, 4096, "relay state key")
	if err != nil {
		return writeRelayStepFailure(*outputPath, "auth", err)
	}
	output, runErr := runRelayStep(context.Background(), input, cookie, accessToken, stateKey)
	if runErr != nil {
		if output.ErrorKind == "" {
			output.ErrorKind = classifyRelayStepError(runErr)
		}
		output.Message = relaySafeMessage(runErr)
	}
	if err := writeRelayStepOutput(*outputPath, output); err != nil {
		fmt.Fprintln(os.Stderr, "write relay result:", relaySafeMessage(err))
		return 1
	}
	if runErr != nil {
		fmt.Fprintln(os.Stderr, "relay step stopped safely:", relaySafeMessage(runErr))
		return 1
	}
	return 0
}

func runRelayStep(ctx context.Context, input relayStepInput, cookie, accessToken, stateKey string) (relayStepOutput, error) {
	if strings.TrimSpace(input.TaskID) == "" || strings.TrimSpace(input.FileID) == "" {
		return relayStepOutput{}, fmt.Errorf("task and file IDs are required")
	}
	if strings.TrimSpace(input.Name) == "" || strings.TrimSpace(input.BaiduStagingPath) == "" || strings.TrimSpace(input.DriveParentID) == "" {
		return relayStepOutput{}, fmt.Errorf("relay file metadata is incomplete")
	}
	if input.Size < 0 {
		return relayStepOutput{}, fmt.Errorf("file size cannot be negative")
	}
	if input.HashOffset < 0 || input.HashOffset > input.Size {
		return relayStepOutput{}, fmt.Errorf("invalid hash offset %d/%d", input.HashOffset, input.Size)
	}
	if input.SourceMD5 != "" && !canonicalMD5.MatchString(input.SourceMD5) {
		return relayStepOutput{}, fmt.Errorf("source MD5 is not canonical")
	}

	drive := &driveResumableHTTP{AccessToken: strings.TrimSpace(accessToken)}
	if input.Size == 0 {
		file, err := drive.CreateOrAdoptEmpty(ctx, input.Name, input.DriveParentID)
		if err != nil {
			if errors.Is(err, errDriveAuthRequired) {
				return relayStepOutput{ErrorKind: "auth"}, err
			}
			return relayStepOutput{ErrorKind: "retryable"}, err
		}
		if strings.TrimSpace(file.FileID) == "" || !strings.EqualFold(file.MD5Checksum, emptyBlobMD5) {
			return relayStepOutput{}, fmt.Errorf("empty Drive object failed independent verification")
		}
		if input.SourceMD5 != "" && !strings.EqualFold(input.SourceMD5, emptyBlobMD5) {
			return relayStepOutput{}, fmt.Errorf("empty source MD5 does not match the empty blob digest")
		}
		return relayStepOutput{
			ConfirmedOffset: 0,
			HashOffset:      0,
			ComputedMD5:     emptyBlobMD5,
			Complete:        true,
			DriveFileID:     strings.TrimSpace(file.FileID),
			DriveMD5:        emptyBlobMD5,
		}, nil
	}

	source, err := baidu.NewClient(cookie)
	if err != nil {
		return relayStepOutput{}, fmt.Errorf("create Baidu relay client: %w", err)
	}
	if !source.HasLoginCookies() {
		return relayStepOutput{ErrorKind: "auth"}, baidu.ErrAuthRequired
	}

	sessionURI := ""
	sealed := strings.TrimSpace(input.SessionSealed)
	if sealed == "" {
		sessionURI, err = drive.StartSession(ctx, input.Name, input.DriveParentID, input.Size)
		if err != nil {
			return relayStepOutput{}, fmt.Errorf("start Drive resumable upload: %w", err)
		}
		sealed, err = sealCapability(stateKey, input.TaskID, input.FileID, sessionURI)
		if err != nil {
			return relayStepOutput{}, fmt.Errorf("seal Drive resumable session: %w", err)
		}
	} else {
		sessionURI, err = openCapability(stateKey, input.TaskID, input.FileID, sealed)
		if err != nil {
			return relayStepOutput{SessionSealed: sealed, ErrorKind: "state"}, err
		}
	}

	persisted := relayHashState{Offset: input.HashOffset, State: input.MD5State, MD5: input.ComputedMD5}
	result, hashState, relayErr := relayNextChunkHashed(ctx, source, drive, relaySpec{
		RemotePath: input.BaiduStagingPath,
		SessionURI: sessionURI,
		Total:      input.Size,
		ChunkBytes: defaultRelayChunkBytes,
	}, persisted)
	output := relayStepOutput{
		SessionSealed:    sealed,
		ConfirmedOffset: result.ConfirmedOffset,
		HashOffset:      hashState.Offset,
		MD5State:        hashState.State,
		ComputedMD5:     hashState.MD5,
		Complete:        result.Complete,
		DriveFileID:     strings.TrimSpace(result.FileID),
		DriveMD5:        strings.ToLower(strings.TrimSpace(result.MD5Checksum)),
	}
	if relayErr != nil {
		if errors.Is(relayErr, errDriveSessionExpired) {
			output.ErrorKind = "session_expired"
		} else if errors.Is(relayErr, errDriveAuthRequired) || errors.Is(relayErr, baidu.ErrAuthRequired) {
			output.ErrorKind = "auth"
		} else {
			output.ErrorKind = "retryable"
		}
		return output, relayErr
	}
	if !result.Complete {
		return output, nil
	}
	if output.DriveFileID == "" {
		return output, fmt.Errorf("completed Drive upload returned no file ID")
	}
	if !canonicalMD5.MatchString(output.DriveMD5) {
		return output, fmt.Errorf("completed Drive upload returned no canonical MD5")
	}
	if !canonicalMD5.MatchString(output.ComputedMD5) {
		return output, fmt.Errorf("completed source stream has no canonical MD5")
	}
	if !strings.EqualFold(output.DriveMD5, output.ComputedMD5) {
		return output, fmt.Errorf("Drive MD5 does not match streamed source MD5")
	}
	if input.SourceMD5 != "" && !strings.EqualFold(input.SourceMD5, output.ComputedMD5) {
		return output, fmt.Errorf("streamed MD5 does not match canonical Baidu MD5")
	}
	return output, nil
}

func classifyRelayStepError(err error) string {
	if err == nil {
		return ""
	}
	if errors.Is(err, errDriveSessionExpired) {
		return "session_expired"
	}
	if errors.Is(err, errDriveAuthRequired) || errors.Is(err, baidu.ErrAuthRequired) {
		return "auth"
	}
	return "retryable"
}

func readRelayStepInput(path string) (relayStepInput, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return relayStepInput{}, fmt.Errorf("read relay input: %w", err)
	}
	if len(data) > 1<<20 {
		return relayStepInput{}, fmt.Errorf("relay input is too large")
	}
	var input relayStepInput
	if err := json.Unmarshal(data, &input); err != nil {
		return relayStepInput{}, fmt.Errorf("parse relay input: %w", err)
	}
	return input, nil
}

func readSecretFile(path string, limit int64, label string) (string, error) {
	file, err := os.Open(path)
	if err != nil {
		return "", fmt.Errorf("open %s: %w", label, err)
	}
	defer file.Close()
	data, err := io.ReadAll(io.LimitReader(file, limit+1))
	if err != nil {
		return "", fmt.Errorf("read %s: %w", label, err)
	}
	if int64(len(data)) > limit {
		return "", fmt.Errorf("%s is too large", label)
	}
	value := strings.TrimSpace(string(data))
	if value == "" {
		return "", fmt.Errorf("%s is empty", label)
	}
	return value, nil
}

func writeRelayStepOutput(path string, output relayStepOutput) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return err
	}
	data, err := json.MarshalIndent(output, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o600)
}

func writeRelayStepFailure(path, kind string, err error) int {
	_ = writeRelayStepOutput(path, relayStepOutput{ErrorKind: kind, Message: relaySafeMessage(err)})
	fmt.Fprintln(os.Stderr, "relay step setup failed:", relaySafeMessage(err))
	return 1
}

func relaySafeMessage(err error) string {
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
