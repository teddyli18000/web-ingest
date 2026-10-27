package main

import (
	"context"
	"crypto/md5"
	"encoding"
	"encoding/base64"
	"encoding/hex"
	"fmt"
	"hash"
	"io"

	"github.com/teddyli18000/baidu-drive-mover/internal/baidu"
)

type relayHashState struct {
	Offset int64  `json:"offset"`
	State  string `json:"state"`
	MD5    string `json:"md5,omitempty"`
}

type teeReadCloser struct {
	io.Reader
	io.Closer
}

type hashingRangeSource struct {
	base      relayRangeSource
	hash      hash.Hash
	lastStart int64
	lastEnd   int64
	opened    bool
}

func (s *hashingRangeSource) OpenDownloadRange(ctx context.Context, remotePath string, start, end int64) (*baidu.DownloadStream, error) {
	stream, err := s.base.OpenDownloadRange(ctx, remotePath, start, end)
	if err != nil {
		return nil, err
	}
	s.lastStart = start
	s.lastEnd = end
	s.opened = true
	stream.Body = &teeReadCloser{Reader: io.TeeReader(stream.Body, s.hash), Closer: stream.Body}
	return stream, nil
}

func restoreRelayMD5(state string, offset int64) (hash.Hash, error) {
	if offset < 0 {
		return nil, fmt.Errorf("negative relay hash offset")
	}
	h := md5.New()
	if state == "" {
		if offset != 0 {
			return nil, fmt.Errorf("relay hash state missing at offset %d", offset)
		}
		return h, nil
	}
	data, err := base64.RawStdEncoding.DecodeString(state)
	if err != nil {
		return nil, fmt.Errorf("decode relay hash state: %w", err)
	}
	unmarshaler, ok := h.(encoding.BinaryUnmarshaler)
	if !ok {
		return nil, fmt.Errorf("MD5 implementation cannot restore state")
	}
	if err := unmarshaler.UnmarshalBinary(data); err != nil {
		return nil, fmt.Errorf("restore relay hash state: %w", err)
	}
	return h, nil
}

func marshalRelayMD5(h hash.Hash, offset int64) (relayHashState, error) {
	if h == nil || offset < 0 {
		return relayHashState{}, fmt.Errorf("invalid relay hash state")
	}
	marshaler, ok := h.(encoding.BinaryMarshaler)
	if !ok {
		return relayHashState{}, fmt.Errorf("MD5 implementation cannot persist state")
	}
	data, err := marshaler.MarshalBinary()
	if err != nil {
		return relayHashState{}, fmt.Errorf("persist relay hash state: %w", err)
	}
	return relayHashState{
		Offset: offset,
		State:  base64.RawStdEncoding.EncodeToString(data),
	}, nil
}

func syncRelayHashToOffset(
	ctx context.Context,
	source relayRangeSource,
	remotePath string,
	total int64,
	h hash.Hash,
	hashOffset *int64,
	target int64,
) error {
	if source == nil || h == nil || hashOffset == nil {
		return fmt.Errorf("relay hash synchronization is not configured")
	}
	if total < 0 || target < 0 || target > total {
		return fmt.Errorf("invalid relay hash target %d/%d", target, total)
	}
	if *hashOffset < 0 || *hashOffset > total {
		return fmt.Errorf("invalid relay hash offset %d/%d", *hashOffset, total)
	}
	if *hashOffset > target {
		h.Reset()
		*hashOffset = 0
	}
	for *hashOffset < target {
		if err := ctx.Err(); err != nil {
			return err
		}
		start := *hashOffset
		end := start + defaultRelayChunkBytes - 1
		if end >= target {
			end = target - 1
		}
		stream, err := source.OpenDownloadRange(ctx, remotePath, start, end)
		if err != nil {
			return fmt.Errorf("open Baidu hash catch-up range %d-%d: %w", start, end, err)
		}
		want := end - start + 1
		if stream.Start != start || stream.End != end || stream.Total != total || stream.Remaining != want {
			stream.Body.Close()
			return fmt.Errorf("Baidu hash catch-up range mismatch")
		}
		written, copyErr := io.CopyN(h, stream.Body, want)
		closeErr := stream.Body.Close()
		if copyErr != nil {
			return fmt.Errorf("hash Baidu catch-up range: %w", copyErr)
		}
		if written != want {
			return fmt.Errorf("hashed %d bytes, want %d", written, want)
		}
		if closeErr != nil {
			return fmt.Errorf("close Baidu hash catch-up stream: %w", closeErr)
		}
		*hashOffset = end + 1
	}
	return nil
}

// relayNextChunkHashed keeps an MD5 state exactly aligned with Drive's proven
// offset. The normal successful path hashes the same Baidu bytes while they are
// streamed to Drive. If a PUT is only partially committed, the speculative
// hash state is discarded and rebuilt only for the confirmed gap.
func relayNextChunkHashed(
	ctx context.Context,
	source relayRangeSource,
	drive relayDrive,
	spec relaySpec,
	persisted relayHashState,
) (relayResult, relayHashState, error) {
	before, err := drive.Status(ctx, spec.SessionURI, spec.Total)
	if err != nil {
		return relayResult{}, persisted, fmt.Errorf("query Drive before hashed relay: %w", err)
	}
	if err := validateDriveProgress(before, spec.Total); err != nil {
		return relayResult{}, persisted, err
	}
	h, err := restoreRelayMD5(persisted.State, persisted.Offset)
	if err != nil {
		return relayResult{}, persisted, err
	}
	hashOffset := persisted.Offset
	if err := syncRelayHashToOffset(ctx, source, spec.RemotePath, spec.Total, h, &hashOffset, before.NextOffset); err != nil {
		return relayResult{}, persisted, err
	}
	preState, err := marshalRelayMD5(h, hashOffset)
	if err != nil {
		return relayResult{}, persisted, err
	}
	if before.Complete || before.NextOffset == spec.Total {
		preState.MD5 = hex.EncodeToString(h.Sum(nil))
		return resultFromDrive(before), preState, nil
	}

	wrapped := &hashingRangeSource{base: source, hash: h}
	result, relayErr := relayNextChunk(ctx, wrapped, drive, spec)

	chunk := spec.ChunkBytes
	if chunk <= 0 {
		chunk = defaultRelayChunkBytes
	}
	expectedEnd := before.NextOffset + chunk
	if expectedEnd > spec.Total {
		expectedEnd = spec.Total
	}
	keepSpeculative := relayErr == nil && wrapped.opened && wrapped.lastStart == before.NextOffset && result.ConfirmedOffset == expectedEnd
	if keepSpeculative {
		hashOffset = result.ConfirmedOffset
	} else {
		h, err = restoreRelayMD5(preState.State, preState.Offset)
		if err != nil {
			return result, persisted, err
		}
		hashOffset = preState.Offset
		if err := syncRelayHashToOffset(ctx, source, spec.RemotePath, spec.Total, h, &hashOffset, result.ConfirmedOffset); err != nil {
			return result, persisted, err
		}
	}

	nextState, err := marshalRelayMD5(h, hashOffset)
	if err != nil {
		return result, persisted, err
	}
	if result.Complete && hashOffset == spec.Total {
		nextState.MD5 = hex.EncodeToString(h.Sum(nil))
	}
	return result, nextState, relayErr
}
