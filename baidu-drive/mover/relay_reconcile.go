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
	destinationAbsent  = "absent"
	destinationAdopted = "adopted"
)

// expectedSourceMD5 returns source evidence strong enough to adopt an existing
// Drive object. Prefer already verified source/hash evidence; only re-read the
// whole Baidu object when neither is available.
func expectedSourceMD5(ctx context.Context, source relayRangeSource, input relayStepInput) (string, error) {
	if input.Size == 0 {
		return emptyBlobMD5, nil
	}
	if value := strings.ToLower(strings.TrimSpace(input.SourceMD5)); canonicalMD5.MatchString(value) {
		return value, nil
	}
	if input.HashOffset == input.Size {
		if value := strings.ToLower(strings.TrimSpace(input.ComputedMD5)); canonicalMD5.MatchString(value) {
			return value, nil
		}
	}
	return computeBaiduFileMD5(ctx, source, input.BaiduStagingPath, input.Size)
}

func validateExistingDestination(ctx context.Context, source relayRangeSource, input relayStepInput, files []driveProgress) (relayStepOutput, bool, error) {
	if len(files) == 0 {
		return relayStepOutput{}, false, nil
	}
	if len(files) != 1 {
		return relayStepOutput{}, false, fmt.Errorf("%w: found %d same-name objects", errDriveDestinationConflict, len(files))
	}
	candidate := files[0]
	if candidate.Size != input.Size {
		return relayStepOutput{}, false, fmt.Errorf("%w: same-name object size %d does not match %d", errDriveDestinationConflict, candidate.Size, input.Size)
	}
	remoteMD5 := strings.ToLower(strings.TrimSpace(candidate.MD5Checksum))
	if !canonicalMD5.MatchString(remoteMD5) {
		return relayStepOutput{}, false, fmt.Errorf("%w: same-name object has no canonical MD5", errDriveDestinationConflict)
	}
	expected, err := expectedSourceMD5(ctx, source, input)
	if err != nil {
		return relayStepOutput{}, false, fmt.Errorf("verify source for Drive destination reconciliation: %w", err)
	}
	if !strings.EqualFold(remoteMD5, expected) {
		return relayStepOutput{}, false, fmt.Errorf("%w: same-name Drive object MD5 does not match source", errDriveDestinationConflict)
	}
	if strings.TrimSpace(candidate.FileID) == "" {
		return relayStepOutput{}, false, fmt.Errorf("%w: same-name Drive object has no ID", errDriveDestinationConflict)
	}
	return relayStepOutput{
		ConfirmedOffset: input.Size,
		HashOffset:      input.Size,
		ComputedMD5:     expected,
		Complete:        true,
		DriveFileID:     strings.TrimSpace(candidate.FileID),
		DriveMD5:        remoteMD5,
	}, true, nil
}

// reconcileDestinationBeforeCreate is the only gate allowed before starting a
// new resumable session. It uses two successful absence proofs separated by a
// bounded delay. If a final object appears, it is adopted only after exact
// size+MD5 verification; duplicates or conflicts stop without replay.
func reconcileDestinationBeforeCreate(
	ctx context.Context,
	source relayRangeSource,
	drive *driveResumableHTTP,
	input relayStepInput,
) (relayStepOutput, string, error) {
	for pass := 0; pass < 2; pass++ {
		files, err := drive.findExactNamedFiles(ctx, input.Name, input.DriveParentID)
		if err != nil {
			return relayStepOutput{}, "", fmt.Errorf("query Drive destination before session creation: %w", err)
		}
		if adopted, ok, err := validateExistingDestination(ctx, source, input, files); err != nil || ok {
			if ok {
				return adopted, destinationAdopted, nil
			}
			return relayStepOutput{}, "", err
		}
		if pass == 0 {
			if err := drive.waitForReconcile(ctx); err != nil {
				return relayStepOutput{}, "", err
			}
		}
	}
	return relayStepOutput{}, destinationAbsent, nil
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
