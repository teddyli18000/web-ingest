package main

// The Quark download source resolves a fresh signed link from the user's
// staged Quark file ID. CDN segments stream directly into the Drive PUT.
import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"regexp"
	"strconv"
	"strings")

const quarkAPIBase = "https://drive-pc.quark.cn/1/clouddrive"
const quarkUserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) quark-cloud-drive/2.5.20 Chrome/100.0.4896.160 Electron/18.3.5.4-b478491100 Safari/537.36"
const quarkRangePart = int64(4 << 20)

var (
	errQuarkAuthRequired = errors.New("Quark browser login required")
	errQuarkSourceDenied = errors.New("Quark file download unavailable")
	quarkContentRange = regexp.MustCompile(`^bytes ([0-9]+)-([0-9]+)/([0-9]+)$`)
	quarkFIDPattern = regexp.MustCompile(`^[A-Za-z0-9_-]{1,128}$`)
)

type quarkDownloadStream struct {
	Body      io.ReadCloser
	Start     int64
	End       int64
	Total     int64
	Remaining int64
}

type quarkDownloadSource struct {
	cookie  string
	client  *http.Client
	apiBase string
}

func newQuarkDownloadSource(cookie string) (*quarkDownloadSource, error) {
	if strings.TrimSpace(cookie) == "" || !strings.Contains(cookie, "__puus=") {
		return nil, errQuarkAuthRequired
	}
	return &quarkDownloadSource{
		cookie: cookie, apiBase: quarkAPIBase,
		client: &http.Client{
			Timeout: 0,
			CheckRedirect: func(req *http.Request, chain []*http.Request) error {
				if len(chain) > 5 || !allowQuarkURL(req.URL) {
					return errQuarkSourceDenied
				}
				req.Header.Del("Authorization")
				req.Header.Del("Cookie")
				if quarkCookieHost(req.URL.Hostname()) {
					req.Header.Set("Cookie", cookie)
				}
				return nil
			},
		},
	}, nil
}

func quarkCookieHost(host string) bool {
	host = strings.ToLower(host)
	return host == "quark.cn" || strings.HasSuffix(host, ".quark.cn")
}

func allowQuarkURL(u *url.URL) bool {
	if u == nil || u.Scheme != "https" || u.User != nil || u.Port() != "" {
		return false
	}
	host := strings.ToLower(u.Hostname())
	// Signed CDN URL is supplied by the authenticated Quark API. Never accept
	// literal IPs or a local/single-label host as a signed download target.
	if host == "" || !strings.Contains(host, ".") || strings.ContainsAny(host, "[]") {
		return false
	}
	return !strings.HasSuffix(host, ".localhost") && host != "localhost"
}

func parseQuarkContentRange(value string) (start, end, total int64, err error) {
	fields := quarkContentRange.FindStringSubmatch(value)
	if len(fields) != 4 {
		return 0, 0, 0, fmt.Errorf("Quark CDN omitted an exact Content-Range")
	}
	start, err = strconv.ParseInt(fields[1], 10, 64)
	if err != nil { return }
	end, err = strconv.ParseInt(fields[2], 10, 64)
	if err != nil { return }
	total, err = strconv.ParseInt(fields[3], 10, 64)
	if err != nil { return }
	if start < 0 || end < start || total <= end {
		return 0, 0, 0, fmt.Errorf("Quark CDN returned an invalid Content-Range")
	}
	return
}

func (s *quarkDownloadSource) refreshLink(ctx context.Context, fid string) (string, error) {
	body := strings.NewReader(fmt.Sprintf(`{"fids":[%q]}`, fid))
	target := s.apiBase + "/file/download?pr=ucpro&fr=pc"
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, target, body)
	if err != nil { return "", fmt.Errorf("create Quark link request: %T", err) }
	req.Header.Set("Cookie", s.cookie)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("User-Agent", quarkUserAgent)
	req.Header.Set("Referer", "https://pan.quark.cn/")
	req.Header.Set("Origin", "https://pan.quark.cn")
	resp, err := s.client.Do(req)
	if err != nil { return "", fmt.Errorf("Quark link request failed: %T", err) }
	defer resp.Body.Close()
	if resp.StatusCode == 401 { return "", errQuarkAuthRequired }
	if resp.StatusCode != 200 {
		if resp.StatusCode == 429 || resp.StatusCode >= 500 {
			return "", fmt.Errorf("Quark link service temporarily unavailable: HTTP %d", resp.StatusCode)
		}
		return "", errQuarkSourceDenied
	}
	var result struct {
		Code int `json:"code"`
		Data []struct {
			FID string `json:"fid"`
			DownloadURL string `json:"download_url"`
		} `json:"data"`
	}
	if err := json.NewDecoder(io.LimitReader(resp.Body, 1<<20)).Decode(&result); err != nil {
		return "", fmt.Errorf("decode Quark signed link: %T", err)
	}
	if result.Code == 40001 || result.Code == 10000 { return "", errQuarkAuthRequired }
	if result.Code == 23018 { return "", fmt.Errorf("Quark download provider temporarily throttled") }
	if result.Code != 0 { return "", errQuarkSourceDenied }
	if len(result.Data) == 0 { return "", fmt.Errorf("Quark signed link is pending") }
	var raw string
	for _, link := range result.Data {
		if link.FID == fid && link.DownloadURL != "" { raw = link.DownloadURL; break }
	}
	if raw == "" && len(result.Data) == 1 { raw = result.Data[0].DownloadURL }
	u, err := url.Parse(raw)
	if err != nil || !allowQuarkURL(u) { return "", errQuarkSourceDenied }
	u.Fragment = ""
	return u.String(), nil
}

type quarkSegmentReader struct {
	source   *quarkDownloadSource
	ctx      context.Context
	fid      string
	signed   string
	pos      int64
	end      int64
	total    int64
	partEnd  int64
	body     io.ReadCloser
}

func (r *quarkSegmentReader) openPart() error {
	end := r.pos + quarkRangePart - 1
	if end > r.end { end = r.end }
	for attempt:=0; attempt<2; attempt++ {
		if r.signed == "" {
			signed, err := r.source.refreshLink(r.ctx, r.fid)
			if err != nil { return err }
			r.signed = signed
		}
		req, err := http.NewRequestWithContext(r.ctx, http.MethodGet, r.signed, nil)
		if err != nil { return fmt.Errorf("create Quark CDN Range: %T", err) }
		req.Header.Set("Range",fmt.Sprintf("bytes=%d-%d",r.pos,end))
		req.Header.Set("Accept-Encoding","identity")
		req.Header.Set("User-Agent",quarkUserAgent)
		u,_ := url.Parse(r.signed)
		if quarkCookieHost(u.Hostname()) { req.Header.Set("Cookie",r.source.cookie) }
		resp, err := r.source.client.Do(req)
		if err != nil {
			if errors.Is(err,errQuarkSourceDenied) { return errQuarkSourceDenied }
			return fmt.Errorf("Quark CDN transport failed: %T", err)
		}
		if resp.StatusCode == 401 || resp.StatusCode == 403 {
			resp.Body.Close()
			r.signed = ""
			continue
		}
		if resp.StatusCode != http.StatusPartialContent {
			resp.Body.Close()
			if resp.StatusCode == 429 || resp.StatusCode >= 500 {
				return fmt.Errorf("Quark CDN temporarily unavailable: HTTP %d",resp.StatusCode)
			}
			return errQuarkSourceDenied
		}
		start,actualEnd,total,err := parseQuarkContentRange(resp.Header.Get("Content-Range"))
		if err != nil {
			resp.Body.Close()
			return err
		}
		if start != r.pos || actualEnd != end || (r.total != 0 && r.total != total) ||
			(resp.ContentLength >= 0 && resp.ContentLength != end-r.pos+1) {
			resp.Body.Close()
			return fmt.Errorf("Quark CDN did not honor exact byte range")
		}
		r.total, r.partEnd, r.body = total, end, resp.Body
		return nil
	}
	return errQuarkSourceDenied
}

func (r *quarkSegmentReader) Read(p []byte) (int,error) {
	if len(p)==0 {return 0,nil}
	if r.pos>r.end {return 0,io.EOF}
	if r.body==nil {if err:=r.openPart();err!=nil{return 0,err}}
	want:=int64(len(p))
	if remain:=r.partEnd-r.pos+1;want>remain {want=remain}
	n,err:=r.body.Read(p[:int(want)])
	r.pos+=int64(n)
	if err==io.EOF && r.pos<=r.partEnd {return n,io.ErrUnexpectedEOF}
	if err!=nil && err!=io.EOF {return n,err}
	if r.pos>r.partEnd {_=r.body.Close();r.body=nil}
	if n>0 {return n,nil}
	if r.pos>r.end {return 0,io.EOF}
	return 0,io.ErrNoProgress
}

func (r *quarkSegmentReader) Close() error {
	if r.body==nil{return nil}
	err:=r.body.Close()
	r.body=nil
	return err
}

func (s *quarkDownloadSource) OpenDownloadRange(ctx context.Context, fid string, start,end int64) (*quarkDownloadStream,error) {
	if !quarkFIDPattern.MatchString(fid) || start<0 || end<start {
		return nil,fmt.Errorf("invalid Quark source file ID or range")
	}
	reader:= &quarkSegmentReader{source:s,ctx:ctx,fid:fid,pos:start,end:end}
	if err:=reader.openPart();err!=nil{return nil,err}
	return &quarkDownloadStream{Body:reader,Start:start,End:end,Total:reader.total,Remaining:end-start+1},nil
}
