package main

import (
 "bytes"
 "context"
 "errors"
 "fmt"
 "io"
 "net/http"
 "net/url"
 "strconv"
 "strings"
 "testing"

 "github.com/teddyli18000/baidu-drive-mover/internal/baidu"
)

type stagedSourceFixture struct {
 files []baidu.RemoteFile
 calls int
}
func (f *stagedSourceFixture) ListStagingDirectory(_ context.Context, dir string) ([]baidu.RemoteFile,error) {
 f.calls++
 if dir != "/BaiduDriveMover/t/b" { return nil, fmt.Errorf("unexpected stage directory") }
 return f.files,nil
}
type signedSourceTransport func(*http.Request)(*http.Response,error)
func (f signedSourceTransport) RoundTrip(r *http.Request)(*http.Response,error) {return f(r)}

func TestSignedSourceStreamsBaiduRangesWithoutExposingCookies(t *testing.T) {
 const size int64=2*baiduSourceSegmentBytes+17
 const remote="/BaiduDriveMover/t/b/video.mp4"
 stage:=&stagedSourceFixture{files:[]baidu.RemoteFile{{FsID:42,Path:remote,Size:size}}}
 content:=bytes.Repeat([]byte{17},int(size))
 metadataCalls,rangeCalls:=0,0
 source:=newBaiduSignedRangeSource(stage,"BDUSS=private; STOKEN=private",size)
 source.transport.Transport=signedSourceTransport(func(req *http.Request)(*http.Response,error) {
  if req.URL.Host=="pan.baidu.com" {
   metadataCalls++
   if req.URL.Path!="/api/filemetas" || req.URL.Query().Get("fsids")!="[42]" || req.URL.Query().Get("dlink")!="1" {t.Error("unexpected filemetas request")}
   if !strings.Contains(req.Header.Get("Cookie"),"BDUSS=") {t.Error("missing own-session cookie")}
   return &http.Response{StatusCode:200,Header:make(http.Header),Body:io.NopCloser(strings.NewReader(`{"errno":0,"info":[{"fs_id":42,"dlink":"https://d.pcs.baidu.com/file/opaque?sign=private"}]}`))},nil
  }
  rangeCalls++
  if req.URL.Host!="d.pcs.baidu.com" || req.Header.Get("Cookie")!="" { t.Fatalf("secret or untrusted URL in signed download") }
  var from,to int64
  if _,err:=fmt.Sscanf(req.Header.Get("Range"),"bytes=%d-%d",&from,&to);err!=nil {t.Fatal(err)}
  if to-from+1>baiduSourceSegmentBytes {t.Fatalf("unbounded source segment")}
  header:=make(http.Header)
  header.Set("Content-Range",fmt.Sprintf("bytes %d-%d/%d",from,to,size))
  return &http.Response{StatusCode:206,Header:header,Body:io.NopCloser(bytes.NewReader(content[from:to+1])),ContentLength:to-from+1},nil
 })
 stream,err:=source.OpenDownloadRange(context.Background(),remote,0,size-1)
 if err!=nil {t.Fatal(err)}
 actual,err:=io.ReadAll(stream.Body)
 stream.Body.Close()
 if err!=nil || !bytes.Equal(actual,content) || metadataCalls!=1 || rangeCalls!=3 || stage.calls!=1 {
  t.Fatalf("unexpected bytes/requests bytes=%d metadata=%d ranges=%d stage=%d err=%v",len(actual),metadataCalls,rangeCalls,stage.calls,err)
 }
 suffix,err:=source.OpenDownloadRange(context.Background(),remote,17,42)
 if err!=nil {t.Fatal(err)}
 got,err:=io.ReadAll(suffix.Body)
 suffix.Body.Close()
 if err!=nil || !bytes.Equal(got,content[17:43]) || metadataCalls!=1 {t.Fatal("runner-local signed URL cache broken")}
}

func TestSignedSourceFailsClosedOnDownloadDenial(t *testing.T) {
 const remote="/BaiduDriveMover/t/b/video.mp4"
 stage:=&stagedSourceFixture{files:[]baidu.RemoteFile{{FsID:42,Path:remote,Size:4096}}}
 source:=newBaiduSignedRangeSource(stage,"BDUSS=private",4096)
 calls:=0
 source.transport.Transport=signedSourceTransport(func(req *http.Request)(*http.Response,error) {
  if req.URL.Host=="pan.baidu.com" {return &http.Response{StatusCode:200,Header:make(http.Header),Body:io.NopCloser(strings.NewReader(`{"errno":0,"info":[{"fs_id":42,"dlink":"https://d.pcs.baidu.com/file/opaque?sign=secret"}]}`))},nil}
  calls++
  return &http.Response{StatusCode:403,Header:make(http.Header),Body:io.NopCloser(strings.NewReader(`{"error_code":31326}`))},nil
 })
 _,err:=source.OpenDownloadRange(context.Background(),remote,0,4095)
 if !errors.Is(err,errBaiduDownloadDenied) || calls!=1 || strings.Contains(err.Error(),"secret") {t.Fatalf("rejected download mishandled: %v calls=%d",err,calls)}
}

func TestSignedSourceRejectsUntrustedLinkAndMismatchedRange(t *testing.T) {
 for _,raw:=range []string{"https://evil.example/file","http://d.pcs.baidu.com/file","https://d.pcs.baidu.com.evil.example/file","https://user:secret@d.pcs.baidu.com/file"} {
  u,_:=url.Parse(raw)
  if signedBaiduHost(u) {t.Fatalf("accepted untrusted URL: %s",raw)}
 }
 const remote="/BaiduDriveMover/t/b/video.mp4"
 stage:=&stagedSourceFixture{files:[]baidu.RemoteFile{{FsID:42,Path:remote,Size:1024}}}
 source:=newBaiduSignedRangeSource(stage,"BDUSS=private",1024)
 source.transport.Transport=signedSourceTransport(func(req *http.Request)(*http.Response,error) {
  if req.URL.Host=="pan.baidu.com" {return &http.Response{StatusCode:200,Header:make(http.Header),Body:io.NopCloser(strings.NewReader(`{"errno":0,"info":[{"fs_id":42,"dlink":"https://d.pcs.baidu.com/file/opaque"}]}`))},nil}
  h:=make(http.Header)
  h.Set("Content-Range","bytes 0-999/"+strconv.Itoa(1024))
  return &http.Response{StatusCode:206,Header:h,Body:io.NopCloser(strings.NewReader("x")),ContentLength:1000},nil
 })
 _,err:=source.OpenDownloadRange(context.Background(),remote,0,1023)
 if err==nil || !strings.Contains(err.Error(),"Content-Range") {t.Fatalf("wrong Range accepted: %v",err)}
}

func TestSignedBaiduDenialIsNotRetried(t *testing.T) {
 if got:=classifyRelayStepError(fmt.Errorf("Baidu blocked: %w",errBaiduDownloadDenied));got!="source_denied" {
  t.Fatalf("got %q, want source_denied",got)
 }
}
