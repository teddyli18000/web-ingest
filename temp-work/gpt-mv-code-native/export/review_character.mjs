import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright-core';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const output=path.join(root,'out','character_plate_1080.png');
await fs.mkdir(path.dirname(output),{recursive:true});
const mime={'.html':'text/html','.js':'text/javascript','.json':'application/json','.css':'text/css'};
const server=http.createServer(async(req,res)=>{
  const url=new URL(req.url,'http://localhost');
  const name=url.pathname==='/'?'/index.html':url.pathname;
  const file=path.resolve(root,'.'+name);
  const content=await fs.readFile(file);
  res.writeHead(200,{'content-type':mime[path.extname(file)]||'application/octet-stream'});
  res.end(content);
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const browser=await chromium.launch({
  headless:true,
  executablePath:process.env.CHROME_PATH||'/usr/bin/google-chrome'
});
const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
await page.goto('http://127.0.0.1:'+server.address().port+'/?lab=character&t=0',{waitUntil:'networkidle'});
await page.waitForFunction(()=>window.GPT_MV_READY===true);
const meta=await page.evaluate(async()=>{
  const parts=await Promise.all(Array.from({length:4},(_,i)=>
    fetch('/assets/gpt/bust_plate.b64.'+i).then(r=>r.text())
  ));
  const image=new Image();
  image.src='data:image/webp;base64,'+parts.join('');
  await image.decode();
  const canvas=document.createElement('canvas');
  canvas.width=image.naturalWidth;canvas.height=image.naturalHeight;
  const g=canvas.getContext('2d',{willReadFrequently:true});
  g.drawImage(image,0,0);
  const data=g.getImageData(0,0,canvas.width,canvas.height).data;
  let empty=0,solid=0,partial=0;
  let minX=canvas.width,minY=canvas.height,maxX=-1,maxY=-1;
  for(let y=0;y<canvas.height;y++)for(let x=0;x<canvas.width;x++){
    const a=data[(y*canvas.width+x)*4+3];
    if(a===0)empty++;
    else if(a===255)solid++;
    else partial++;
    if(a>16){
      minX=Math.min(minX,x);minY=Math.min(minY,y);
      maxX=Math.max(maxX,x);maxY=Math.max(maxY,y);
    }
  }
  return {
    source:window.GPT_ART_SOURCE,
    width:canvas.width,height:canvas.height,
    transparent:empty,opaque:solid,partial,
    alphaBounds:[minX,minY,maxX+1,maxY+1],
    stageSize:[document.getElementById('stage').width,document.getElementById('stage').height]
  };
});
if(meta.source!=='gpt-bust-print-v2')throw new Error('wrong character source: '+meta.source);
if(meta.width!==550||meta.height!==640)throw new Error('unexpected plate dimensions');
if(meta.transparent===0||meta.opaque===0)throw new Error('missing transparency or opaque subject');
await page.evaluate(()=>window.renderFrame(0));
await page.locator('#stage').screenshot({path:output});
await fs.writeFile(path.join(root,'out','character_alpha.json'),JSON.stringify(meta,null,2)+'\n');
console.log(JSON.stringify(meta));
console.log(output);
await browser.close();
server.close();
