import {Draw} from './engine/draw.js';
import {loadGPTArt} from './components/gpt_art.js';
import {renderOpeningV8} from './scenes/opening_v8.js';
import {renderDrafts} from './scenes/drafts.js';

const canvas=document.getElementById('stage');
const g=canvas.getContext('2d',{alpha:false});
const d=new Draw(g,canvas.width,canvas.height);
const gptArt=await loadGPTArt();

export const DURATION=30;

export function renderFrame(t){
  t=Math.max(0,Math.min(DURATION,t));
  g.setTransform(1,0,0,1,0,0);
  g.clearRect(0,0,canvas.width,canvas.height);
  if(t<15)renderOpeningV8(d,t,gptArt);
  else renderDrafts(d,t);
  return canvas;
}

window.renderFrame=renderFrame;
window.GPT_MV_DURATION=DURATION;
window.GPT_MV_READY=true;

const params=new URLSearchParams(location.search);
if(params.has('t')){
  renderFrame(Number(params.get('t'))||0);
}else{
  let start=performance.now();
  const tick=(now)=>{const t=((now-start)/1000)%DURATION;renderFrame(t);requestAnimationFrame(tick)};
  requestAnimationFrame(tick);
}
