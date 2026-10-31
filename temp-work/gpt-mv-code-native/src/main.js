import {Draw} from './engine/draw.js';
import {loadGPTArt} from './components/gpt_art.js';
import {loadGPTPoses} from './components/gpt_poses.js';
import {renderOpeningV11} from './scenes/opening_v11.js';
import {renderDraftsV13} from './scenes/drafts_v13.js';
import {renderConstructV6} from './scenes/construct_v6.js';
import {renderEndingV3} from './scenes/ending_v3.js';

const canvas=document.getElementById('stage');
const g=canvas.getContext('2d',{alpha:false});
const d=new Draw(g,canvas.width,canvas.height);
const [gptArt,gptPoses]=await Promise.all([loadGPTArt(),loadGPTPoses()]);

export const DURATION=60;
const CAMERA_CUTS=[0,3.40,7.15,11.10,15,18.35,21.80,25.20,28.15,30,33.20,36.40,40.55,45];

function withShotCamera(t,fn){
  let i=-1;
  for(let j=0;j<CAMERA_CUTS.length-1;j++)if(t>=CAMERA_CUTS[j]&&t<CAMERA_CUTS[j+1]){i=j;break;}
  if(i<0)return fn();
  const a=CAMERA_CUTS[i],b=CAMERA_CUTS[i+1],raw=Math.max(0,Math.min(1,(t-a)/(b-a))),u=raw*raw*(3-2*raw);
  const dir=i%2?-1:1,s=1.012+.012*u,dx=dir*(-7+14*u),dy=4-8*u;
  g.save();g.translate(960,540);g.scale(s,s);g.translate(-960+dx,-540+dy);fn();g.restore();
}

export function renderFrame(t){
  t=Math.max(0,Math.min(DURATION,t));
  g.setTransform(1,0,0,1,0,0);
  g.clearRect(0,0,canvas.width,canvas.height);
  const body=()=>{
    if(t<15)renderOpeningV11(d,t,gptArt);
    else if(t<30)renderDraftsV13(d,t,gptArt,gptPoses);
    else renderConstructV6(d,t,gptArt,gptPoses);
  };
  if(t<45)withShotCamera(t,body);else renderEndingV3(d,t,gptArt,gptPoses);
  return canvas;
}

window.renderFrame=renderFrame;
window.GPT_MV_DURATION=DURATION;
window.GPT_MV_READY=true;
window.GPT_ART_SOURCE=gptArt.source;
window.GPT_POSES_READY=true;

const params=new URLSearchParams(location.search);
if(params.has('t'))renderFrame(Number(params.get('t'))||0);
else{let start=performance.now();const tick=now=>{const t=((now-start)/1000)%DURATION;renderFrame(t);requestAnimationFrame(tick)};requestAnimationFrame(tick);}
