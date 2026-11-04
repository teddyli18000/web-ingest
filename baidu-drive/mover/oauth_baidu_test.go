package main

import (
 "context"
 "fmt"
 "net/http"
 "net/http/httptest"
 "net/url"
 "strings"
 "testing"

 "github.com/teddyli18000/baidu-drive-mover/internal/baidu"
 "github.com/teddyli18000/baidu-drive-mover/internal/manifest"
)
type oauthCapture struct {files []manifest.File;dirs []manifest.Directory}
func (c *oauthCapture) UpsertManifestPage(_ context.Context,_ string,dirs []manifest.Directory,files []manifest.File)error{
 c.files=append(c.files,files...);c.dirs=append(c.dirs,dirs...);return nil
}
func TestOAuthProviderShareStagingAndBoundedStream(t *testing.T){
 var server *httptest.Server
 transfers:=0
 deletes:=0
 server=httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter,r *http.Request){
  if r.URL.Query().Get("access_token")!="test-access" {t.Errorf("missing OAuth token on %s",r.URL.Path)}
  switch r.URL.Path{
  case "/rest/2.0/xpan/share":
   switch r.URL.Query().Get("method"){
   case "verify":
    if r.FormValue("pwd")!="abcd" {t.Errorf("verify password not forwarded")}
    fmt.Fprint(w, `{"errno":0,"randsk":"encoded%20sekey"}`)
   case "list":
    if r.URL.Query().Get("sekey")!="encoded sekey" {t.Errorf("share sekey was not URL decoded")}
    fmt.Fprint(w, `{"errno":0,"share_id":888,"uk":999,"list":[{"fs_id":101,"server_filename":"hello.bin","path":"/shared/hello.bin","size":11,"md5":"5eb63bbbe01eeed093cb22bb8f5acdc3","isdir":0}]}`)
   case "transfer":
    transfers++
    if r.FormValue("path")!="/apps/demo/BaiduDriveMover/task/batch" || r.FormValue("sekey")!="encoded sekey" {t.Errorf("transfer params %v",r.Form)}
    fmt.Fprint(w, `{"errno":0}`)
   }
  case "/rest/2.0/xpan/file":
   switch r.URL.Query().Get("method"){
   case "create":
    if !strings.HasPrefix(r.FormValue("path"),"/apps/demo/BaiduDriveMover") {t.Errorf("mkdir escaped sandbox")}
    fmt.Fprint(w, `{"errno":0}`)
   case "list":
    fmt.Fprint(w, `{"errno":0,"list":[{"fs_id":222,"server_filename":"hello.bin","path":"/apps/demo/BaiduDriveMover/task/batch/hello.bin","size":11,"md5":"5eb63bbbe01eeed093cb22bb8f5acdc3","isdir":0}]}`)
   case "filemanager":
    deletes++
    if r.URL.Query().Get("opera")!="delete" || r.FormValue("filelist")=="" {t.Error("unsafe cleanup request")}
    fmt.Fprint(w, `{"errno":0}`)
   }
  case "/rest/2.0/xpan/multimedia":
   fmt.Fprintf(w,`{"errno":0,"list":[{"fs_id":222,"size":11,"dlink":"%s/download"}]}`,server.URL)
  case "/download":
   if r.Header.Get("Range")!="bytes=2-7" {t.Errorf("incorrect Range %q",r.Header.Get("Range"))}
   if !strings.Contains(r.Header.Get("User-Agent"),"pan.baidu.com"){t.Error("download UA missing Baidu marker")}
   w.Header().Set("Content-Range","bytes 2-7/11")
   w.Header().Set("Content-Length","6")
   w.WriteHeader(206)
   _,_=w.Write([]byte("llo wo"))
  }
 }))
 defer server.Close()
 o,err:=newOAuthBaiduAt("test-access","/apps/demo",server.URL,server.Client())
 if err!=nil{t.Fatal(err)}
 link,err:=baidu.ParseShareLink("https://pan.baidu.com/s/1example");if err!=nil{t.Fatal(err)}
 sh,err:=o.AccessSharePage(context.Background(),link);if err!=nil{t.Fatal(err)}
 if err:=o.VerifyPassword(context.Background(),link,sh,"abcd");err!=nil{t.Fatal(err)}
 capture:=&oauthCapture{}
 if err:=o.Scan(context.Background(),"task",link,sh,capture);err!=nil{t.Fatal(err)}
 if len(capture.files)!=1 || capture.files[0].Name!="hello.bin" {t.Fatalf("scan files: %#v",capture.files)}
 if err:=o.EnsureStagingDirectory(context.Background(),"/BaiduDriveMover/task/batch");err!=nil{t.Fatal(err)}
 if err:=o.TransferFiles(context.Background(),link,sh,[]int64{101},"/BaiduDriveMover/task/batch");err!=nil{t.Fatal(err)}
 objects,err:=o.ListStagingDirectory(context.Background(),"/BaiduDriveMover/task/batch");if err!=nil{t.Fatal(err)}
 if len(objects)!=1 || objects[0].Path!="/BaiduDriveMover/task/batch/hello.bin" {t.Fatalf("unsafe mapped staging %#v",objects)}
 stream,err:=o.OpenDownloadRange(context.Background(),objects[0].Path,2,7);if err!=nil{t.Fatal(err)}
 defer stream.Body.Close()
 if stream.Start!=2||stream.End!=7||stream.Total!=11||stream.Remaining!=6{t.Fatalf("range mismatch %#v",stream)}
 if err:=o.DeleteStagingPath(context.Background(),"/BaiduDriveMover/task/batch");err!=nil{t.Fatal(err)}
 if transfers!=1||deletes!=1{t.Fatalf("missing remote steps: transfer %d delete %d",transfers,deletes)}
}
func TestOAuthProviderRejectsOutOfSandboxMutations(t *testing.T){
 o,_:=newOAuthBaidu("token","/apps/demo")
 if err:=o.DeleteStagingPath(context.Background(),"/BaiduDriveMover");err==nil{t.Fatal("global staging root could be deleted")}
 if err:=o.DeleteStagingPath(context.Background(),"/outside");err==nil{t.Fatal("unrelated path could be deleted")}
 if _,err:=o.physical("/BaiduDriveMover/task/../outside");err==nil{t.Fatal("noncanonical virtual path accepted")}
 if _,err:=newOAuthBaidu("token","/apps/demo/another");err==nil{t.Fatal("nested app root accepted")}
 if _,err:=newOAuthBaidu("token","/BaiduDriveMover");err==nil{t.Fatal("non-app root accepted")}
}
var _ = url.Values{}
