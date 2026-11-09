import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright-core';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const out=path.resolve(process.argv[2]||'out/opening-v12-stills');
const times=process.argv[3]?process.argv[3].split(',').map(Number):[.58,1.55,2.52,3.37,4.62,5.48,6.86,7.82,8.92,9.92,11.25,12.15,13.42,14.72,15.18];
await fs.mkdir(out,{recursive:true});
const types={'.html':'text/html','.js':'text/javascript','.webp':'image/webp','.png':'image/png','.json':'application/json'};
const server=http.createServer(async(req,res)=>{
  const url=decodeURIComponent((req.url||'/').split('?')[0]);
  const file=path.resolve(root,'.'+(url==='/'?'/index.html':url));
  try{
    const bytes=await fs.readFile(file);
    res.writeHead(200,{'content-type':types[path.extname(file)]||'application/octet-stream'});
    res.end(bytes);
  }catch(e){res.writeHead(404);res.end('not found');}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'/usr/bin/google-chrome',headless:true});
try{
  const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
  page.on('pageerror',e=>console.error('Page error:',e.message));
  await page.goto('http://127.0.0.1:'+server.address().port+'/?t=0',{waitUntil:'networkidle'});
  await page.waitForFunction(()=>window.GPT_MV_READY===true);
  for(const t of times){
    await page.evaluate(time=>window.renderFrame(time),t);
    const p=path.join(out,'t-'+t.toFixed(2).replace('.','-')+'.png');
    await page.locator('#stage').screenshot({path:p});
    console.log(p);
  }
}finally{await browser.close();server.close();}
