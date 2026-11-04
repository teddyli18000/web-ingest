package main

// The OAuth-only Baidu transport translates the mover's virtual, tool-owned
// /BaiduDriveMover paths into the application's isolated /apps/<app> directory.
// It never sends cookies or invokes web-login APIs.
import (
 "context"
 "encoding/json"
 "fmt"
 "io"
 "net/http"
 "net/url"
 "path"
 "strconv"
 "strings"
 "time"

 "github.com/teddyli18000/baidu-drive-mover/internal/baidu"
 "github.com/teddyli18000/baidu-drive-mover/internal/manifest"
)

const virtualStagingRoot = "/BaiduDriveMover"
const maxOAuthPages = 10000

type oauthBaidu struct {
 token string
 appRoot string
 baseURL string
 client *http.Client
 sekey string
 shareID string
 shareUK string
}

func newOAuthBaidu(token, appRoot string) (*oauthBaidu, error) {
 return newOAuthBaiduAt(token, appRoot, "https://pan.baidu.com", &http.Client{Timeout: 45*time.Minute})
}
func newOAuthBaiduAt(token, appRoot, base string, client *http.Client) (*oauthBaidu, error) {
 appRoot = path.Clean(strings.TrimSpace(appRoot))
 if !strings.HasPrefix(appRoot, "/apps/") || appRoot == "/apps/" || strings.Contains(appRoot, "..") || strings.ContainsRune(appRoot, 0) || strings.ContainsRune(appRoot, 92) || strings.Contains(appRoot[6:],"/") {
  return nil, fmt.Errorf("invalid OAuth application root")
 }
 if strings.TrimSpace(token)=="" { return nil, baidu.ErrAuthRequired }
 if client==nil { client=&http.Client{Timeout:45*time.Minute} }
 return &oauthBaidu{token: strings.TrimSpace(token), appRoot:appRoot, baseURL:base, client:client},nil
}
func (o *oauthBaidu) HasLoginCookies() bool { return o != nil && o.token!="" }
func (o *oauthBaidu) CookieString() string { return "" }
func (o *oauthBaidu) physical(virtual string) (string,error) {
 if virtual!=path.Clean(virtual) || (virtual!=virtualStagingRoot && !strings.HasPrefix(virtual,virtualStagingRoot+"/")) {
  return "",fmt.Errorf("Baidu path outside tool staging root")
 }
 return o.appRoot+virtual,nil
}
func (o *oauthBaidu) virtual(physical string) (string,error) {
 prefix:=o.appRoot+virtualStagingRoot
 if physical!=prefix && !strings.HasPrefix(physical,prefix+"/") {return "",fmt.Errorf("Baidu returned path outside tool staging root")}
 return strings.TrimPrefix(physical,o.appRoot),nil
}
func (o *oauthBaidu) call(ctx context.Context,method,endpoint string,query,form url.Values,out any) error {
 u,err:=url.Parse(o.baseURL+endpoint);if err!=nil{return err}
 if query==nil{query=url.Values{}}
 query.Set("access_token",o.token)
 u.RawQuery=query.Encode()
 var body io.Reader
 if form!=nil {body=strings.NewReader(form.Encode())}
 requestCtx,cancel:=context.WithTimeout(ctx,45*time.Second)
 defer cancel()
 req,err:=http.NewRequestWithContext(requestCtx,method,u.String(),body);if err!=nil{return fmt.Errorf("invalid Baidu OAuth API request")}
 req.Header.Set("User-Agent","BaiduDriveMover/1.0 pan.baidu.com")
 if form!=nil {req.Header.Set("Content-Type","application/x-www-form-urlencoded")}
 resp,err:=o.client.Do(req);if err!=nil{return fmt.Errorf("Baidu OAuth API connection failed")}
 defer resp.Body.Close()
 if resp.StatusCode==http.StatusUnauthorized||resp.StatusCode==http.StatusForbidden{return baidu.ErrAuthRequired}
 if resp.StatusCode<200||resp.StatusCode>=300{return fmt.Errorf("Baidu OAuth API returned HTTP %d",resp.StatusCode)}
 data,err:=io.ReadAll(io.LimitReader(resp.Body,8<<20));if err!=nil{return err}
 var status struct {Errno int `json:"errno"`; ErrorCode int `json:"error_code"`; Info []struct {Errno int `json:"errno"`} `json:"info"`}
 if err=json.Unmarshal(data,&status);err!=nil{return fmt.Errorf("invalid Baidu OAuth API JSON: %w",err)}
 code:=status.Errno;if code==0 {code=status.ErrorCode}
 if code!=0{
  switch code{
  case -6,-7,31041,31042,31045: return baidu.ErrAuthRequired
  case -9: return baidu.ErrPasswordRequired
  case 31066,31202: return baidu.ErrStagingNotFound
  case 8001,-62: return baidu.ErrVerificationRequired
  }
  return fmt.Errorf("Baidu OAuth API errno %d",code)
 }
 for _,item:=range status.Info {if item.Errno!=0{return fmt.Errorf("Baidu OAuth API item errno %d",item.Errno)}}
 if out!=nil {if err=json.Unmarshal(data,out);err!=nil{return fmt.Errorf("invalid Baidu OAuth API response: %w",err)}}
 return nil
}

type oauthShareItem struct {
 FsID int64 `json:"fs_id"`
 Name string `json:"server_filename"`
 Path string `json:"path"`
 Size int64 `json:"size"`
 MD5 string `json:"md5"`
 IsDir int `json:"isdir"`
}
type oauthSharePage struct {
 ShareID int64 `json:"share_id"`
 UK int64 `json:"uk"`
 List []oauthShareItem `json:"list"`
}
func (o *oauthBaidu) AccessSharePage(ctx context.Context,link baidu.ShareLink)(baidu.ShareContext,error){
 // The official share APIs identify shares by short URL, without a browser
 // session or bdstoken. Protected shares are verified separately below.
 return baidu.ShareContext{},nil
}
func (o *oauthBaidu) VerifyPassword(ctx context.Context,link baidu.ShareLink,_ baidu.ShareContext,password string)error{
 if password==""{return baidu.ErrPasswordRequired}
 query:=url.Values{"method":{"verify"},"surl":{link.ShortURL}}
 form:=url.Values{"pwd":{password}}
 var result struct {Randsk string `json:"randsk"`}
 if err:=o.call(ctx,"POST","/rest/2.0/xpan/share",query,form,&result);err!=nil{return err}
 if result.Randsk==""{return fmt.Errorf("Baidu share verification did not return sekey")}
 decoded,err:=url.QueryUnescape(result.Randsk);if err!=nil{return fmt.Errorf("invalid share sekey")}
 o.sekey=decoded
 return nil
}
func (o *oauthBaidu) sharePage(ctx context.Context,link baidu.ShareLink,fid int64,first bool,page int)(oauthSharePage,error){
 query:=url.Values{"method":{"list"},"shorturl":{link.ShortURL},"page":{strconv.Itoa(page)},"num":{"100"}}
 if first {query.Set("root","1");query.Set("fid","0")} else {query.Set("root","0");query.Set("fid",strconv.FormatInt(fid,10))}
 if o.sekey!="" {query.Set("sekey",o.sekey)}
 var result oauthSharePage
 err:=o.call(ctx,"GET","/rest/2.0/xpan/share",query,nil,&result)
 if err!=nil{return result,err}
 if result.ShareID!=0 {o.shareID=strconv.FormatInt(result.ShareID,10)}
 if result.UK!=0 {o.shareUK=strconv.FormatInt(result.UK,10)}
 return result,nil
}
type shareFolder struct {fsid int64; logical string; source string; root bool}
func (o *oauthBaidu) Scan(ctx context.Context,taskID string,link baidu.ShareLink,_ baidu.ShareContext,sink manifest.Sink)error{
 if sink==nil||taskID==""{return fmt.Errorf("missing Baidu manifest sink")}
 if link.StartPath!="/" && link.StartPath!="" {return fmt.Errorf("OAuth share-subfolder links are not supported; use share root")}
 folders:=[]shareFolder{{fsid:0,logical:"/",source:"/",root:true}}
 for len(folders)>0 {
  folder:=folders[0];folders=folders[1:]
  for page:=1;page<=maxOAuthPages;page++ {
   response,err:=o.sharePage(ctx,link,folder.fsid,folder.root,page);if err!=nil{return err}
   dirs:=[]manifest.Directory{};files:=[]manifest.File{}
   for _,item:=range response.List {
    if item.Name==""||item.Name=="."||item.Name==".."||strings.ContainsAny(item.Name,"/")||strings.ContainsRune(item.Name,92)||strings.ContainsRune(item.Name,0)||item.Size<0||item.FsID<=0{return fmt.Errorf("unsafe Baidu share item")}
    logical:=path.Join(folder.logical,item.Name)
    if !strings.HasPrefix(logical,"/"){logical="/"+logical}
    source:=item.Path
    if source==""{source=path.Join(folder.source,item.Name)}
    if item.IsDir==1 {
     dirs=append(dirs,manifest.Directory{LogicalPath:logical})
     folders=append(folders,shareFolder{fsid:item.FsID,logical:logical,source:source})
    } else {
     parent:=path.Dir(logical)
     files=append(files,manifest.File{SourceID:strconv.FormatInt(item.FsID,10),SourcePath:source,
      LogicalPath:logical,ParentPath:parent,Name:item.Name,Size:item.Size,MD5:strings.ToLower(strings.TrimSpace(item.MD5))})
    }
   }
   if len(dirs)+len(files)>0 {
    if err:=sink.UpsertManifestPage(ctx,taskID,dirs,files);err!=nil{return err}
   }
   if len(response.List)<100 {break}
   if page==maxOAuthPages {return fmt.Errorf("Baidu share pagination exceeded limit")}
  }
 }
 return nil
}

type oauthFileEntry struct {
 FsID int64 `json:"fs_id"`
 Path string `json:"path"`
 Name string `json:"server_filename"`
 Size int64 `json:"size"`
 MD5 string `json:"md5"`
 IsDir int `json:"isdir"`
}
func (o *oauthBaidu) listActual(ctx context.Context,dir string)([]oauthFileEntry,error) {
 result:=[]oauthFileEntry{}
 for start:=0;start<1000000;start+=100 {
  q:=url.Values{"method":{"list"},"dir":{dir},"start":{strconv.Itoa(start)},"limit":{"100"}}
  var page struct {List []oauthFileEntry `json:"list"`}
  if err:=o.call(ctx,"GET","/rest/2.0/xpan/file",q,nil,&page);err!=nil{return nil,err}
  result=append(result,page.List...)
  if len(page.List)<100{return result,nil}
 }
 return nil,fmt.Errorf("Baidu directory pagination exceeded limit")
}
func (o *oauthBaidu) EnsureStagingDirectory(ctx context.Context,virtual string)error {
 actual,err:=o.physical(virtual);if err!=nil{return err}
 // The app directory is created by Baidu and is never a deletion target.
 suffix:=strings.TrimPrefix(actual,o.appRoot+"/")
 current:=o.appRoot
 for _,component:=range strings.Split(suffix,"/"){
  if component==""{continue}
  current=path.Join(current,component)
  form:=url.Values{"path":{current},"size":{"0"},"isdir":{"1"},"rtype":{"0"}}
  err:=o.call(ctx,"POST","/rest/2.0/xpan/file",url.Values{"method":{"create"}},form,nil)
  if err!=nil && !strings.Contains(err.Error(),"errno -8"){return err}
 }
 return nil
}
func (o *oauthBaidu) ListStagingDirectory(ctx context.Context,virtual string)([]baidu.RemoteFile,error){
 actual,err:=o.physical(virtual);if err!=nil{return nil,err}
 entries,err:=o.listActual(ctx,actual);if err!=nil{return nil,err}
 out:=make([]baidu.RemoteFile,0,len(entries))
 for _,entry:=range entries {
  logical,err:=o.virtual(entry.Path);if err!=nil{return nil,err}
  out=append(out,baidu.RemoteFile{FsID:entry.FsID,Name:entry.Name,Path:logical,
   Size:entry.Size,MD5:entry.MD5,IsDir:entry.IsDir==1})
 }
 return out,nil
}
func (o *oauthBaidu) ListStagingPathForCleanup(ctx context.Context,virtual string)([]baidu.RemoteFile,error){
 if virtual==virtualStagingRoot{return nil,fmt.Errorf("refusing cleanup of staging root")}
 return o.ListStagingDirectory(ctx,virtual)
}
func (o *oauthBaidu) DeleteStagingPath(ctx context.Context,virtual string)error{
 if virtual==virtualStagingRoot{return fmt.Errorf("refusing deletion of staging root")}
 actual,err:=o.physical(virtual);if err!=nil{return err}
 encoded,_:=json.Marshal([]string{actual})
 form:=url.Values{"async":{"0"},"filelist":{string(encoded)}}
 return o.call(ctx,"POST","/rest/2.0/xpan/file",url.Values{"method":{"filemanager"},"opera":{"delete"}},form,nil)
}
func (o *oauthBaidu) TransferFiles(ctx context.Context,link baidu.ShareLink,_ baidu.ShareContext,ids []int64,virtual string)error{
 if len(ids)==0{return fmt.Errorf("no staged share IDs")}
 actual,err:=o.physical(virtual);if err!=nil{return err}
 if o.shareID=="" || o.shareUK=="" {
  if _,err:=o.sharePage(ctx,link,0,true,1);err!=nil{return err}
 }
 if o.shareID==""||o.shareUK==""{return fmt.Errorf("share listing did not return share ID and owner UK")}
 var account struct {UK int64 `json:"uk"`}
 if err:=o.call(ctx,"GET","/rest/2.0/xpan/nas",url.Values{"method":{"uinfo"}},nil,&account);err!=nil{return err}
 if account.UK==0{return fmt.Errorf("Baidu OAuth account did not return UK")}
 if strconv.FormatInt(account.UK,10)==o.shareUK{
  return o.copyOwnSharedFiles(ctx,link,ids,actual)
 }
 idsJSON,_:=json.Marshal(ids)
 form:=url.Values{"fsidlist":{string(idsJSON)},"path":{actual}}
 if o.sekey!=""{form.Set("sekey",o.sekey)}
 query:=url.Values{"method":{"transfer"},"shareid":{o.shareID},"from":{o.shareUK}}
 return o.call(ctx,"POST","/rest/2.0/xpan/share",query,form,nil)
}

type oauthOwnedSources struct {requested map[string]bool; found map[string]manifest.File}
func (r *oauthOwnedSources) UpsertManifestPage(_ context.Context,_ string,_ []manifest.Directory,files []manifest.File)error{
 for _,file:=range files {if r.requested[file.SourceID] {r.found[file.SourceID]=file}}
 return nil
}
func (o *oauthBaidu) copyOwnSharedFiles(ctx context.Context,link baidu.ShareLink,ids []int64,dest string)error{
 if len(ids)>100 {return &baidu.TransferLimitError{Target:len(ids),Limit:100}}
 receiver:=&oauthOwnedSources{requested:map[string]bool{},found:map[string]manifest.File{}}
 for _,id:=range ids {receiver.requested[strconv.FormatInt(id,10)]=true}
 if err:=o.Scan(ctx,"own-share-resolution",link,baidu.ShareContext{},receiver);err!=nil{return err}
 items:=make([]map[string]string,0,len(ids))
 for _,id:=range ids{
  file,found:=receiver.found[strconv.FormatInt(id,10)]
  if !found || !strings.HasPrefix(file.SourcePath,"/") || path.Clean(file.SourcePath)!=file.SourcePath {
   return fmt.Errorf("owned Baidu share source could not be resolved safely")
  }
  items=append(items,map[string]string{"path":file.SourcePath,"dest":dest,"newname":file.Name,"ondup":"fail"})
 }
 body,_:=json.Marshal(items)
 form:=url.Values{"async":{"0"},"ondup":{"fail"},"filelist":{string(body)}}
 query:=url.Values{"method":{"filemanager"},"opera":{"copy"}}
 return o.call(ctx,"POST","/rest/2.0/xpan/file",query,form,nil)
}
func (o *oauthBaidu) OpenDownloadRange(ctx context.Context,virtual string,start,end int64)(*baidu.DownloadStream,error){
 actual,err:=o.physical(virtual);if err!=nil{return nil,err}
 if start<0||end<start{return nil,fmt.Errorf("invalid Baidu byte range")}
 entries,err:=o.listActual(ctx,path.Dir(actual));if err!=nil{return nil,err}
 var id int64
 for _,item:=range entries{if item.Path==actual && item.IsDir==0 {if id!=0{return nil,fmt.Errorf("duplicate Baidu file path")};id=item.FsID}}
 if id==0{return nil,fmt.Errorf("Baidu staged file not found")}
 fsids,_:=json.Marshal([]int64{id})
 query:=url.Values{"method":{"filemetas"},"fsids":{string(fsids)},"dlink":{"1"}}
 var meta struct {List []struct {
  FsID int64 `json:"fs_id"`
  Size int64 `json:"size"`
  Dlink string `json:"dlink"`
 } `json:"list"`}
 if err:=o.call(ctx,"GET","/rest/2.0/xpan/multimedia",query,nil,&meta);err!=nil{return nil,err}
 if len(meta.List)!=1||meta.List[0].FsID!=id||meta.List[0].Dlink==""{return nil,fmt.Errorf("invalid Baidu download metadata")}
 link,err:=url.Parse(meta.List[0].Dlink)
 if err!=nil || link.Scheme!="https" || link.User!=nil {return nil,fmt.Errorf("invalid Baidu download URL")}
 host:=strings.ToLower(link.Hostname())
 trusted:=host=="baidu.com" || strings.HasSuffix(host,".baidu.com") || host=="baidupcs.com" || strings.HasSuffix(host,".baidupcs.com")
 if o.baseURL!="https://pan.baidu.com" {
  testBase,parseErr:=url.Parse(o.baseURL)
  trusted=trusted || (parseErr==nil && host==strings.ToLower(testBase.Hostname()))
 }
 if !trusted{return nil,fmt.Errorf("Baidu download URL was not a trusted provider host")}
 values:=link.Query();values.Set("access_token",o.token);link.RawQuery=values.Encode()
 req,err:=http.NewRequestWithContext(ctx,"GET",link.String(),nil);if err!=nil{return nil,fmt.Errorf("invalid Baidu range download request")}
 req.Header.Set("User-Agent","pan.baidu.com")
 req.Header.Set("Range",fmt.Sprintf("bytes=%d-%d",start,end))
 resp,err:=o.client.Do(req);if err!=nil{return nil,fmt.Errorf("Baidu range stream failed")}
 if resp.StatusCode!=http.StatusPartialContent{
  resp.Body.Close()
  if resp.StatusCode==401||resp.StatusCode==403{return nil,baidu.ErrAuthRequired}
  return nil,baidu.ErrRangeNotHonored
 }
 contentRange:=resp.Header.Get("Content-Range")
 var actualStart,actualEnd,total int64
 if _,err=fmt.Sscanf(contentRange,"bytes %d-%d/%d",&actualStart,&actualEnd,&total);err!=nil||
  actualStart!=start||actualEnd!=end||total!=meta.List[0].Size||resp.ContentLength!=end-start+1 {
  resp.Body.Close();return nil,baidu.ErrRangeNotHonored
 }
 return &baidu.DownloadStream{Body:resp.Body,Start:start,End:end,Total:total,Remaining:end-start+1,Partial:true,
 ContentType:resp.Header.Get("Content-Type")},nil
}
var _ interface {
 HasLoginCookies() bool
 CookieString() string
 AccessSharePage(context.Context,baidu.ShareLink)(baidu.ShareContext,error)
 VerifyPassword(context.Context,baidu.ShareLink,baidu.ShareContext,string)error
 Scan(context.Context,string,baidu.ShareLink,baidu.ShareContext,manifest.Sink)error
 EnsureStagingDirectory(context.Context,string)error
 ListStagingDirectory(context.Context,string)([]baidu.RemoteFile,error)
 TransferFiles(context.Context,baidu.ShareLink,baidu.ShareContext,[]int64,string)error
 ListStagingPathForCleanup(context.Context,string)([]baidu.RemoteFile,error)
 DeleteStagingPath(context.Context,string)error
 OpenDownloadRange(context.Context,string,int64,int64)(*baidu.DownloadStream,error)
} = (*oauthBaidu)(nil)
