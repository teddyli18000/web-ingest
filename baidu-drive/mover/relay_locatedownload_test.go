package main

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"testing"
)

type locatedRoundTripper func(*http.Request) (*http.Response, error)

func (f locatedRoundTripper) RoundTrip(r *http.Request) (*http.Response, error) { return f(r) }

func TestLocatedSignatureMatchesBaiduPCSGo(t *testing.T) {
	dev, signature := locatedSignature("test-BDUSS", 42, 1660000000)
	if dev != "95E9A26E45284C82EF98A62C03EF4997|0" || signature != "b7512a25d82526454830b7738b0b642314cef76a" {
		t.Fatalf("locatedownload signer differs from upstream algorithm")
	}
}

func TestLocatedDownloadHostAndRange(t *testing.T) {
	for _, host := range []string{
		"https://d.pcs.baidu.com/file",
		"https://bj001.baidupcs.com/file",
	} {
		u, _ := url.Parse(host)
		if !allowedLocatedHost(u) { t.Fatalf("valid signed host rejected") }
	}
	for _, bad := range []string{
		"http://d.pcs.baidu.com/file",
		"https://baidupcs.com.evil.test/path",
		"https://d.pcs.baidu.com:444/file",
		"https://user@d.pcs.baidu.com/file",
	} {
		u, _ := url.Parse(bad)
		if allowedLocatedHost(u) { t.Fatalf("invalid signed host accepted") }
	}
	a, b, c, err := locatedRange("bytes 4-7/10")
	if err != nil || a != 4 || b != 7 || c != 10 {t.Fatal("exact range parsing failed")}
	for _, bad := range []string{"bytes 8-7/10", "bytes 0-10/10", "bytes */10", "items 0-1/2"} {
		if _,_,_,err := locatedRange(bad); err == nil {t.Fatal("invalid range accepted")}
	}
}

func TestLocatedSourceStreamsExactRange(t *testing.T) {
	cookie := "BDUSS=test-BDUSS; STOKEN=test"
	source, err := newLocatedDownloadSource(cookie)
	if err != nil { t.Fatal(err) }
	source.meta = &http.Client{Transport: locatedRoundTripper(func(req *http.Request) (*http.Response, error) {
		if req.Header.Get("Cookie") != cookie || req.Header.Get("User-Agent") != locatedUserAgent {
			t.Fatal("signed metadata request lost expected authorization")
		}
		switch {
		case req.URL.Hostname() == "pan.baidu.com" && req.URL.Path == "/api/user/getinfo":
			return &http.Response{StatusCode: 200, Body: io.NopCloser(strings.NewReader(`{"records":[{"uk":42}]}`))}, nil
		case req.URL.Hostname() == "pcs.baidu.com" && req.URL.Query().Get("method") == "locatedownload":
			q := req.URL.Query()
			if req.Method != http.MethodPost || q.Get("app_id") != "250528" || q.Get("clienttype") != "17" || q.Get("path") != "/BaiduDriveMover/test/file" || q.Get("rand") == "" || q.Get("devuid") == "" {
				t.Fatal("signed locatedownload arguments differ from upstream")
			}
			return &http.Response{StatusCode: 200, Body: io.NopCloser(strings.NewReader(`{"urls":[{"url":"https://d.pcs.baidu.com/file/test?sign=hidden","encrypt":0}]}`))}, nil
		default:
			return nil, fmt.Errorf("unexpected metadata request")
		}
	})}
	source.data = &http.Client{Transport: locatedRoundTripper(func(req *http.Request) (*http.Response, error) {
		if req.URL.Hostname() != "d.pcs.baidu.com" || req.Header.Get("Range") != "bytes=4-7" || req.Header.Get("User-Agent") != locatedUserAgent || req.Header.Get("Cookie") != "" {
			t.Fatal("signed download request was not exact or exposed credentials")
		}
		return &http.Response{
			StatusCode: http.StatusPartialContent,
			Header: http.Header{"Content-Range": []string{"bytes 4-7/10"}},
			ContentLength: 4,
			Body: io.NopCloser(bytes.NewReader([]byte("ABCD"))),
		}, nil
	})}
	stream, err := source.OpenDownloadRange(context.Background(), "/BaiduDriveMover/test/file", 4, 7)
	if err != nil { t.Fatal(err) }
	defer stream.Body.Close()
	content, err := io.ReadAll(stream.Body)
	if err != nil || string(content) != "ABCD" || stream.Start != 4 || stream.End != 7 || stream.Total != 10 || stream.Remaining != 4 {
		t.Fatalf("stream metadata/payload mismatch")
	}
}

func TestLocatedReaderCrossesFourMiBSegments(t *testing.T) {
	const firstEnd = (4 << 20) - 1
	const finalEnd = firstEnd + 4
	const total = finalEnd + 3
	requests := 0
	client := &http.Client{Transport: locatedRoundTripper(func(req *http.Request) (*http.Response, error) {
		requests++
		switch requests {
		case 1:
			if req.Header.Get("Range") != "bytes=0-4194303" {
				t.Fatal("first segment range mismatch")
			}
			return &http.Response{
				StatusCode: 206,
				Header: http.Header{"Content-Range": []string{"bytes 0-4194303/4194310"}},
				ContentLength: 4 << 20,
				Body: io.NopCloser(bytes.NewReader(bytes.Repeat([]byte("A"), 4 << 20))),
			}, nil
		case 2:
			if req.Header.Get("Range") != "bytes=4194304-4194308" {
				t.Fatal("second segment range mismatch")
			}
			return &http.Response{
				StatusCode: 206,
				Header: http.Header{"Content-Range": []string{"bytes 4194304-4194308/4194310"}},
				ContentLength: 5,
				Body: io.NopCloser(strings.NewReader("BCDEF")),
			}, nil
		default:
			t.Fatal("unexpected third source request")
			return nil, nil
		}
	})}
	reader := &locatedSegmentedReader{
		ctx: context.Background(), client: client,
		signed: "https://d.pcs.baidu.com/file/hidden",
		position: 0, end: finalEnd,
	}
	if err := reader.openNext(); err != nil { t.Fatal(err) }
	defer reader.Close()
	got, err := io.ReadAll(reader)
	if err != nil || len(got) != int(finalEnd+1) || string(got[len(got)-5:]) != "BCDEF" || requests != 2 || reader.total != total {
		t.Fatalf("signed source segment continuity mismatch: requests=%d", requests)
	}
}
