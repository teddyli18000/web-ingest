import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {chromium} from 'playwright';

const HERE=path.dirname(fileURLToPath(import.meta.url));
const ROOT=path.resolve(HERE,'..');

function arg(name,def){const i=process.argv.indexOf(`--${name}`);return i>=0?process.argv[i+1]:def}
const width=Number(arg('width','960')),height=Number(arg('height','540')),fps=Number(arg('fps','18'));
const start=Number(arg('start','0')),end=Number(arg('end','15'));
const out=path.resolve(arg('out',path.join(ROOT,'out','gate01.mp4')));
const frames=path.join(path.dirname(out),'.frames-code-native');
await fs.mkdir(path.dirname(out),{recursive:true});
await fs.rm(frames,{recursive:true,force:true});await fs.mkdir(frames,{recursive:true});

const mime={'.html':'text/html','.js':'text/javascript','.json':'application/json','.css':'text/css'};
const server=http.createServer(async(req,res)=>{
  try{
    let rel=decodeURIComponent((req.url||'/').split('?')[0]);if(rel==='/')rel='/index.html';
    const full=path.resolve(ROOT,'.'+rel);if(!full.startsWith(ROOT))throw new Error('bad path');
    const data=await fs.readFile(full);res.writeHead(200,{'content-type':mime[path.extname(full)]||'application/octet-stream','cache-control':'no-store'});res.end(data);
  }catch{res.writeHead(404);res.end('not found')}
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const port=server.address().port;
const browser=await chromium.launch({headless:true});
const page=await browser.newPage({viewport:{width,height},deviceScaleFactor:1});
await page.goto(`http://127.0.0.1:${port}/`,{waitUntil:'networkidle'});
await page.waitForFunction(()=>window.GPT_MV_READY===true);
// Important: the Canvas stays 1920×1080 internally. The viewport only scales its CSS presentation.
// Scene code therefore uses one stable coordinate system at preview, CI, 1080p and 4K export.

const total=Math.round((end-start)*fps),canvas=page.locator('#stage');
for(let n=0;n<total;n++){
  const t=start+n/fps;await page.evaluate(t=>window.renderFrame(t),t);
  await canvas.screenshot({path:path.join(frames,`f-${String(n).padStart(5,'0')}.png`)});
  if(n%(fps*2)===0)console.log(`frame ${n}/${total} t=${t.toFixed(2)}`);
}
await browser.close();server.close();

const video=out.replace(/\.mp4$/i,'.video.mp4');
let r=spawnSync('ffmpeg',['-y','-hide_banner','-loglevel','error','-framerate',String(fps),'-i',path.join(frames,'f-%05d.png'),'-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p',video],{stdio:'inherit'});
if(r.status!==0)process.exit(r.status||1);
const dur=end-start;
const audio=`0.012*sin(2*PI*146.83*t)+0.009*sin(2*PI*220*t)+0.006*sin(2*PI*293.66*t)+0.010*sin(2*PI*659.25*t)*exp(-7*mod(t\\,2.07))`;
r=spawnSync('ffmpeg',['-y','-hide_banner','-loglevel','error','-i',video,'-f','lavfi','-t',String(dur),'-i',`aevalsrc=${audio}:s=48000`,'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',out],{stdio:'inherit'});
if(r.status!==0)process.exit(r.status||1);
await fs.rm(video,{force:true});

const marks=[.6,2.3,4.2,6.2,7.7,9.3,11.2,13.1,14.6].filter(t=>t>=start&&t<end).map(t=>Math.max(0,Math.min(total-1,Math.round((t-start)*fps))));
const expr=marks.map(n=>`eq(n\\,${n})`).join('+');
const sheet=out.replace(/\.mp4$/i,'.contact.jpg');
r=spawnSync('ffmpeg',['-y','-hide_banner','-loglevel','error','-i',out,'-vf',`select='${expr}',scale=480:-2,tile=3x3:padding=5:margin=5:color=white`,'-frames:v','1',sheet],{stdio:'inherit'});
if(r.status!==0)process.exit(r.status||1);
spawnSync('ffmpeg',['-v','error','-i',out,'-f','null','-'],{stdio:'inherit'});
console.log(out);console.log(sheet);
