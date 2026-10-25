import {PALETTE as P} from '../engine/palette.js';
import {easeInOut,easeOut,lerp,prog,smooth} from '../engine/timing.js';
import {renderDraftsV9} from './drafts_v9.js';

const T3=25.20,T4=28.15,END=30;
const PAPER='rgba(255,253,248,.985)';
const MAP0=[110,475],GOOD=[805,485];

function art(d,model,dst,{crop='full',alpha=1,register=0,rot=0,cover=false}={}){
  if(register>0)model.register(d.g,dst,{crop,spread:register,alpha,rot});
  else model.draw(d.g,dst,{crop,alpha,rot,cover});
}
function base(d,t,{blue=.045,gold=.15,dark=.032}={}){
  d.paper(t*.28);
  d.glow(1510,220,680,P.gold,gold);
  d.glow(330,800,720,P.cobalt,blue);
  d.gradRect(0,760,1920,320,[[0,'rgba(23,32,51,0)'],[1,`rgba(23,32,51,${dark})`]],true);
  d.save(()=>{d.g.translate(-130,850);d.g.rotate(-.045);d.rect(0,0,2180,410,{fill:P.ink,alpha:.048});d.line(170,52,1700,52,{color:P.gold,width:6,alpha:.14});});
}
function pagePose(d,p,fn){const w=900,h=610;d.save(()=>{d.g.translate(p.cx,p.cy);d.g.rotate(p.rot);d.g.scale(p.scale,p.scale);d.g.translate(-w/2,-h/2);fn(w,h);});}
function correctedProof(d,w,h,{a=1,accent=P.cobalt,title=true}={}){
  d.rrect(18,22,w,h,18,{fill:P.ink,alpha:.045*a});
  d.rrect(0,0,w,h,18,{fill:PAPER,stroke:'rgba(53,65,92,.18)',width:1.5,alpha:a,shadow:.31*a});
  d.line(36,42,w-40,42,{color:accent,width:5,alpha:.48*a});
  if(title){d.text('REVISION / FINAL',42,88,{size:20,font:'mono',weight:700,color:P.ink2,alpha:.42*a});d.text('keep what matters.',42,128,{size:31,font:'serif',italic:true,color:P.ink,alpha:.62*a});}
  const pts=[[110,475],[240,390],[365,430],[500,315],[625,355],GOOD];
  for(let i=0;i<pts.length-1;i++){const p=pts[i],n=pts[i+1];d.line(p[0],p[1],n[0],n[1],{color:P.cobalt,width:6,alpha:.67*a});}
  for(let i=0;i<pts.length;i++)d.circle(pts[i][0],pts[i][1],i===0?8:6,{fill:i===pts.length-1?P.gold:P.cobalt,alpha:.82*a});
  // Wrong route remains as graphite residue.
  d.line(625,355,790,185,{color:P.ink2,width:3,alpha:.11*a});
  d.circle(790,185,40,{fill:null,stroke:'#d94b3d',width:3,alpha:.16*a});
}
function pointOnPage(p,pt){
  const w=900,h=610,x=(pt[0]-w/2)*p.scale,y=(pt[1]-h/2)*p.scale,c=Math.cos(p.rot),s=Math.sin(p.rot);
  return [p.cx+x*c-y*s,p.cy+x*s+y*c];
}
function userMark(d,x,y,a=1){d.glow(x,y,150,P.gold,.22*a);d.circle(x,y,11,{fill:P.gold,alpha:a});d.circle(x,y,36,{fill:null,stroke:P.gold2,width:2,alpha:.44*a});}
function paperBridge(d,from,to,k,{count=8}={}){
  if(k<=0)return;
  for(let i=0;i<count;i++){
    const u=i/(count-1),q=easeOut(prog(k,i*.065,.38+i*.065));if(q<=0)continue;
    const x=lerp(from[0],to[0],u),y=lerp(from[1],to[1],u)-Math.sin(u*Math.PI)*72;
    d.save(()=>{d.g.translate(x,y);d.g.rotate(lerp(-.12,.06,u));d.rrect(-51*q,-16,102*q,32,5,{fill:i%2?P.white:P.gold2,stroke:P.line,width:1,alpha:.94*q,shadow:.12});});
  }
}
function lensProof(d,t){
  const q=prog(t,T4-.48,T4+.52);if(q<=0||q>=1)return;
  const k=easeInOut(q),x=lerp(-1720,2090,k),y=lerp(230,470,k),w=1780,h=1280;
  d.save(()=>{
    const g=d.g;g.translate(x+w/2,y+h/2);g.rotate(-.085);g.translate(-w/2,-h/2);
    d.rrect(22,28,w,h,28,{fill:P.ink,alpha:.055,shadow:.30});d.rrect(0,0,w,h,28,{fill:'#fffdf8',stroke:'rgba(53,65,92,.16)',width:2,alpha:.995,shadow:.48});
    d.text('HANDOFF',130,230,{size:112,font:'serif',weight:700,color:P.ink,alpha:.12});
    d.text('/ FINAL',138,292,{size:27,font:'mono',weight:700,color:P.cobalt,alpha:.34});
    d.line(150,870,520,690,{color:P.cobalt,width:15,alpha:.27});d.line(520,690,810,760,{color:P.cobalt,width:15,alpha:.27});d.line(810,760,1160,510,{color:P.cobalt,width:15,alpha:.27});d.line(1160,510,1495,570,{color:P.cobalt,width:15,alpha:.27});
    d.circle(150,870,13,{fill:P.cobalt,alpha:.34});d.circle(1495,570,15,{fill:P.gold,alpha:.34});
    d.text('the answer leaves the page.',1040,1030,{size:46,font:'serif',italic:true,color:P.ink2,alpha:.20});
  });
}
function shotGive(d,t,model){
  base(d,t);
  const move=easeInOut(prog(t,T3,T3+1.55));
  const p={cx:lerp(1030,720,move),cy:lerp(555,610,move),rot:lerp(-.018,-.060,move),scale:lerp(.99,.78,move)};
  // Same actor geometry as shotPeel's end, then a deliberate camera push.
  const char={x:lerp(1320,1110,move),y:lerp(80,28,move),w:lerp(720,930,move),h:lerp(880,1050,move)};
  art(d,model,char,{crop:'full',alpha:1,register:5,rot:-.008});
  pagePose(d,p,(w,h)=>correctedProof(d,w,h,{a:1}));
  const user=easeOut(prog(t,T3+.55,T3+1.18));userMark(d,225,800,user);
  const from=pointOnPage(p,MAP0),bridge=easeOut(prog(t,T3+.90,T3+2.35));paperBridge(d,from,[260,800],bridge);
  // Route escapes the proof before the paper leaves frame.
  if(bridge>.15){const a=smooth(prog(bridge,.15,.82));d.line(from[0],from[1],lerp(from[0],290,a),lerp(from[1],790,a),{color:P.cobalt,width:6,alpha:.38*a});}
  const note=easeOut(prog(t,T3+.72,T3+1.45))*(1-smooth(prog(t,T4-.70,T4-.18)));
  d.text('not an answer to keep.',94,142,{size:22,font:'mono',weight:700,color:P.ink2,alpha:.30*note});
  d.text('something to use.',92,196,{size:46,font:'serif',italic:true,color:P.ink,alpha:.58*note});
  lensProof(d,t);
}
function shotHand(d,t,model){
  base(d,t,{blue:.055,gold:.17,dark:.026});
  const settle=easeOut(prog(t,T4,T4+.62));
  // Same master artwork, new camera distance: gesture close-up rather than another pose.
  art(d,model,{x:lerp(520,610,settle),y:lerp(-60,20,settle),w:1460,h:1080},{crop:'hand',alpha:1,register:lerp(7,4,settle),cover:true});
  const user=easeOut(prog(t,T4+.15,T4+.62));userMark(d,275,755,user);
  const from=[775,700],to=[315,755],bridge=easeOut(prog(t,T4+.08,T4+.90));paperBridge(d,from,to,bridge,{count:7});
  d.glow(690,680,240,P.cobalt,.08*bridge);
  const route=easeOut(prog(t,T4+.35,T4+1.15));d.line(755,692,lerp(755,326,route),lerp(692,750,route),{color:P.cobalt,width:7,alpha:.40*route});
  d.circle(755,692,9,{fill:P.cobalt,alpha:.65*route});
  // Small surviving proof edge: the paper has moved out of the way, not vanished.
  const edge=easeInOut(prog(t,T4,T4+.82));d.save(()=>{d.g.translate(lerp(-40,-330,edge),620);d.g.rotate(-.07);d.rrect(0,0,430,330,15,{fill:PAPER,stroke:P.line,width:1.2,alpha:.92,shadow:.22});d.line(34,42,350,42,{color:P.cobalt,width:5,alpha:.40});});
  const end=easeOut(prog(t,T4+.78,END-.32));d.text('REVISION / COMPLETE',88,982,{size:20,font:'mono',weight:700,color:P.ink2,alpha:.30*end});
  lensProof(d,t);
}

export function renderDraftsV10(d,t,model,poses){
  if(t<T3)return renderDraftsV9(d,t,model,poses);
  if(t<T4)return shotGive(d,t,model);
  return shotHand(d,t,model);
}

export const DRAFTS_V10_CUTS=[15,18.30,21.80,T3,T4,END];
