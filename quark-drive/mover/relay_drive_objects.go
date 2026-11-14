package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"strings"
)

const (
	defaultDriveFilesEndpoint = "https://www.googleapis.com/drive/v3/files"
	emptyBlobMD5              = "d41d8cd98f00b204e9800998ecf8427e"
)

type driveListedFile struct {
	ID          string `json:"id"`
	Name        string `json:"name"`
	Size        string `json:"size"`
	MD5Checksum string `json:"md5Checksum"`
	MimeType    string `json:"mimeType"`
}

type driveFileList struct {
	Files         []driveListedFile `json:"files"`
	NextPageToken string            `json:"nextPageToken"`
}

type driveCreateMetadata struct {
	Name     string   `json:"name"`
	Parents  []string `json:"parents,omitempty"`
	MimeType string   `json:"mimeType"`
}

func validateDriveObjectName(name string) (string, error) {
	name = strings.TrimSpace(name)
	if name == "" || strings.ContainsRune(name, '\x00') || strings.Contains(name, "/") {
		return "", fmt.Errorf("invalid Drive filename")
	}
	return name, nil
}

// filesEndpoint uses the official endpoint in production. Tests already set
// UploadEndpoint to a local server, so derive the same origin without adding a
// second mutable test-only field to the Drive client.
func (d *driveResumableHTTP) filesEndpoint() string {
	if d != nil && strings.TrimSpace(d.UploadEndpoint) != "" {
		if parsed, err := url.Parse(strings.TrimSpace(d.UploadEndpoint)); err == nil && parsed.IsAbs() {
			return parsed.Scheme + "://" + parsed.Host + "/drive/v3/files"
		}
	}
	return defaultDriveFilesEndpoint
}

func driveQueryLiteral(value string) string {
	value = strings.ReplaceAll(value, `\`, `\\`)
	return strings.ReplaceAll(value, `'`, `\'`)
}

func (d *driveResumableHTTP) findExactNamedFiles(ctx context.Context, name, parentID string) ([]driveProgress, error) {
	if d == nil || strings.TrimSpace(d.AccessToken) == "" {
		return nil, errDriveAuthRequired
	}
	var err error
	name, err = validateDriveObjectName(name)
	if err != nil {
		return nil, err
	}
	parentID = strings.TrimSpace(parentID)
	if parentID == "" {
		return nil, fmt.Errorf("Drive parent ID is required")
	}

	endpoint, err := url.Parse(d.filesEndpoint())
	if err != nil {
		return nil, fmt.Errorf("parse Drive files endpoint: %w", err)
	}
	query := endpoint.Query()
	query.Set("q", fmt.Sprintf("'%s' in parents and name = '%s' and trashed = false", driveQueryLiteral(parentID), driveQueryLiteral(name)))
	query.Set("spaces", "drive")
	query.Set("pageSize", "10")
	query.Set("fields", "nextPageToken,files(id,name,size,md5Checksum,mimeType)")
	endpoint.RawQuery = query.Encode()

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, endpoint.String(), nil)
	if err != nil {
		return nil, fmt.Errorf("create Drive reconciliation request: %w", err)
	}
	d.authorize(req)
	resp, err := d.httpClient().Do(req)
	if err != nil {
		return nil, fmt.Errorf("list Drive destination objects: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode == http.StatusUnauthorized || resp.StatusCode == http.StatusForbidden {
		return nil, errDriveAuthRequired
	}
	if resp.StatusCode != http.StatusOK {
		_, _ = io.Copy(io.Discard, io.LimitReader(resp.Body, maxDriveResponseBytes))
		return nil, fmt.Errorf("Drive destination reconciliation returned HTTP %d", resp.StatusCode)
	}
	data, err := io.ReadAll(io.LimitReader(resp.Body, maxDriveResponseBytes+1))
	if err != nil {
		return nil, fmt.Errorf("read Drive reconciliation response: %w", err)
	}
	if int64(len(data)) > maxDriveResponseBytes {
		return nil, fmt.Errorf("Drive reconciliation response is too large")
	}
	var listed driveFileList
	if err := json.Unmarshal(data, &listed); err != nil {
		return nil, fmt.Errorf("parse Drive reconciliation response: %w", err)
	}
	if strings.TrimSpace(listed.NextPageToken) != "" {
		return nil, fmt.Errorf("Drive destination name is too ambiguous to reconcile safely")
	}
	result := make([]driveProgress, 0, len(listed.Files))
	for _, item := range listed.Files {
		if item.Name != name {
			continue
		}
		if strings.TrimSpace(item.ID) == "" {
			return nil, fmt.Errorf("Drive destination object has no ID")
		}
		size, err := strconv.ParseInt(strings.TrimSpace(item.Size), 10, 64)
		if err != nil || size < 0 {
			return nil, fmt.Errorf("Drive destination object has invalid size")
		}
		result = append(result, driveProgress{
			NextOffset:  size,
			Complete:    true,
			FileID:      strings.TrimSpace(item.ID),
			Size:        size,
			MD5Checksum: strings.ToLower(strings.TrimSpace(item.MD5Checksum)),
		})
	}
	return result, nil
}

func verifiedEmptyCandidate(files []driveProgress) (driveProgress, bool, error) {
	if len(files) == 0 {
		return driveProgress{}, false, nil
	}
	if len(files) != 1 {
		return driveProgress{}, false, fmt.Errorf("Drive destination contains %d same-name objects", len(files))
	}
	file := files[0]
	if file.Size != 0 || !strings.EqualFold(file.MD5Checksum, emptyBlobMD5) {
		return driveProgress{}, false, fmt.Errorf("same-name Drive object is not the expected empty blob")
	}
	if strings.TrimSpace(file.FileID) == "" {
		return driveProgress{}, false, fmt.Errorf("empty Drive object has no ID")
	}
	file.NextOffset = 0
	file.Complete = true
	file.MD5Checksum = emptyBlobMD5
	return file, true, nil
}

func (d *driveResumableHTTP) CreateOrAdoptEmpty(ctx context.Context, name, parentID string) (driveProgress, error) {
	if d == nil || strings.TrimSpace(d.AccessToken) == "" {
		return driveProgress{}, errDriveAuthRequired
	}
	name, err := validateDriveObjectName(name)
	if err != nil {
		return driveProgress{}, err
	}
	parentID = strings.TrimSpace(parentID)
	if parentID == "" {
		return driveProgress{}, fmt.Errorf("Drive parent ID is required")
	}

	existing, err := d.findExactNamedFiles(ctx, name, parentID)
	if err != nil {
		return driveProgress{}, err
	}
	if candidate, ok, err := verifiedEmptyCandidate(existing); err != nil || ok {
		return candidate, err
	}

	metadata, err := json.Marshal(driveCreateMetadata{
		Name: name, Parents: []string{parentID}, MimeType: "application/octet-stream",
	})
	if err != nil {
		return driveProgress{}, fmt.Errorf("encode empty Drive metadata: %w", err)
	}
	endpoint, err := url.Parse(d.filesEndpoint())
	if err != nil {
		return driveProgress{}, fmt.Errorf("parse Drive create endpoint: %w", err)
	}
	query := endpoint.Query()
	query.Set("fields", "id,size,md5Checksum")
	endpoint.RawQuery = query.Encode()
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, endpoint.String(), bytes.NewReader(metadata))
	if err != nil {
		return driveProgress{}, fmt.Errorf("create empty Drive request: %w", err)
	}
	d.authorize(req)
	req.Header.Set("Content-Type", "application/json; charset=UTF-8")
	resp, requestErr := d.httpClient().Do(req)
	if requestErr == nil {
		progress, parseErr := parseDriveResponse(resp, 0)
		if parseErr == nil {
			if candidate, ok, verifyErr := verifiedEmptyCandidate([]driveProgress{progress}); verifyErr != nil || ok {
				return candidate, verifyErr
			}
		}
		requestErr = parseErr
	}

	// A transport failure can happen after Drive committed the metadata create.
	// Reconcile the exact task-root name once before allowing any retry so an
	// uncertain response cannot create duplicate empty files.
	existing, reconcileErr := d.findExactNamedFiles(ctx, name, parentID)
	if reconcileErr == nil {
		if candidate, ok, verifyErr := verifiedEmptyCandidate(existing); verifyErr != nil || ok {
			return candidate, verifyErr
		}
	}
	if requestErr == nil {
		requestErr = errors.New("empty Drive create returned no verifiable object")
	}
	if reconcileErr != nil {
		return driveProgress{}, fmt.Errorf("empty Drive create failed and reconciliation failed: %v; %w", requestErr, reconcileErr)
	}
	return driveProgress{}, fmt.Errorf("create empty Drive file: %w", requestErr)
}
