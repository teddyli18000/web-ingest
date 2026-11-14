package main

import (
 "context"
 "encoding/json"
 "errors"
 "fmt"
 "io"
 "net/http"
 "net/url"
 "path"
 "regexp"
 "strconv"
 "strings"
 "time"

 "github.com/teddyli18000/baidu-drive-mover/internal/baidu"
)

const baiduSourceSegmentBytes int64 = 4 << 20
const baiduWebUserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
var baiduContentRange = regexp.MustCompile(`^bytes ([0-9]+)-([0-9]+)/([0-9]+)$`)
var errBaiduDownloadDenied = errors.New("Baidu denied an authenticated download")

type stagedFileLister interface {
 ListStagingDirectory(context.Context, string) ([]baidu.RemoteFile, error)
}

type baiduSignedRangeSource struct {
 staging stagedFileLister
 cookie string
 transport *http.Client
 fileSize int64
 signedURL string
}

func signedBaiduHost(u *url.URL) bool {
 if u == nil || u.Scheme != "https" || u.User != nil || u.Port() != "" { return false }
 host := strings.ToLower(u.Hostname())
 return host == "d.pcs.baidu.com" || strings.HasSuffix(host, ".baidupcs.com")
}

func newBaiduSignedRangeSource(staging stagedFileLister, cookie string, size int64) *baiduSignedRangeSource {
 return &baiduSignedRangeSource{
  staging: staging, cookie: cookie, fileSize: size,
  transport: &http.Client{
   Timeout: 5 * time.Minute,
   CheckRedirect: func(req *http.Request, via []*http.Request) error {
    if !signedBaiduHost(req.URL) || len(via) >= 5 { return errBaiduDownloadDenied }
    req.Header.Del("Cookie")
    req.Header.Del("Authorization")
    req.Header.Del("Referer")
    return nil
   },
  },
 }
}

func (s *baiduSignedRangeSource) resolve(ctx context.Context, remotePath string) (string, error) {
 if s.signedURL != "" { return s.signedURL, nil }
 if remotePath == "/BaiduDriveMover" || !strings.HasPrefix(remotePath, "/BaiduDriveMover/") || path.Clean(remotePath) != remotePath {
  return "", fmt.Errorf("Baidu source path is not tool-owned")
 }
 files, err := s.staging.ListStagingDirectory(ctx, path.Dir(remotePath))
 if err != nil { return "", fmt.Errorf("list tool-owned Baidu stage: %w", err) }
 var fsID int64
 for _, file := range files {
  if file.Path == remotePath {
   if file.IsDir || file.FsID <= 0 || file.Size != s.fileSize { return "", fmt.Errorf("Baidu stage identity does not match") }
   fsID = file.FsID
   break
  }
 }
 if fsID == 0 { return "", fmt.Errorf("Baidu staged file was not found") }
 values := url.Values{}
 values.Set("fsids", fmt.Sprintf("[%d]", fsID))
 values.Set("dlink", "1")
 req, err := http.NewRequestWithContext(ctx, http.MethodGet, "https://pan.baidu.com/api/filemetas?"+values.Encode(), nil)
 if err != nil { return "", err }
 req.Header.Set("Cookie", s.cookie)
 req.Header.Set("User-Agent", baiduWebUserAgent)
 req.Header.Set("Referer", "https://pan.baidu.com/disk/home")
 metadataClient := *s.transport
 metadataClient.Timeout = 45 * time.Second
 metadataClient.CheckRedirect = func(_ *http.Request, _ []*http.Request) error { return http.ErrUseLastResponse }
 resp, err := metadataClient.Do(req)
 if err != nil { return "", fmt.Errorf("query Baidu filemetas: %w", err) }
 defer resp.Body.Close()
 if resp.StatusCode == http.StatusUnauthorized || resp.StatusCode == http.StatusForbidden { return "", errBaiduDownloadDenied }
 if resp.StatusCode != http.StatusOK {
  if resp.StatusCode < 500 { return "", fmt.Errorf("%w (filemetas HTTP %d)", errBaiduDownloadDenied, resp.StatusCode) }
  return "", fmt.Errorf("Baidu filemetas returned HTTP %d", resp.StatusCode)
 }
 raw, err := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
 if err != nil { return "", fmt.Errorf("read Baidu filemetas: %w", err) }
 var payload struct {
  Errno int `json:"errno"`
  Info []struct { FsID int64 `json:"fs_id"`; Dlink string `json:"dlink"` } `json:"info"`
 }
 if err := json.Unmarshal(raw, &payload); err != nil { return "", fmt.Errorf("decode Baidu filemetas: %w", err) }
 if payload.Errno != 0 {
  if payload.Errno == -6 || payload.Errno == -7 || payload.Errno == 9019 { return "", baidu.ErrAuthRequired }
  return "", fmt.Errorf("%w (filemetas errno %d)", errBaiduDownloadDenied, payload.Errno)
 }
 if len(payload.Info) != 1 || payload.Info[0].FsID != fsID { return "", fmt.Errorf("Baidu filemetas identity mismatch") }
 u, err := url.Parse(payload.Info[0].Dlink)
 if err != nil || !signedBaiduHost(u) { return "", fmt.Errorf("Baidu filemetas returned an untrusted download origin") }
 s.signedURL = u.String()
 return s.signedURL, nil
}

func (s *baiduSignedRangeSource) OpenDownloadRange(ctx context.Context, remotePath string, start, end int64) (*baidu.DownloadStream, error) {
 if start < 0 || end < start || end >= s.fileSize { return nil, fmt.Errorf("invalid source range") }
 link, err := s.resolve(ctx, remotePath)
 if err != nil { return nil, err }
 reader := &baiduSegmentedReader{ctx:ctx, client:s.transport, signedURL:link, position:start, end:end, total:s.fileSize}
 if err := reader.openNext(); err != nil { return nil, err }
 return &baidu.DownloadStream{Body:reader, Start:start, End:end, Remaining:end-start+1, Total:s.fileSize, Partial:true}, nil
}

type baiduSegmentedReader struct {
 ctx context.Context
 client *http.Client
 signedURL string
 position, end, total int64
 current io.ReadCloser
 currentEnd int64
}

func (r *baiduSegmentedReader) openNext() error {
 if r.position > r.end { return io.EOF }
 last := r.position + baiduSourceSegmentBytes - 1
 if last > r.end { last = r.end }
 req, err := http.NewRequestWithContext(r.ctx, http.MethodGet, r.signedURL, nil)
 if err != nil { return err }
 req.Header.Set("Range", fmt.Sprintf("bytes=%d-%d", r.position, last))
 req.Header.Set("User-Agent", baiduWebUserAgent)
 resp, err := r.client.Do(req)
 if err != nil { return fmt.Errorf("open authorized Baidu range: %w", err) }
 if resp.StatusCode != http.StatusPartialContent {
  resp.Body.Close()
  if resp.StatusCode == http.StatusUnauthorized || resp.StatusCode == http.StatusForbidden { return errBaiduDownloadDenied }
  if resp.StatusCode < 500 { return fmt.Errorf("%w (signed range HTTP %d)", errBaiduDownloadDenied, resp.StatusCode) }
  return fmt.Errorf("Baidu signed download returned HTTP %d", resp.StatusCode)
 }
 match := baiduContentRange.FindStringSubmatch(resp.Header.Get("Content-Range"))
 if len(match) != 4 { resp.Body.Close(); return fmt.Errorf("Baidu signed download omitted exact Content-Range") }
 a, e1 := strconv.ParseInt(match[1], 10, 64)
 b, e2 := strconv.ParseInt(match[2], 10, 64)
 c, e3 := strconv.ParseInt(match[3], 10, 64)
 if e1 != nil || e2 != nil || e3 != nil || a != r.position || b != last || c != r.total {
  resp.Body.Close()
  return fmt.Errorf("Baidu signed download returned mismatched Content-Range")
 }
 if resp.ContentLength >= 0 && resp.ContentLength != last-r.position+1 {
  resp.Body.Close()
  return fmt.Errorf("Baidu signed download returned incorrect Content-Length")
 }
 r.current, r.currentEnd = resp.Body, last
 return nil
}

func (r *baiduSegmentedReader) Read(p []byte) (int, error) {
 if len(p) == 0 { return 0, nil }
 if r.position > r.end { return 0, io.EOF }
 if r.current == nil { if err := r.openNext(); err != nil { return 0, err } }
 count := int64(len(p))
 if remain := r.currentEnd-r.position+1; count > remain { count = remain }
 n, err := r.current.Read(p[:int(count)])
 r.position += int64(n)
 if err == io.EOF && r.position <= r.currentEnd { return n, io.ErrUnexpectedEOF }
 if err != nil && err != io.EOF { return n, err }
 if r.position > r.currentEnd {
  r.current.Close()
  r.current = nil
 }
 if n > 0 { return n, nil }
 if r.position > r.end { return 0, io.EOF }
 return 0, io.ErrNoProgress
}

func (r *baiduSegmentedReader) Close() error {
 if r.current == nil { return nil }
 err := r.current.Close()
 r.current = nil
 return err
}
