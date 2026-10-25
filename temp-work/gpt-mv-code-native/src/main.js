import {Draw} from './engine/draw.js';
import {loadGPTArt} from './components/gpt_art.js';
import {loadGPTPoses} from './components/gpt_poses.js';
import {renderOpeningV8} from './scenes/opening_v8.js';
import {renderDraftsV10} from './scenes/drafts_v10.js';
import {renderConstructV2} from './scenes/construct_v2.js';

const canvas=document.getElementById('stage');
const g=canvas.getContext('2d',{alpha:false});
const d=new Draw(g,canvas.width,canvas.height);
const [gptArt,gptPoses]=await Promise.all([loadGPTArt(),loadGPTPoses()]);

export const DURATION=45;

export function renderFrame(t){
  t=Math.max(0,Math.min(DURATION,t));
  g.setTransform(1,0,0,1,0,0);
  g.clearRect(0,0,canvas.width,canvas.height);
  if(t<15)renderOpeningV8(d,t,gptArt);
  else if(t<30)renderDraftsV10(d,t,gptArt,gptPoses);
  else renderConstructV2(d,t,gptArt,gptPoses);
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
