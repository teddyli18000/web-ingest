package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"regexp"
	"strconv"
	"strings"

	"github.com/teddyli18000/baidu-drive-mover/internal/baidu"
)

const (
	driveResumeIncomplete = 308
	driveChunkQuantum      = int64(256 << 10)
	defaultRelayChunkBytes = int64(512 << 20)
	maxDriveResponseBytes  = int64(1 << 20)
)

var (
	errDriveSessionExpired = errors.New("Drive resumable session expired")
	errDriveAuthRequired   = errors.New("Drive authorization required")
	driveRangePattern      = regexp.MustCompile(`^bytes=0-([0-9]+)$`)
)

type relayRangeSource interface {
	OpenDownloadRange(ctx context.Context, remotePath string, start, end int64) (*baidu.DownloadStream, error)
}

type driveProgress struct {
	NextOffset  int64
	Complete    bool
	FileID      string
	Size        int64
	MD5Checksum string
}

type relayDrive interface {
	Status(ctx context.Context, sessionURI string, total int64) (driveProgress, error)
	Upload(ctx context.Context, sessionURI string, start, end, total int64, body io.Reader) (driveProgress, error)
}

type relaySpec struct {
	RemotePath string
	SessionURI string
	Total      int64
	ChunkBytes int64
}

type relayResult struct {
	ConfirmedOffset int64
	Complete        bool
	FileID          string
	MD5Checksum     string
}

type relayInterruptedError struct {
	Cause error
}

func (e *relayInterruptedError) Error() string {
	if e == nil || e.Cause == nil {
		return "relay upload interrupted"
	}
	return "relay upload interrupted; Drive state reconciled: " + e.Cause.Error()
}

func (e *relayInterruptedError) Unwrap() error {
	if e == nil {
		return nil
	}
	return e.Cause
}

func validateRelaySpec(spec relaySpec) error {
	if strings.TrimSpace(spec.RemotePath) == "" {
		return fmt.Errorf("Baidu staged path is required")
	}
	if strings.TrimSpace(spec.SessionURI) == "" {
		return fmt.Errorf("Drive resumable session is required")
	}
	if spec.Total <= 0 {
		return fmt.Errorf("file size must be positive")
	}
	chunk := spec.ChunkBytes
	if chunk <= 0 {
		chunk = defaultRelayChunkBytes
	}
	if chunk%driveChunkQuantum != 0 {
		return fmt.Errorf("non-final Drive chunk size must be a multiple of 256 KiB")
	}
	return nil
}

func relayNextChunk(ctx context.Context, source relayRangeSource, drive relayDrive, spec relaySpec) (relayResult, error) {
	if source == nil || drive == nil {
		return relayResult{}, fmt.Errorf("relay source and Drive client are required")
	}
	if err := validateRelaySpec(spec); err != nil {
		return relayResult{}, err
	}
	chunk := spec.ChunkBytes
	if chunk <= 0 {
		chunk = defaultRelayChunkBytes
	}

	before, err := drive.Status(ctx, spec.SessionURI, spec.Total)
	if err != nil {
		return relayResult{}, fmt.Errorf("query Drive resumable state: %w", err)
	}
	if err := validateDriveProgress(before, spec.Total); err != nil {
		return relayResult{}, err
	}
	if before.Complete || before.NextOffset == spec.Total {
		return resultFromDrive(before), nil
	}

	start := before.NextOffset
	end := start + chunk - 1
	if end >= spec.Total {
		end = spec.Total - 1
	}

	stream, err := source.OpenDownloadRange(ctx, spec.RemotePath, start, end)
	if err != nil {
		return resultFromDrive(before), fmt.Errorf("open Baidu relay range %d-%d: %w", start, end, err)
	}
	defer stream.Body.Close()

	want := end - start + 1
	if stream.Start != start || stream.End != end || stream.Total != spec.Total || stream.Remaining != want {
		return resultFromDrive(before), fmt.Errorf(
			"Baidu relay range mismatch: got %d-%d/%d (%d bytes), want %d-%d/%d (%d bytes)",
			stream.Start, stream.End, stream.Total, stream.Remaining,
			start, end, spec.Total, want,
		)
	}

	// The Baidu response body becomes the Drive request body directly. The
	// Drive client sets Content-Length=want, so neither a chunk-sized file nor a
	// chunk-sized in-memory buffer is needed on the runner.
	after, uploadErr := drive.Upload(ctx, spec.SessionURI, start, end, spec.Total, io.LimitReader(stream.Body, want))
	if uploadErr == nil {
		if err := validateDriveProgress(after, spec.Total); err != nil {
			return resultFromDrive(before), err
		}
		if after.NextOffset < start || after.NextOffset > end+1 {
			return resultFromDrive(before), fmt.Errorf("Drive confirmed impossible offset %d after range %d-%d", after.NextOffset, start, end)
		}
		if after.Complete && end != spec.Total-1 {
			return resultFromDrive(before), fmt.Errorf("Drive reported completion after non-final range %d-%d", start, end)
		}
		return resultFromDrive(after), nil
	}

	// Never infer progress from bytes read locally. A failed PUT may have
	// committed none, some, or all of the request. Ask Drive and return that
	// proven state to the scheduler.
	reconciled, statusErr := drive.Status(ctx, spec.SessionURI, spec.Total)
	if statusErr != nil {
		return resultFromDrive(before), fmt.Errorf("Drive upload failed and status reconciliation failed: %v; %w", uploadErr, statusErr)
	}
	if err := validateDriveProgress(reconciled, spec.Total); err != nil {
		return resultFromDrive(before), err
	}
	return resultFromDrive(reconciled), &relayInterruptedError{Cause: uploadErr}
}

func validateDriveProgress(progress driveProgress, total int64) error {
	if total <= 0 {
		return fmt.Errorf("invalid total size %d", total)
	}
	if progress.NextOffset < 0 || progress.NextOffset > total {
		return fmt.Errorf("Drive confirmed offset %d outside file size %d", progress.NextOffset, total)
	}
	if progress.Complete && progress.NextOffset != total {
		return fmt.Errorf("Drive reported complete at offset %d of %d", progress.NextOffset, total)
	}
	return nil
}

func resultFromDrive(progress driveProgress) relayResult {
	return relayResult{
		ConfirmedOffset: progress.NextOffset,
		Complete:        progress.Complete,
		FileID:          progress.FileID,
		MD5Checksum:     progress.MD5Checksum,
	}
}

type driveResumableHTTP struct {
	Client         *http.Client
	AccessToken    string
	UploadEndpoint string
}

func (d *driveResumableHTTP) httpClient() *http.Client {
	if d != nil && d.Client != nil {
		return d.Client
	}
	return http.DefaultClient
}

func (d *driveResumableHTTP) Status(ctx context.Context, sessionURI string, total int64) (driveProgress, error) {
	if total <= 0 {
		return driveProgress{}, fmt.Errorf("invalid Drive total size %d", total)
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPut, sessionURI, nil)
	if err != nil {
		return driveProgress{}, fmt.Errorf("create Drive status request: %w", err)
	}
	req.ContentLength = 0
	req.Header.Set("Content-Range", fmt.Sprintf("bytes */%d", total))
	d.authorize(req)
	resp, err := d.httpClient().Do(req)
	if err != nil {
		return driveProgress{}, fmt.Errorf("query Drive upload status: %w", err)
	}
	return parseDriveResponse(resp, total)
}

func (d *driveResumableHTTP) Upload(ctx context.Context, sessionURI string, start, end, total int64, body io.Reader) (driveProgress, error) {
	if start < 0 || end < start || total <= end {
		return driveProgress{}, fmt.Errorf("invalid Drive upload range %d-%d/%d", start, end, total)
	}
	length := end - start + 1
	if end != total-1 && length%driveChunkQuantum != 0 {
		return driveProgress{}, fmt.Errorf("non-final Drive chunk length %d is not a multiple of 256 KiB", length)
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPut, sessionURI, body)
	if err != nil {
		return driveProgress{}, fmt.Errorf("create Drive upload request: %w", err)
	}
	req.ContentLength = length
	req.Header.Set("Content-Type", "application/octet-stream")
	req.Header.Set("Content-Range", fmt.Sprintf("bytes %d-%d/%d", start, end, total))
	d.authorize(req)
	resp, err := d.httpClient().Do(req)
	if err != nil {
		return driveProgress{}, fmt.Errorf("upload Drive range %d-%d: %w", start, end, err)
	}
	return parseDriveResponse(resp, total)
}

func (d *driveResumableHTTP) authorize(req *http.Request) {
	if d == nil || req == nil {
		return
	}
	if token := strings.TrimSpace(d.AccessToken); token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
}

type driveFileResponse struct {
	ID          string `json:"id"`
	Size        string `json:"size"`
	MD5Checksum string `json:"md5Checksum"`
}

func parseDriveResponse(resp *http.Response, total int64) (driveProgress, error) {
	if resp == nil {
		return driveProgress{}, fmt.Errorf("nil Drive response")
	}
	defer resp.Body.Close()

	switch resp.StatusCode {
	case driveResumeIncomplete:
		next, err := parseDriveNextOffset(resp.Header.Get("Range"), total)
		if err != nil {
			return driveProgress{}, err
		}
		_, _ = io.Copy(io.Discard, io.LimitReader(resp.Body, maxDriveResponseBytes))
		return driveProgress{NextOffset: next}, nil
	case http.StatusOK, http.StatusCreated:
		data, err := io.ReadAll(io.LimitReader(resp.Body, maxDriveResponseBytes))
		if err != nil {
			return driveProgress{}, fmt.Errorf("read final Drive response: %w", err)
		}
		var file driveFileResponse
		if len(strings.TrimSpace(string(data))) != 0 {
			if err := json.Unmarshal(data, &file); err != nil {
				return driveProgress{}, fmt.Errorf("parse final Drive response: %w", err)
			}
		}
		size := total
		if strings.TrimSpace(file.Size) != "" {
			parsed, err := strconv.ParseInt(file.Size, 10, 64)
			if err != nil || parsed < 0 {
				return driveProgress{}, fmt.Errorf("invalid Drive final size %q", file.Size)
			}
			size = parsed
			if size != total {
				return driveProgress{}, fmt.Errorf("Drive final size %d does not match expected %d", size, total)
			}
		}
		return driveProgress{
			NextOffset:  total,
			Complete:    true,
			FileID:      strings.TrimSpace(file.ID),
			Size:        size,
			MD5Checksum: strings.TrimSpace(file.MD5Checksum),
		}, nil
	case http.StatusNotFound:
		_, _ = io.Copy(io.Discard, io.LimitReader(resp.Body, maxDriveResponseBytes))
		return driveProgress{}, errDriveSessionExpired
	case http.StatusUnauthorized, http.StatusForbidden:
		_, _ = io.Copy(io.Discard, io.LimitReader(resp.Body, maxDriveResponseBytes))
		return driveProgress{}, errDriveAuthRequired
	default:
		_, _ = io.Copy(io.Discard, io.LimitReader(resp.Body, maxDriveResponseBytes))
		return driveProgress{}, fmt.Errorf("Drive resumable request returned HTTP %d", resp.StatusCode)
	}
}

func parseDriveNextOffset(header string, total int64) (int64, error) {
	header = strings.TrimSpace(header)
	if header == "" {
		return 0, nil
	}
	match := driveRangePattern.FindStringSubmatch(header)
	if len(match) != 2 {
		return 0, fmt.Errorf("invalid Drive Range header %q", header)
	}
	last, err := strconv.ParseInt(match[1], 10, 64)
	if err != nil || last < 0 || last >= total {
		return 0, fmt.Errorf("invalid Drive Range header %q", header)
	}
	return last + 1, nil
}
