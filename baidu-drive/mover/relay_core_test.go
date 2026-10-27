package main

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/teddyli18000/baidu-drive-mover/internal/baidu"
)

type fakeRelaySource struct {
	calls [][2]int64
	total int64
	bad   bool
}

func (s *fakeRelaySource) OpenDownloadRange(_ context.Context, _ string, start, end int64) (*baidu.DownloadStream, error) {
	s.calls = append(s.calls, [2]int64{start, end})
	length := end - start + 1
	streamStart := start
	if s.bad {
		streamStart++
	}
	return &baidu.DownloadStream{
		Body:      io.NopCloser(io.LimitReader(&zeroReader{}, length)),
		Start:     streamStart,
		End:       end,
		Remaining: length,
		Total:     s.total,
		Partial:   true,
	}, nil
}

type zeroReader struct{}

func (*zeroReader) Read(p []byte) (int, error) {
	for i := range p {
		p[i] = 0
	}
	return len(p), nil
}

type fakeRelayDrive struct {
	statuses  []driveProgress
	statusErr error
	upload    driveProgress
	uploadErr error
	calls     int
	bodyBytes int64
	rangeSeen [3]int64
}

func (d *fakeRelayDrive) Status(_ context.Context, _ string, _ int64) (driveProgress, error) {
	if d.statusErr != nil {
		return driveProgress{}, d.statusErr
	}
	if len(d.statuses) == 0 {
		return driveProgress{}, fmt.Errorf("unexpected status call")
	}
	value := d.statuses[0]
	d.statuses = d.statuses[1:]
	return value, nil
}

func (d *fakeRelayDrive) Upload(_ context.Context, _ string, start, end, total int64, body io.Reader) (driveProgress, error) {
	d.calls++
	d.rangeSeen = [3]int64{start, end, total}
	n, err := io.Copy(io.Discard, body)
	if err != nil {
		return driveProgress{}, err
	}
	d.bodyBytes = n
	return d.upload, d.uploadErr
}

func TestRelayNextChunkStreamsExactWindow(t *testing.T) {
	const chunk = int64(256 << 10)
	source := &fakeRelaySource{total: chunk * 3}
	drive := &fakeRelayDrive{
		statuses: []driveProgress{{NextOffset: chunk}},
		upload:   driveProgress{NextOffset: chunk * 2},
	}
	result, err := relayNextChunk(context.Background(), source, drive, relaySpec{
		RemotePath: "/BaiduDriveMover/task/b/file.bin",
		SessionURI: "https://upload.example/session",
		Total:      chunk * 3,
		ChunkBytes: chunk,
	})
	if err != nil {
		t.Fatal(err)
	}
	if result.ConfirmedOffset != chunk*2 || result.Complete {
		t.Fatalf("unexpected result %+v", result)
	}
	if len(source.calls) != 1 || source.calls[0] != [2]int64{chunk, chunk*2 - 1} {
		t.Fatalf("unexpected source ranges %+v", source.calls)
	}
	if drive.rangeSeen != [3]int64{chunk, chunk*2 - 1, chunk * 3} || drive.bodyBytes != chunk {
		t.Fatalf("unexpected Drive call range=%v bytes=%d", drive.rangeSeen, drive.bodyBytes)
	}
}

func TestRelayNextChunkFinalChunkCanBeShort(t *testing.T) {
	const chunk = int64(256 << 10)
	total := chunk + 17
	source := &fakeRelaySource{total: total}
	drive := &fakeRelayDrive{
		statuses: []driveProgress{{NextOffset: chunk}},
		upload: driveProgress{
			NextOffset:  total,
			Complete:    true,
			FileID:      "drive-file",
			MD5Checksum: "0123456789abcdef0123456789abcdef",
		},
	}
	result, err := relayNextChunk(context.Background(), source, drive, relaySpec{
		RemotePath: "/BaiduDriveMover/task/b/file.bin",
		SessionURI: "https://upload.example/session",
		Total:      total,
		ChunkBytes: chunk,
	})
	if err != nil {
		t.Fatal(err)
	}
	if !result.Complete || result.ConfirmedOffset != total || result.FileID != "drive-file" {
		t.Fatalf("unexpected result %+v", result)
	}
	if drive.bodyBytes != 17 {
		t.Fatalf("final body bytes=%d", drive.bodyBytes)
	}
}

func TestRelayUploadFailureReconcilesDriveTruth(t *testing.T) {
	const chunk = int64(256 << 10)
	source := &fakeRelaySource{total: chunk * 4}
	drive := &fakeRelayDrive{
		statuses: []driveProgress{
			{NextOffset: chunk},
			{NextOffset: chunk + 12345},
		},
		uploadErr: errors.New("connection reset"),
	}
	result, err := relayNextChunk(context.Background(), source, drive, relaySpec{
		RemotePath: "/BaiduDriveMover/task/b/file.bin",
		SessionURI: "https://upload.example/session",
		Total:      chunk * 4,
		ChunkBytes: chunk,
	})
	var interrupted *relayInterruptedError
	if !errors.As(err, &interrupted) {
		t.Fatalf("expected reconciled interruption, got %v", err)
	}
	if result.ConfirmedOffset != chunk+12345 {
		t.Fatalf("confirmed offset=%d", result.ConfirmedOffset)
	}
}

func TestRelayRejectsMismatchedBaiduRange(t *testing.T) {
	const chunk = int64(256 << 10)
	source := &fakeRelaySource{total: chunk * 2, bad: true}
	drive := &fakeRelayDrive{statuses: []driveProgress{{NextOffset: 0}}}
	_, err := relayNextChunk(context.Background(), source, drive, relaySpec{
		RemotePath: "/BaiduDriveMover/task/b/file.bin",
		SessionURI: "https://upload.example/session",
		Total:      chunk * 2,
		ChunkBytes: chunk,
	})
	if err == nil || !strings.Contains(err.Error(), "range mismatch") {
		t.Fatalf("unexpected error %v", err)
	}
	if drive.calls != 0 {
		t.Fatalf("Drive upload called %d times", drive.calls)
	}
}

func TestRelayRejectsUnalignedNonFinalChunkPolicy(t *testing.T) {
	err := validateRelaySpec(relaySpec{
		RemotePath: "/BaiduDriveMover/task/b/file.bin",
		SessionURI: "https://upload.example/session",
		Total:      1 << 30,
		ChunkBytes: (256 << 10) + 1,
	})
	if err == nil {
		t.Fatal("expected chunk alignment error")
	}
}

func TestDriveHTTPStatusParsesRemoteOffset(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPut || r.Header.Get("Content-Range") != "bytes */100" || r.ContentLength != 0 {
			t.Fatalf("unexpected request method=%s range=%q length=%d", r.Method, r.Header.Get("Content-Range"), r.ContentLength)
		}
		if r.Header.Get("Authorization") != "Bearer token" {
			t.Fatalf("missing authorization header")
		}
		w.Header().Set("Range", "bytes=0-41")
		w.WriteHeader(driveResumeIncomplete)
	}))
	defer server.Close()

	client := &driveResumableHTTP{Client: server.Client(), AccessToken: "token"}
	progress, err := client.Status(context.Background(), server.URL, 100)
	if err != nil {
		t.Fatal(err)
	}
	if progress.NextOffset != 42 || progress.Complete {
		t.Fatalf("unexpected progress %+v", progress)
	}
}

func TestDriveHTTPUploadStreamsBodyAndHeaders(t *testing.T) {
	payload := bytes.Repeat([]byte{7}, 256<<10)
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("Content-Range") != fmt.Sprintf("bytes 0-%d/%d", len(payload)-1, len(payload)*2) {
			t.Fatalf("range=%q", r.Header.Get("Content-Range"))
		}
		if r.ContentLength != int64(len(payload)) {
			t.Fatalf("content length=%d", r.ContentLength)
		}
		data, err := io.ReadAll(r.Body)
		if err != nil || !bytes.Equal(data, payload) {
			t.Fatalf("body mismatch err=%v bytes=%d", err, len(data))
		}
		w.Header().Set("Range", fmt.Sprintf("bytes=0-%d", len(payload)-1))
		w.WriteHeader(driveResumeIncomplete)
	}))
	defer server.Close()

	client := &driveResumableHTTP{Client: server.Client()}
	progress, err := client.Upload(
		context.Background(), server.URL,
		0, int64(len(payload)-1), int64(len(payload)*2), bytes.NewReader(payload),
	)
	if err != nil {
		t.Fatal(err)
	}
	if progress.NextOffset != int64(len(payload)) {
		t.Fatalf("next offset=%d", progress.NextOffset)
	}
}

func TestDriveHTTPFinalResponseCarriesVerificationMetadata(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprint(w, `{"id":"abc","size":"17","md5Checksum":"0123456789abcdef0123456789abcdef"}`)
	}))
	defer server.Close()

	client := &driveResumableHTTP{Client: server.Client()}
	progress, err := client.Upload(context.Background(), server.URL, 0, 16, 17, strings.NewReader("0123456789abcdefg"))
	if err != nil {
		t.Fatal(err)
	}
	if !progress.Complete || progress.NextOffset != 17 || progress.FileID != "abc" || progress.Size != 17 {
		t.Fatalf("unexpected progress %+v", progress)
	}
}

func TestDriveHTTPExpiredSessionIsTyped(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusNotFound)
	}))
	defer server.Close()

	client := &driveResumableHTTP{Client: server.Client()}
	_, err := client.Status(context.Background(), server.URL, 100)
	if !errors.Is(err, errDriveSessionExpired) {
		t.Fatalf("expected expired session, got %v", err)
	}
}

func TestParseDriveNextOffsetMissingRangeMeansZero(t *testing.T) {
	next, err := parseDriveNextOffset("", 100)
	if err != nil || next != 0 {
		t.Fatalf("next=%d err=%v", next, err)
	}
}
