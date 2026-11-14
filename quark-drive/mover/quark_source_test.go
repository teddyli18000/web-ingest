package main

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/url"
	"strings"
	"testing"
)

type mockQuarkTransport func(*http.Request) (*http.Response,error)
func (f mockQuarkTransport) RoundTrip(r *http.Request) (*http.Response,error) {return f(r)}

func TestQuarkURLBoundaryAndContentRange(t *testing.T) {
	for _,raw:=range []string{"https://dl.quark.cn/data","https://cdn.aliyundomain.example/a"} {
		u,_:=url.Parse(raw)
		if !allowQuarkURL(u) {t.Fatal("expected Quark signed URL to be accepted")}
	}
	for _,raw:=range []string{"http://dl.quark.cn/a","https://user@dl.quark.cn/a","https://dl.quark.cn:80/a","https://localhost/a"} {
		u,_:=url.Parse(raw)
		if allowQuarkURL(u) {t.Fatal("unsafe signed URL accepted")}
	}
	a,b,c,err:=parseQuarkContentRange("bytes 2-4/9")
	if err!=nil || a!=2 || b!=4 || c!=9 {t.Fatal("incorrect Range parser")}
	if _,_,_,err=parseQuarkContentRange("bytes 2-9/9");err==nil {t.Fatal("allowed invalid Range")}
}

func TestQuarkSignedRangeStreamsAndRefreshes(t *testing.T) {
	src,err:=newQuarkDownloadSource("__puus=test")
	if err!=nil {t.Fatal(err)}
	lookups,reads:=0,0
	src.client=&http.Client{Transport:mockQuarkTransport(func(req *http.Request)(*http.Response,error){
		if strings.HasPrefix(req.URL.Path,"/1/clouddrive/file/download") {
			lookups++
			if req.Header.Get("Cookie")!="__puus=test" || req.Method!="POST" {t.Fatal("Quark API auth missing")}
			blob,_:=json.Marshal(map[string]any{"code":0,"data":[]map[string]string{{"fid":"fid-1","download_url":"https://dl.quark.cn/data?sign=private"}}})
			return &http.Response{StatusCode:200,Body:io.NopCloser(bytes.NewReader(blob))},nil
		}
		if req.URL.Hostname()!="dl.quark.cn" {t.Fatal("unexpected download host")}
		reads++
		if req.Header.Get("Range")!="bytes=0-5" || req.Header.Get("Cookie")!="__puus=test" {t.Fatal("Range or cookie not honored")}
		if reads==1 {return &http.Response{StatusCode:403,Body:io.NopCloser(strings.NewReader(""))},nil}
		return &http.Response{StatusCode:206,Header:http.Header{"Content-Range":[]string{"bytes 0-5/6"}},ContentLength:6,Body:io.NopCloser(strings.NewReader("ABCDEF"))},nil
	})}
	stream,err:=src.OpenDownloadRange(context.Background(),"fid-1",0,5)
	if err!=nil {t.Fatal(err)}
	defer stream.Body.Close()
	raw,err:=io.ReadAll(stream.Body)
	if err!=nil || string(raw)!="ABCDEF" {t.Fatal("incorrect Quark stream")}
	if stream.Start!=0||stream.End!=5||stream.Total!=6||stream.Remaining!=6 {t.Fatal("incorrect stream metadata")}
	if lookups!=2||reads!=2 {t.Fatalf("expected one signed URL refresh, got %d/%d",lookups,reads)}
}
