package main

// BaiduPCS-Go-compatible locatedownload source for tool-owned staged files.
// The download URL and account identity never enter public state or logs.
import (
	"context"
	"crypto/md5"
	"crypto/sha1"
	"encoding/hex"
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

const locatedUserAgent = "netdisk;P2SP;3.0.0.8;netdisk;11.12.3;ANG-AN00;android-android;10.0;JSbridge4.4.0;jointBridge;1.1.0;"
const locatedSignSalt = "ebrcUYiuxaZv2XGu7KIYKxUrqfnOfpDF"

var errLocatedDownloadDenied = errors.New("Baidu refused signed locatedownload")
var locatedContentRange = regexp.MustCompile(`^bytes ([0-9]+)-([0-9]+)/([0-9]+)$`)

type locatedDownloadSource struct {
	cookie string
	bduss  string
	meta   *http.Client
	data   *http.Client
}

func newLocatedDownloadSource(cookie string) (*locatedDownloadSource, error) {
	bduss := ""
	for _, pair := range strings.Split(cookie, ";") {
		name, value, ok := strings.Cut(strings.TrimSpace(pair), "=")
		if ok && name == "BDUSS" {
			bduss = value
			break
		}
	}
	if bduss == "" {
		return nil, baidu.ErrAuthRequired
	}
	return &locatedDownloadSource{
		cookie: cookie,
		bduss: bduss,
		meta: &http.Client{
			Timeout: 45 * time.Second,
			CheckRedirect: func(_ *http.Request, _ []*http.Request) error { return http.ErrUseLastResponse },
		},
		data: &http.Client{
			CheckRedirect: func(req *http.Request, via []*http.Request) error {
				if len(via) >= 5 || !allowedLocatedHost(req.URL) {
					return errLocatedDownloadDenied
				}
				req.Header.Del("Cookie")
				req.Header.Del("Authorization")
				req.Header.Del("Referer")
				req.Header.Set("User-Agent", locatedUserAgent)
				return nil
			},
		},
	}, nil
}

func locatedSignature(bduss string, uid int64, stamp int64) (devuid, signature string) {
	md5sum := md5.Sum([]byte(bduss))
	devuid = strings.ToUpper(hex.EncodeToString(md5sum[:])) + "|0"
	shaBDUSS := sha1.Sum([]byte(bduss))
	input := hex.EncodeToString(shaBDUSS[:]) + strconv.FormatInt(uid, 10) +
		locatedSignSalt + strconv.FormatInt(stamp, 10) + devuid
	sum := sha1.Sum([]byte(input))
	return devuid, hex.EncodeToString(sum[:])
}

func allowedLocatedHost(u *url.URL) bool {
	if u == nil || u.Scheme != "https" || u.User != nil || u.Port() != "" {
		return false
	}
	host := strings.ToLower(u.Hostname())
	return host == "d.pcs.baidu.com" || strings.HasSuffix(host, ".baidupcs.com")
}

func locatedRange(value string) (start, end, total int64, err error) {
	fields := locatedContentRange.FindStringSubmatch(value)
	if len(fields) != 4 {
		return 0, 0, 0, fmt.Errorf("signed Baidu range is missing or malformed")
	}
	start, err = strconv.ParseInt(fields[1], 10, 64)
	if err != nil {
		return
	}
	end, err = strconv.ParseInt(fields[2], 10, 64)
	if err != nil {
		return
	}
	total, err = strconv.ParseInt(fields[3], 10, 64)
	if err != nil {
		return
	}
	if start < 0 || end < start || total <= end {
		return 0, 0, 0, fmt.Errorf("signed Baidu range is invalid")
	}
	return
}

func (s *locatedDownloadSource) accountJSON(ctx context.Context, method, target string, result any) error {
	req, err := http.NewRequestWithContext(ctx, method, target, nil)
	if err != nil {
		return fmt.Errorf("create Baidu metadata request: %w", err)
	}
	req.Header.Set("Cookie", s.cookie)
	req.Header.Set("User-Agent", locatedUserAgent)
	req.Header.Set("Accept", "application/json,*/*")
	req.Header.Set("Referer", "https://pan.baidu.com/disk/home")
	resp, err := s.meta.Do(req)
	if err != nil {
		return fmt.Errorf("Baidu metadata request failed: %T", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("%w: metadata HTTP %d", errLocatedDownloadDenied, resp.StatusCode)
	}
	if err := json.NewDecoder(io.LimitReader(resp.Body, 1<<20)).Decode(result); err != nil {
		return fmt.Errorf("decode Baidu metadata: %w", err)
	}
	return nil
}

func (s *locatedDownloadSource) locate(ctx context.Context, remotePath string) (string, error) {
	var identity struct {
		Records []struct{ UK json.Number `json:"uk"` } `json:"records"`
	}
	if err := s.accountJSON(ctx, http.MethodGet,
		"https://pan.baidu.com/api/user/getinfo?need_selfinfo=1", &identity); err != nil {
		return "", err
	}
	if len(identity.Records) != 1 {
		return "", fmt.Errorf("%w: account UK unavailable", errLocatedDownloadDenied)
	}
	uid, err := identity.Records[0].UK.Int64()
	if err != nil || uid <= 0 {
		return "", fmt.Errorf("%w: invalid account UK", errLocatedDownloadDenied)
	}
	stamp := time.Now().Unix()
	devuid, sign := locatedSignature(s.bduss, uid, stamp)
	query := url.Values{
		"ant": {"1"}, "check_blue": {"1"}, "es": {"1"}, "esl": {"1"},
		"app_id": {"250528"}, "method": {"locatedownload"},
		"path": {remotePath}, "ver": {"4.0"}, "clienttype": {"17"},
		"channel": {"0"}, "apn_id": {"1_0"}, "freeisp": {"0"},
		"queryfree": {"0"}, "use": {"0"}, "time": {strconv.FormatInt(stamp, 10)},
		"rand": {sign}, "devuid": {devuid}, "cuid": {devuid},
	}
	var result struct {
		ErrorCode int `json:"error_code"`
		Errno     int `json:"errno"`
		URLs      []struct {
			URL string `json:"url"`
			Encrypt int `json:"encrypt"`
		} `json:"urls"`
	}
	target := "https://pcs.baidu.com/rest/2.0/pcs/file?" + query.Encode()
	if err := s.accountJSON(ctx, http.MethodPost, target, &result); err != nil {
		return "", err
	}
	if result.ErrorCode != 0 || result.Errno != 0 {
		return "", fmt.Errorf("%w: locatedownload code %d/%d", errLocatedDownloadDenied, result.ErrorCode, result.Errno)
	}
	for _, item := range result.URLs {
		if item.Encrypt != 0 {
			continue
		}
		link, err := url.Parse(item.URL)
		if err != nil {
			continue
		}
		link.Scheme = "https"
		link.Fragment = ""
		if allowedLocatedHost(link) {
			return link.String(), nil
		}
	}
	return "", fmt.Errorf("%w: no valid signed download address", errLocatedDownloadDenied)
}

// The CDN has a separate per-request Range policy. Fetch bounded source
// segments while exposing one continuous reader to Drive's 512 MiB PUT.
const locatedSegmentBytes = int64(4 << 20)

type locatedSegmentedReader struct {
	ctx      context.Context
	client   *http.Client
	signed   string
	position int64
	end      int64
	total    int64
	current  io.ReadCloser
	partEnd  int64
}

func (r *locatedSegmentedReader) openNext() error {
	partEnd := r.position + locatedSegmentBytes - 1
	if partEnd > r.end {
		partEnd = r.end
	}
	req, err := http.NewRequestWithContext(r.ctx, http.MethodGet, r.signed, nil)
	if err != nil {
		return fmt.Errorf("create Baidu signed range request: %T", err)
	}
	req.Header.Set("User-Agent", locatedUserAgent)
	req.Header.Set("Accept", "*/*")
	req.Header.Set("Accept-Encoding", "identity")
	req.Header.Set("Range", fmt.Sprintf("bytes=%d-%d", r.position, partEnd))
	resp, err := r.client.Do(req)
	if err != nil {
		if errors.Is(err, errLocatedDownloadDenied) {
			return errLocatedDownloadDenied
		}
		return fmt.Errorf("signed Baidu download transport failed: %T", err)
	}
	if resp.StatusCode != http.StatusPartialContent {
		resp.Body.Close()
		if resp.StatusCode < 500 {
			return fmt.Errorf("%w: download HTTP %d", errLocatedDownloadDenied, resp.StatusCode)
		}
		return fmt.Errorf("Baidu signed download HTTP %d", resp.StatusCode)
	}
	actualStart, actualEnd, total, err := locatedRange(resp.Header.Get("Content-Range"))
	if err != nil {
		resp.Body.Close()
		return err
	}
	if actualStart != r.position || actualEnd != partEnd ||
		(r.total != 0 && r.total != total) ||
		(resp.ContentLength >= 0 && resp.ContentLength != partEnd-r.position+1) {
		resp.Body.Close()
		return fmt.Errorf("Baidu signed download did not honor exact byte range")
	}
	r.total = total
	r.current = resp.Body
	r.partEnd = partEnd
	return nil
}

func (r *locatedSegmentedReader) Read(p []byte) (int, error) {
	if len(p) == 0 {
		return 0, nil
	}
	if r.position > r.end {
		return 0, io.EOF
	}
	if r.current == nil {
		if err := r.openNext(); err != nil {
			return 0, err
		}
	}
	maxBytes := int64(len(p))
	if left := r.partEnd - r.position + 1; maxBytes > left {
		maxBytes = left
	}
	n, err := r.current.Read(p[:int(maxBytes)])
	r.position += int64(n)
	if err == io.EOF && r.position <= r.partEnd {
		return n, io.ErrUnexpectedEOF
	}
	if err != nil && err != io.EOF {
		return n, err
	}
	if r.position > r.partEnd {
		_ = r.current.Close()
		r.current = nil
	}
	if n > 0 {
		return n, nil
	}
	if r.position > r.end {
		return 0, io.EOF
	}
	return 0, io.ErrNoProgress
}

func (r *locatedSegmentedReader) Close() error {
	if r.current == nil {
		return nil
	}
	err := r.current.Close()
	r.current = nil
	return err
}

func (s *locatedDownloadSource) OpenDownloadRange(ctx context.Context, remotePath string, start, end int64) (*baidu.DownloadStream, error) {
	if remotePath == "/BaiduDriveMover" || !strings.HasPrefix(remotePath, "/BaiduDriveMover/") || path.Clean(remotePath) != remotePath {
		return nil, fmt.Errorf("Baidu source path is outside tool-owned staging")
	}
	if start < 0 || end < start {
		return nil, fmt.Errorf("invalid Baidu byte range")
	}
	link, err := s.locate(ctx, remotePath)
	if err != nil {
		return nil, err
	}
	reader := &locatedSegmentedReader{
		ctx: ctx, client: s.data, signed: link, position: start, end: end,
	}
	if err := reader.openNext(); err != nil {
		return nil, err
	}
	return &baidu.DownloadStream{
		Body: reader,
		Start: start, End: end, Total: reader.total,
		Remaining: end-start+1,
		Partial: true,
	}, nil
}
