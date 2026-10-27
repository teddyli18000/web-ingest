package main

import (
	"context"
	"crypto/md5"
	"encoding/hex"
	"errors"
	"fmt"
	"strings"
)

var errDriveDestinationConflict = errors.New("Drive destination requires reconciliation")

const (
	expiredSessionAbsent  = "absent"
	expiredSessionAdopted = "adopted"
)

// reconcileExpiredSession decides whether an expired resumable session already
// committed its final object. It never creates a replacement object itself.
// A caller may safely restart from byte zero only after this returns "absent".
func reconcileExpiredSession(
	ctx context.Context,
	source relayRangeSource,
	drive *driveResumableHTTP,
	input relayStepInput,
) (relayStepOutput, string, error) {
	files, err := drive.findExactNamedFiles(ctx, input.Name, input.DriveParentID)
	if err != nil {
		return relayStepOutput{}, "", fmt.Errorf("query Drive after expired resumable session: %w", err)
	}
	if len(files) == 0 {
		return relayStepOutput{}, expiredSessionAbsent, nil
	}
	if len(files) != 1 {
		return relayStepOutput{}, "", fmt.Errorf("%w: found %d same-name objects", errDriveDestinationConflict, len(files))
	}

	candidate := files[0]
	if candidate.Size != input.Size {
		return relayStepOutput{}, "", fmt.Errorf("%w: same-name object size %d does not match %d", errDriveDestinationConflict, candidate.Size, input.Size)
	}
	remoteMD5 := strings.ToLower(strings.TrimSpace(candidate.MD5Checksum))
	if !canonicalMD5.MatchString(remoteMD5) {
		return relayStepOutput{}, "", fmt.Errorf("%w: same-name object has no canonical MD5", errDriveDestinationConflict)
	}

	computed, err := computeBaiduFileMD5(ctx, source, input.BaiduStagingPath, input.Size)
	if err != nil {
		return relayStepOutput{}, "", fmt.Errorf("verify Baidu source after expired resumable session: %w", err)
	}
	if !strings.EqualFold(remoteMD5, computed) {
		return relayStepOutput{}, "", fmt.Errorf("%w: same-name Drive object MD5 does not match Baidu source", errDriveDestinationConflict)
	}
	if input.SourceMD5 != "" && !strings.EqualFold(input.SourceMD5, computed) {
		return relayStepOutput{}, "", fmt.Errorf("%w: computed source MD5 conflicts with canonical Baidu MD5", errDriveDestinationConflict)
	}
	if strings.TrimSpace(candidate.FileID) == "" {
		return relayStepOutput{}, "", fmt.Errorf("%w: same-name Drive object has no ID", errDriveDestinationConflict)
	}

	return relayStepOutput{
		ConfirmedOffset: input.Size,
		HashOffset:      input.Size,
		ComputedMD5:     computed,
		Complete:        true,
		DriveFileID:     strings.TrimSpace(candidate.FileID),
		DriveMD5:        remoteMD5,
	}, expiredSessionAdopted, nil
}

func computeBaiduFileMD5(ctx context.Context, source relayRangeSource, remotePath string, total int64) (string, error) {
	if source == nil || strings.TrimSpace(remotePath) == "" || total < 0 {
		return "", fmt.Errorf("invalid Baidu MD5 source")
	}
	if total == 0 {
		return emptyBlobMD5, nil
	}
	h := md5.New()
	offset := int64(0)
	if err := syncRelayHashToOffset(ctx, source, remotePath, total, h, &offset, total); err != nil {
		return "", err
	}
	if offset != total {
		return "", fmt.Errorf("hashed %d of %d source bytes", offset, total)
	}
	return hex.EncodeToString(h.Sum(nil)), nil
}
