package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
)

const defaultDriveUploadEndpoint = "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable&fields=id,size,md5Checksum"

type driveSessionMetadata struct {
	Name    string   `json:"name"`
	Parents []string `json:"parents,omitempty"`
}

func (d *driveResumableHTTP) StartSession(ctx context.Context, name, parentID string, total int64) (string, error) {
	if d == nil {
		return "", fmt.Errorf("Drive client is required")
	}
	if strings.TrimSpace(d.AccessToken) == "" {
		return "", errDriveAuthRequired
	}
	name = strings.TrimSpace(name)
	parentID = strings.TrimSpace(parentID)
	if name == "" || strings.ContainsRune(name, '\x00') || strings.Contains(name, "/") {
		return "", fmt.Errorf("invalid Drive filename")
	}
	if total <= 0 {
		return "", fmt.Errorf("invalid Drive total size %d", total)
	}

	metadata := driveSessionMetadata{Name: name}
	if parentID != "" {
		metadata.Parents = []string{parentID}
	}
	body, err := json.Marshal(metadata)
	if err != nil {
		return "", fmt.Errorf("encode Drive upload metadata: %w", err)
	}

	endpoint := strings.TrimSpace(d.UploadEndpoint)
	if endpoint == "" {
		endpoint = defaultDriveUploadEndpoint
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, endpoint, bytes.NewReader(body))
	if err != nil {
		return "", fmt.Errorf("create Drive resumable session request: %w", err)
	}
	req.Header.Set("Authorization", "Bearer "+strings.TrimSpace(d.AccessToken))
	req.Header.Set("Content-Type", "application/json; charset=UTF-8")
	req.Header.Set("X-Upload-Content-Type", "application/octet-stream")
	req.Header.Set("X-Upload-Content-Length", fmt.Sprintf("%d", total))

	resp, err := d.httpClient().Do(req)
	if err != nil {
		return "", fmt.Errorf("start Drive resumable session: %w", err)
	}
	defer resp.Body.Close()
	_, _ = io.Copy(io.Discard, io.LimitReader(resp.Body, maxDriveResponseBytes))

	if resp.StatusCode == http.StatusUnauthorized || resp.StatusCode == http.StatusForbidden {
		return "", errDriveAuthRequired
	}
	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
		return "", fmt.Errorf("Drive resumable session creation returned HTTP %d", resp.StatusCode)
	}
	location := strings.TrimSpace(resp.Header.Get("Location"))
	if location == "" {
		return "", fmt.Errorf("Drive resumable session response omitted Location")
	}
	parsed, err := url.Parse(location)
	if err != nil || !parsed.IsAbs() || (parsed.Scheme != "https" && parsed.Scheme != "http") {
		return "", fmt.Errorf("Drive resumable session returned invalid Location")
	}
	if endpoint == defaultDriveUploadEndpoint && parsed.Scheme != "https" {
		return "", fmt.Errorf("Drive resumable session returned insecure Location")
	}
	return location, nil
}
