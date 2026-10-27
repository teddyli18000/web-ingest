package state

import (
	"context"
	"fmt"
	"strings"
	"time"
)

// ActionProgress is the small, non-secret projection needed by the web-ingest
// control plane. It deliberately excludes credentials and capability URLs.
type ActionProgress struct {
	FilesTotal int   `json:"files_total"`
	FilesDone  int   `json:"files_done"`
	BytesTotal int64 `json:"bytes_total"`
	BytesDone  int64 `json:"bytes_done"`
}

// ActionRelayFile is the public, non-secret handoff from the serialized mover
// checkpoint to one independently scheduled relay worker.
type ActionRelayFile struct {
	FileID           string `json:"file_id"`
	BatchID          string `json:"batch_id"`
	LogicalPath      string `json:"logical_path"`
	ParentPath       string `json:"parent_path"`
	Name             string `json:"name"`
	Size             int64  `json:"size"`
	MD5              string `json:"md5,omitempty"`
	BaiduStagingPath string `json:"baidu_staging_path"`
	DriveParentID    string `json:"drive_parent_id"`
}

type ActionRelayVerification struct {
	FileID  string `json:"file_id"`
	DriveID string `json:"drive_id"`
}

// ResetEphemeralCacheStates reconciles a persisted SQLite checkpoint with a
// fresh GitHub-hosted runner. Runner-local cache files are intentionally not
// persisted between jobs. Any legacy cache-backed pre-verification state is
// therefore rewound to BAIDU_STAGED.
func (s *Store) ResetEphemeralCacheStates(ctx context.Context, taskID string) error {
	if s == nil || s.db == nil {
		return fmt.Errorf("state store is not open")
	}
	now := time.Now().UTC().Format(time.RFC3339Nano)
	_, err := s.db.ExecContext(ctx, `
UPDATE files
SET status = ?, local_cache_path = '', last_error = '', updated_at = ?
WHERE task_id = ? AND status IN (?, ?, ?, ?)`,
		FileBaiduStaged, now, taskID,
		FileDownloading, FileLocalReady, FileDriveUploading, FileDriveUploaded,
	)
	if err != nil {
		return fmt.Errorf("reset ephemeral Action cache states: %w", err)
	}
	return nil
}

// ActionRelayFiles returns only files already proven to exist in the
// tool-owned Baidu staging area. Drive parent IDs must already be reconciled by
// the tree builder. Nothing returned here is a credential or signed URL.
func (s *Store) ActionRelayFiles(ctx context.Context, taskID string) ([]ActionRelayFile, error) {
	if s == nil || s.db == nil {
		return nil, fmt.Errorf("state store is not open")
	}
	rows, err := s.db.QueryContext(ctx, `
SELECT f.file_id, bf.batch_id, f.logical_path, f.parent_path, f.name, f.size, f.md5,
       f.baidu_staging_path,
       CASE WHEN f.parent_path = '/' THEN t.drive_root_id ELSE COALESCE(d.drive_id, '') END
FROM files f
JOIN tasks t ON t.id = f.task_id
JOIN batch_files bf ON bf.task_id = f.task_id AND bf.file_id = f.file_id
LEFT JOIN directories d ON d.task_id = f.task_id AND d.logical_path = f.parent_path
WHERE f.task_id = ? AND f.status = ?
ORDER BY bf.batch_id, bf.ordinal`, taskID, FileBaiduStaged)
	if err != nil {
		return nil, fmt.Errorf("query Action relay files: %w", err)
	}
	defer rows.Close()
	var result []ActionRelayFile
	for rows.Next() {
		var file ActionRelayFile
		if err := rows.Scan(
			&file.FileID, &file.BatchID, &file.LogicalPath, &file.ParentPath, &file.Name,
			&file.Size, &file.MD5, &file.BaiduStagingPath, &file.DriveParentID,
		); err != nil {
			return nil, fmt.Errorf("scan Action relay file: %w", err)
		}
		if strings.TrimSpace(file.FileID) == "" || strings.TrimSpace(file.BatchID) == "" || strings.TrimSpace(file.Name) == "" {
			return nil, fmt.Errorf("relay file has incomplete durable identity")
		}
		if file.Size < 0 {
			return nil, fmt.Errorf("relay file %q has negative size", file.FileID)
		}
		if strings.TrimSpace(file.BaiduStagingPath) == "" {
			return nil, fmt.Errorf("relay file %q has no Baidu staging path", file.FileID)
		}
		if strings.TrimSpace(file.DriveParentID) == "" {
			return nil, fmt.Errorf("relay file %q has no reconciled Drive parent ID", file.FileID)
		}
		result = append(result, file)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate Action relay files: %w", err)
	}
	return result, nil
}

// ApplyActionRelayVerifications imports independently verified Drive results
// from file workers back into the serialized mover checkpoint. The relay path
// intentionally has no local full-file cache; local_cache_path is set to the
// normal opaque expected path solely so the existing cleanup provenance gate
// can treat an already-missing runner-local file as idempotently cleaned.
func (s *Store) ApplyActionRelayVerifications(ctx context.Context, taskID string, values []ActionRelayVerification) error {
	if s == nil || s.db == nil {
		return fmt.Errorf("state store is not open")
	}
	if len(values) == 0 {
		return nil
	}
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return fmt.Errorf("begin relay verification import: %w", err)
	}
	defer tx.Rollback()
	now := time.Now().UTC().Format(time.RFC3339Nano)
	seen := make(map[string]struct{}, len(values))
	for _, value := range values {
		fileID := strings.TrimSpace(value.FileID)
		driveID := strings.TrimSpace(value.DriveID)
		if fileID == "" || driveID == "" {
			return fmt.Errorf("relay verification requires file and Drive IDs")
		}
		if _, exists := seen[fileID]; exists {
			return fmt.Errorf("duplicate relay verification for file %q", fileID)
		}
		seen[fileID] = struct{}{}

		var status FileStatus
		var existingDriveID, logicalPath string
		if err := tx.QueryRowContext(ctx, `
SELECT status, drive_id, logical_path FROM files WHERE task_id = ? AND file_id = ?`, taskID, fileID).Scan(
			&status, &existingDriveID, &logicalPath,
		); err != nil {
			return fmt.Errorf("read relay file %q: %w", fileID, err)
		}
		if status == FileDriveVerified || status == FileCleanupPending || status == FileDone {
			if existingDriveID != driveID {
				return fmt.Errorf("relay file %q Drive ID changed from %q to %q", fileID, existingDriveID, driveID)
			}
			continue
		}
		if status != FileBaiduStaged {
			return fmt.Errorf("relay file %q is not importable from %s", fileID, status)
		}
		if existingDriveID != "" && existingDriveID != driveID {
			return fmt.Errorf("relay file %q Drive ID conflicts with persisted ID", fileID)
		}
		expectedLocal, err := expectedLocalCachePath(taskID, fileID)
		if err != nil {
			return err
		}
		if _, err := tx.ExecContext(ctx, `
UPDATE files
SET status = ?, local_cache_path = ?, drive_id = ?, last_error = '', updated_at = ?
WHERE task_id = ? AND file_id = ? AND status = ?`,
			FileDriveVerified, expectedLocal, driveID, now, taskID, fileID, FileBaiduStaged,
		); err != nil {
			return fmt.Errorf("persist relay verification for %q: %w", fileID, err)
		}
		if _, err := tx.ExecContext(ctx, `
INSERT INTO owned_objects(task_id, scope, object_id, object_path, cleanup_allowed, created_at)
VALUES(?, 'drive_file', ?, ?, 0, ?)
ON CONFLICT(task_id, scope, object_id) DO UPDATE SET object_path = excluded.object_path`,
			taskID, driveID, logicalPath, now,
		); err != nil {
			return fmt.Errorf("register relay Drive provenance for %q: %w", fileID, err)
		}
	}
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("commit relay verification import: %w", err)
	}
	return nil
}

// ActionProgressForTask returns aggregate progress safe for the public Release
// status projection. DONE is the only completed state because destination
// verification and cleanup must both have succeeded before a file reaches it.
func (s *Store) ActionProgressForTask(ctx context.Context, taskID string) (ActionProgress, error) {
	if s == nil || s.db == nil {
		return ActionProgress{}, fmt.Errorf("state store is not open")
	}
	var value ActionProgress
	err := s.db.QueryRowContext(ctx, `
SELECT COUNT(*),
       COALESCE(SUM(size), 0),
       COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0),
       COALESCE(SUM(CASE WHEN status = ? THEN size ELSE 0 END), 0)
FROM files
WHERE task_id = ?`, FileDone, FileDone, taskID).Scan(
		&value.FilesTotal,
		&value.BytesTotal,
		&value.FilesDone,
		&value.BytesDone,
	)
	if err != nil {
		return ActionProgress{}, fmt.Errorf("query Action progress: %w", err)
	}
	return value, nil
}
