package state

import (
	"context"
	"fmt"
	"time"
)

// ActionProgress is the small, non-secret projection needed by the web-ingest
// control plane. It deliberately excludes paths, filenames, cookies and tokens.
type ActionProgress struct {
	FilesTotal int   `json:"files_total"`
	FilesDone  int   `json:"files_done"`
	BytesTotal int64 `json:"bytes_total"`
	BytesDone  int64 `json:"bytes_done"`
}

// ResetEphemeralCacheStates reconciles a persisted SQLite checkpoint with a
// fresh GitHub-hosted runner. Runner-local cache files are intentionally not
// persisted between jobs. Any pre-verification state that requires those bytes
// is therefore rewound to BAIDU_STAGED so the file can be downloaded again.
//
// drive_id is deliberately retained. If a previous upload committed remotely
// before the runner disappeared, the normal Drive reconciliation path can
// adopt and verify that exact object after the file is re-downloaded.
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
