import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright-core';

const HERE=path.dirname(fileURLToPath(import.meta.url));
const ROOT=path.resolve(HERE,'..');
const OUT=path.resolve(process.argv[2]||path.join(ROOT,'out','character_lab.png'));
await fs.mkdir(path.dirname(OUT),{recursive:true});
const mime={'.html':'text/html','.js':'text/javascript','.css':'text/css','.webp':'image/webp','.png':'image/png'};
const server=http.createServer(async(req,res)=>{
  try{
    let rel=decodeURIComponent((req.url||'/').split('?')[0]); if(rel==='/')rel='/character_lab.html';
    const full=path.resolve(ROOT,'.'+rel); if(!full.startsWith(ROOT))throw new Error('bad path');
    const data=await fs.readFile(full); res.writeHead(200,{'content-type':mime[path.extname(full)]||'application/octet-stream','cache-control':'no-store'}); res.end(data);
  }catch(err){console.error('HTTP',req.url,err.message);res.writeHead(404);res.end('not found')}
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const port=server.address().port;
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||'/usr/bin/google-chrome'});
try{
  const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
  page.on('console',m=>console.log('PAGE',m.type(),m.text()));
  page.on('pageerror',e=>console.error('PAGEERROR',e.stack||e.message));
  const response=await page.goto(`http://127.0.0.1:${port}/character_lab.html`,{waitUntil:'networkidle',timeout:15000});
  console.log('page_status',response?.status());
  await page.waitForFunction(()=>window.GPT_ART_READY===true,null,{timeout:10000});
  await page.locator('#stage').screenshot({path:OUT,timeout:10000});
  console.log(OUT);
}finally{
  await browser.close(); server.close();
}
