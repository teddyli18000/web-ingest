package main

import (
	"bytes"
	"context"
	"crypto/md5"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"testing"

	"github.com/teddyli18000/baidu-drive-mover/internal/baidu"
)

type dataRangeSource struct {
	data  []byte
	calls [][2]int64
}

func (s *dataRangeSource) OpenDownloadRange(_ context.Context, _ string, start, end int64) (*baidu.DownloadStream, error) {
	if start < 0 || end < start || end >= int64(len(s.data)) {
		return nil, fmt.Errorf("invalid source range %d-%d", start, end)
	}
	s.calls = append(s.calls, [2]int64{start, end})
	payload := s.data[start : end+1]
	return &baidu.DownloadStream{
		Body:      io.NopCloser(bytes.NewReader(payload)),
		Start:     start,
		End:       end,
		Remaining: int64(len(payload)),
		Total:     int64(len(s.data)),
		Partial:   true,
	}, nil
}

func hashStateForPrefix(t *testing.T, data []byte, offset int64) relayHashState {
	t.Helper()
	if offset < 0 || offset > int64(len(data)) {
		t.Fatal("bad prefix offset")
	}
	h := md5.New()
	if _, err := h.Write(data[:offset]); err != nil {
		t.Fatal(err)
	}
	state, err := marshalRelayMD5(h, offset)
	if err != nil {
		t.Fatal(err)
	}
	return state
}

func digest(data []byte) string {
	sum := md5.Sum(data)
	return hex.EncodeToString(sum[:])
}

func digestFromState(t *testing.T, state relayHashState) string {
	t.Helper()
	h, err := restoreRelayMD5(state.State, state.Offset)
	if err != nil {
		t.Fatal(err)
	}
	return hex.EncodeToString(h.Sum(nil))
}

func TestRelayMD5StateRoundTrip(t *testing.T) {
	data := []byte("cross-vm resumable hash state")
	prefix := int64(11)
	state := hashStateForPrefix(t, data, prefix)
	h, err := restoreRelayMD5(state.State, state.Offset)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := h.Write(data[prefix:]); err != nil {
		t.Fatal(err)
	}
	if got := hex.EncodeToString(h.Sum(nil)); got != digest(data) {
		t.Fatalf("digest=%s want=%s", got, digest(data))
	}
}

func TestRelayNextChunkHashedUsesSameSuccessfulStream(t *testing.T) {
	const chunk = int64(256 << 10)
	data := bytes.Repeat([]byte("abcdefgh"), int(chunk/8))
	source := &dataRangeSource{data: data}
	drive := &fakeRelayDrive{
		statuses: []driveProgress{{NextOffset: 0}, {NextOffset: 0}},
		upload: driveProgress{
			NextOffset:  chunk,
			Complete:    true,
			FileID:      "drive-file",
			MD5Checksum: digest(data),
		},
	}
	result, state, err := relayNextChunkHashed(context.Background(), source, drive, relaySpec{
		RemotePath: "/BaiduDriveMover/task/b/file.bin",
		SessionURI: "https://upload.example/session",
		Total:      chunk,
		ChunkBytes: chunk,
	}, relayHashState{})
	if err != nil {
		t.Fatal(err)
	}
	if !result.Complete || result.ConfirmedOffset != chunk || state.Offset != chunk {
		t.Fatalf("result=%+v state=%+v", result, state)
	}
	if state.MD5 != digest(data) {
		t.Fatalf("md5=%s want=%s", state.MD5, digest(data))
	}
	if len(source.calls) != 1 || source.calls[0] != [2]int64{0, chunk - 1} {
		t.Fatalf("expected one source stream, got %+v", source.calls)
	}
}

func TestRelayHashCatchesUpOnlyDriveConfirmedGap(t *testing.T) {
	const chunk = int64(256 << 10)
	data := make([]byte, chunk*2)
	for i := range data {
		data[i] = byte(i % 251)
	}
	persisted := hashStateForPrefix(t, data, chunk)
	remote := chunk + 1000
	source := &dataRangeSource{data: data}
	drive := &fakeRelayDrive{
		statuses: []driveProgress{{NextOffset: remote}, {NextOffset: remote}},
		upload: driveProgress{
			NextOffset:  int64(len(data)),
			Complete:    true,
			FileID:      "drive-file",
			MD5Checksum: digest(data),
		},
	}
	result, state, err := relayNextChunkHashed(context.Background(), source, drive, relaySpec{
		RemotePath: "/BaiduDriveMover/task/b/file.bin",
		SessionURI: "https://upload.example/session",
		Total:      int64(len(data)),
		ChunkBytes: chunk,
	}, persisted)
	if err != nil {
		t.Fatal(err)
	}
	if !result.Complete || state.Offset != int64(len(data)) || state.MD5 != digest(data) {
		t.Fatalf("result=%+v state=%+v", result, state)
	}
	if len(source.calls) != 2 {
		t.Fatalf("source calls=%+v", source.calls)
	}
	if source.calls[0] != [2]int64{chunk, remote - 1} {
		t.Fatalf("catch-up range=%v", source.calls[0])
	}
	if source.calls[1] != [2]int64{remote, int64(len(data)) - 1} {
		t.Fatalf("relay range=%v", source.calls[1])
	}
}

func TestRelayHashDiscardsSpeculationAfterPartialCommit(t *testing.T) {
	const chunk = int64(256 << 10)
	data := bytes.Repeat([]byte{7}, int(chunk*2))
	confirmed := int64(12345)
	source := &dataRangeSource{data: data}
	drive := &fakeRelayDrive{
		statuses: []driveProgress{
			{NextOffset: 0},
			{NextOffset: 0},
			{NextOffset: confirmed},
		},
		uploadErr: errors.New("connection reset"),
	}
	result, state, err := relayNextChunkHashed(context.Background(), source, drive, relaySpec{
		RemotePath: "/BaiduDriveMover/task/b/file.bin",
		SessionURI: "https://upload.example/session",
		Total:      int64(len(data)),
		ChunkBytes: chunk,
	}, relayHashState{})
	var interrupted *relayInterruptedError
	if !errors.As(err, &interrupted) {
		t.Fatalf("expected reconciled interruption, got %v", err)
	}
	if result.ConfirmedOffset != confirmed || state.Offset != confirmed {
		t.Fatalf("result=%+v state=%+v", result, state)
	}
	if len(source.calls) != 2 || source.calls[0] != [2]int64{0, chunk - 1} || source.calls[1] != [2]int64{0, confirmed - 1} {
		t.Fatalf("expected speculative range then confirmed catch-up, got %+v", source.calls)
	}
	if got := digestFromState(t, state); got != digest(data[:confirmed]) {
		t.Fatalf("prefix digest=%s want=%s", got, digest(data[:confirmed]))
	}
}

func TestRelayHashRebuildsWhenDriveIsBehindCheckpoint(t *testing.T) {
	const chunk = int64(256 << 10)
	data := make([]byte, chunk*2)
	for i := range data {
		data[i] = byte((i * 7) % 253)
	}
	persisted := hashStateForPrefix(t, data, chunk)
	remote := int64(4096)
	source := &dataRangeSource{data: data}
	drive := &fakeRelayDrive{
		statuses: []driveProgress{{NextOffset: remote}, {NextOffset: remote}},
		upload:   driveProgress{NextOffset: remote + chunk},
	}
	result, state, err := relayNextChunkHashed(context.Background(), source, drive, relaySpec{
		RemotePath: "/BaiduDriveMover/task/b/file.bin",
		SessionURI: "https://upload.example/session",
		Total:      int64(len(data)),
		ChunkBytes: chunk,
	}, persisted)
	if err != nil {
		t.Fatal(err)
	}
	if result.ConfirmedOffset != remote+chunk || state.Offset != remote+chunk {
		t.Fatalf("result=%+v state=%+v", result, state)
	}
	if len(source.calls) != 2 || source.calls[0] != [2]int64{0, remote - 1} {
		t.Fatalf("expected rebuild from zero, got %+v", source.calls)
	}
	if got := digestFromState(t, state); got != digest(data[:remote+chunk]) {
		t.Fatalf("digest=%s want=%s", got, digest(data[:remote+chunk]))
	}
}
