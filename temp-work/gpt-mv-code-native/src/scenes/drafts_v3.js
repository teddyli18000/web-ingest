import {PALETTE as P} from '../engine/palette.js';
import {easeInOut,easeOut,lerp,prog,smooth} from '../engine/timing.js';
import {renderOpeningV8} from './opening_v8.js';

const T0=15,T1=18.25,T2=21.55,T3=25.15,END=30;

function art(d,model,dst,{crop='full',alpha=1,register=0,flip=false,rot=0,cover=false}={}){
  if(register>0)model.register(d.g,dst,{crop,spread:register,alpha,flip,rot});
  else model.draw(d.g,dst,{crop,alpha,flip,rot,cover});
}
function base(d,t,{blue=.055,gold=.11,dark=.035}={}){
  d.paper(t*.27);d.glow(1510,220,650,P.gold,gold);d.glow(330,790,720,P.cobalt,blue);
  d.gradRect(0,760,1920,320,[[0,'rgba(23,32,51,0)'],[1,`rgba(23,32,51,${dark})`]],true);
}
function point(d,x,y,{color=P.gold,a=1,r=9,halo=30}={}){
  d.glow(x,y,halo*3,color,.14*a);d.circle(x,y,r,{fill:color,alpha:a});d.circle(x,y,halo,{fill:null,stroke:color,width:2,alpha:.34*a});
}
function pageTransform(d,{cx,cy,w,h,rot=0,scale=1},fn){d.save(()=>{const g=d.g;g.translate(cx,cy);g.rotate(rot);g.scale(scale,scale);g.translate(-w/2,-h/2);fn(w,h);});}
function sheet(d,w,h,{alpha=1,accent=P.gold,fill='rgba(255,253,248,.975)',shadow=.28}={}){
  d.rrect(17,20,w,h,18,{fill:P.ink,alpha:.045*alpha});d.rrect(0,0,w,h,18,{fill,stroke:'rgba(53,65,92,.17)',width:1.5,alpha,shadow:shadow*alpha});d.line(34,40,w-38,40,{color:accent,width:5,alpha:.46*alpha});
}
function cropMarks(d,w,h,a=.24){const m=12,l=26;for(const [x,y,sx,sy] of [[0,0,1,1],[w,0,-1,1],[0,h,1,-1],[w,h,-1,-1]]){d.line(x-sx*m,y,x+sx*l,y,{color:P.ink2,width:1.5,alpha:a});d.line(x,y-sy*m,x,y+sy*l,{color:P.ink2,width:1.5,alpha:a});}}
const ROUTE=[[110,580],[260,500],[405,535],[555,420],[690,472],[835,350]],GOOD=[900,590],BAD=[850,250];
function route(d,{a=1,color=P.cobalt,width=5,to='bad',ghost=0,progress=1}={}){
  const end=to==='good'?GOOD:BAD,pts=[...ROUTE.slice(0,-1),end],count=(pts.length-1)*Math.max(0,Math.min(1,progress));
  for(let i=0;i<pts.length-1;i++){const q=Math.max(0,Math.min(1,count-i));if(q<=0)continue;const p=pts[i],n=pts[i+1];d.line(p[0],p[1],lerp(p[0],n[0],q),lerp(p[1],n[1],q),{color,width,alpha:a*(.74-.06*i)*(1-.62*ghost)});}
}
function bridge(d,{a=1,ghost=0,peel=0}={}){
  for(let i=0;i<8;i++){
    const q=easeOut(prog(a,i*.06,.45+i*.06));if(q<=0)continue;const u=i/7;
    const wx=lerp(120,BAD[0],u),wy=lerp(580,BAD[1],u)-Math.sin(u*Math.PI)*50,gx=lerp(120,GOOD[0],u),gy=lerp(580,GOOD[1],u)-Math.sin(u*Math.PI)*54;
    const x=lerp(wx,gx,peel),y=lerp(wy,gy,peel)-Math.sin(peel*Math.PI)*38*(u>.38?1:0);
    d.save(()=>{d.g.translate(x,y);d.g.rotate(lerp(-.13,.08,u)+lerp(0,.035*(i-3.5),Math.sin(peel*Math.PI)));d.rrect(-48*q,-16,96*q,32,5,{fill:i%2?P.white:P.gold2,stroke:P.line,width:1.1,alpha:(.93-.48*ghost)*q,shadow:.12*(1-ghost)});});
  }
}
function deskShadow(d,a=1){d.save(()=>{d.g.translate(-120,850);d.g.rotate(-.045);d.rect(0,0,2160,390,{fill:P.ink,alpha:.055*a});d.line(180,52,1620,52,{color:P.gold,width:6,alpha:.16*a});});}
function nearSheet(d,q,{y=820,accent=P.gold,rot=-.11,w=600,h=210}={}){if(q<=0||q>=1)return;d.save(()=>{d.g.translate(lerp(2020,-660,easeInOut(q)),y);d.g.rotate(rot);d.rrect(0,0,w,h,14,{fill:P.white,stroke:P.line,width:1.3,alpha:.94,shadow:.38});d.line(36,46,w-80,46,{color:accent,width:7,alpha:.52});});}
function lerpColor(a,b,k){const parse=s=>s.match(/[0-9a-f]{2}/ig).map(v=>parseInt(v,16)),aa=parse(a),bb=parse(b);return '#'+aa.map((v,i)=>Math.round(lerp(v,bb[i],k)).toString(16).padStart(2,'0')).join('');}

function shotDesk(d,t,model){
  renderOpeningV8(d,14.999,model);
  const wipe=easeInOut(prog(t,T0,T0+1.15));if(wipe>0)d.save(()=>{const x=lerp(-560,-170,wipe),y=lerp(840,-220,wipe),w=2420,h=1510;d.g.translate(x+w/2,y+h/2);d.g.rotate(lerp(-.17,-.04,wipe));d.g.translate(-(x+w/2),-(y+h/2));d.rrect(x,y,w,h,36,{fill:P.white,stroke:'rgba(53,65,92,.14)',width:2,shadow:.58});d.line(x+130,y+112,x+w-200,y+112,{color:P.gold,width:8,alpha:.46});});
  const reveal=smooth(prog(wipe,.54,1));if(reveal<=0)return;d.alpha(reveal,()=>{base(d,t,{blue:.04,gold:.13});deskShadow(d,1);});
  const boardIn=easeOut(prog(t,T0+.70,T0+1.65)),cam=easeInOut(prog(t,T0+1.15,T1));
  pageTransform(d,{cx:lerp(1125,1175,cam),cy:lerp(570,545,cam),w:1080,h:720,rot:lerp(-.072,-.045,cam),scale:lerp(.93,1.02,cam)},(w,h)=>{
    sheet(d,w,h,{alpha:boardIn,accent:P.gold,shadow:.32});cropMarks(d,w,h,.22*boardIn);d.text('revision / 01',46,88,{size:22,font:'mono',weight:700,color:P.ink2,alpha:.44*boardIn});
    const build=easeOut(prog(t,T0+1.02,T1-.05));route(d,{a:.42*build,color:P.ink2,width:3,to:'bad',ghost:.42,progress:build});bridge(d,{a:build});point(d,BAD[0],BAD[1],{color:P.gold,a:build,r:9,halo:28});point(d,120,580,{color:P.cobalt,a:build,r:8,halo:24});
  });
  const charA=boardIn*(1-smooth(prog(t,T0+2.05,T1-.05)));if(charA>0)d.save(()=>{d.g.beginPath();d.g.rect(0,0,670,1080);d.g.clip();art(d,model,{x:-320,y:58,w:1050,h:980},{crop:'bust',alpha:charA,register:5});});
  nearSheet(d,prog(t,T0+.55,T0+1.55),{y:870,accent:P.cobalt,rot:-.13,w:540,h:185});
}

function shotCorrection(d,t,model){
  const push=easeInOut(prog(t,T1,T1+1.35)),peel=easeInOut(prog(t,T1+1.18,T2-.15)),recover=easeInOut(prog(t,T2-.72,T2));
  base(d,t,{blue:.045,gold:.105});deskShadow(d,.8);
  const pre={cx:lerp(1165,990,push),cy:lerp(545,655,push),rot:lerp(-.045,-.022,push),scale:lerp(1.02,1.40,push)},aligned={cx:1020,cy:555,rot:-.012,scale:.93};
  const board={cx:lerp(pre.cx,aligned.cx,recover),cy:lerp(pre.cy,aligned.cy,recover),w:1080,h:720,rot:lerp(pre.rot,aligned.rot,recover),scale:lerp(pre.scale,aligned.scale,recover)};
  pageTransform(d,board,(w,h)=>{
    sheet(d,w,h,{accent:P.gold,shadow:.32});cropMarks(d,w,h,.18);d.text('revision / 01',46,88,{size:22,font:'mono',weight:700,color:P.ink2,alpha:.36*(1-push)*(1-recover)});
    route(d,{a:.17,color:P.ink2,width:3,to:'bad',ghost:.65});bridge(d,{a:1,peel});point(d,120,580,{color:P.cobalt,a:1,r:8,halo:24});point(d,BAD[0],BAD[1],{color:P.gold,a:1-peel*.62,r:9,halo:28});
    const mark=easeOut(prog(t,T1+.50,T1+1.10));if(mark>0){point(d,GOOD[0],GOOD[1],{color:P.coral,a:mark,r:9,halo:28});d.circle(BAD[0],BAD[1],64,{fill:null,stroke:P.coral,width:5,alpha:.65*mark});const ar=easeOut(prog(t,T1+.72,T1+1.48));d.line(BAD[0]+45,BAD[1]+48,lerp(BAD[0]+45,GOOD[0]-28,ar),lerp(BAD[1]+48,GOOD[1]-26,ar),{color:P.coral,width:5,alpha:.72*ar});}
    if(peel>0){route(d,{a:.62*peel,color:P.cobalt,width:6,to:'good',progress:peel});point(d,GOOD[0],GOOD[1],{color:lerpColor(P.coral,P.gold,peel),a:peel,r:10,halo:32});}
  });
  const faceIn=easeOut(prog(t,T1+.25,T1+.78)),faceOut=1-smooth(prog(t,T1+1.55,T2-.50)),faceA=faceIn*faceOut;if(faceA>0){d.save(()=>{d.g.beginPath();d.g.rect(0,0,520,720);d.g.clip();art(d,model,{x:-255,y:-80,w:900,h:720},{crop:'close',alpha:.94*faceA,register:4,cover:true});});d.text('not there.',110,690,{size:32,font:'serif',italic:true,color:P.coral,alpha:.64*faceA});}
  nearSheet(d,prog(t,T1+.32,T1+1.35),{y:900,accent:P.gold,rot:-.12,w:650,h:205});
}

function proofFan(d,t,i,spread,align){
  const fan=[{cx:650,cy:650,rot:-.13,scale:.78,c:P.coral,to:'bad'},{cx:1010,cy:535,rot:.045,scale:.86,c:P.cobalt,to:'good'},{cx:1370,cy:600,rot:.12,scale:.80,c:P.gold,to:'good'}][i],stack={cx:1020,cy:555,rot:-.012,scale:.93};
  const sx=lerp(stack.cx,fan.cx,spread),sy=lerp(stack.cy,fan.cy,spread),sr=lerp(stack.rot,fan.rot,spread),ss=lerp(stack.scale,fan.scale,spread);
  const cx=lerp(sx,stack.cx,align),cy=lerp(sy,stack.cy,align),rot=lerp(sr,stack.rot,align),scale=lerp(ss,stack.scale,align),alpha=i===2?.80:.76*spread;
  if(alpha<=0)return;
  pageTransform(d,{cx,cy,w:1040,h:650,rot,scale},(w,h)=>{
    sheet(d,w,h,{alpha,accent:fan.c,fill:i===1?'rgba(239,244,255,.78)':'rgba(255,253,248,.80)',shadow:.19});route(d,{a:(i===0?.34:.54)*Math.max(.32,spread),color:fan.c,width:i===2?6:4,to:fan.to,ghost:i===0?.45:.10});d.line(38,58,310,58,{color:fan.c,width:6,alpha:.46*alpha});cropMarks(d,w,h,.13*alpha);
  });
}
function shotProofs(d,t){
  const spread=easeInOut(prog(t,T2+.10,T2+1.00)),align=easeInOut(prog(t,T2+1.50,T3-.28)),pan=easeInOut(prog(t,T2,T3));
  base(d,t,{blue:.075,gold:.075});deskShadow(d,.62);d.text('keep the evidence.',lerp(112,70,pan),128,{size:43,font:'serif',italic:true,color:P.ink,alpha:.70});d.text('three passes · one correction',lerp(114,82,pan),170,{size:20,font:'mono',weight:700,color:P.ink2,alpha:.40});
  for(let i=0;i<3;i++)proofFan(d,t,i,spread,align);
  const pin=easeOut(prog(t,T2+.45,T2+1.10));if(pin>0)point(d,1490,770,{color:lerpColor(P.coral,P.gold,align),a:.92*pin,r:9,halo:30});
  for(let i=0;i<3;i++){const q=prog(t,T2+.30+i*.18,T2+1.35+i*.18);nearSheet(d,q,{y:900-i*145,accent:i===0?P.coral:i===1?P.cobalt:P.gold,rot:-.12+i*.07,w:460,h:145});}
}

function shotFinal(d,t,model){
  const settle=easeInOut(prog(t,T3,T3+.88)),clean=easeOut(prog(t,T3+.25,T3+1.35)),drift=Math.sin((t-T3)*.48)*5;
  base(d,t,{blue:.045,gold:.16});deskShadow(d,.48);
  // Full-opacity character is already behind the aligned proof; the sliding paper edge reveals her.
  const breath=Math.sin((t-T3)*1.25)*4;art(d,model,{x:1190,y:88+breath,w:770,h:910},{crop:'full',alpha:1,register:6});
  const board={cx:lerp(1020,865,settle),cy:555+drift,w:1040,h:650,rot:lerp(-.012,-.020,settle),scale:lerp(.93,1.02,settle)};
  pageTransform(d,board,(w,h)=>{
    sheet(d,w,h,{accent:P.gold,fill:'rgba(255,253,248,.995)',shadow:.31});cropMarks(d,w,h,.22);route(d,{a:.11,color:P.ink2,width:3,to:'bad',ghost:.82});route(d,{a:.70*clean,color:P.cobalt,width:6,to:'good',progress:clean});point(d,110,580,{color:P.cobalt,a:clean,r:8,halo:25});point(d,GOOD[0],GOOD[1],{color:P.gold,a:clean,r:10,halo:31});d.text('revision / final',46,86,{size:21,font:'mono',weight:700,color:P.ink2,alpha:.40});const words=easeOut(prog(t,T3+.88,T3+1.72));d.text('keep what matters.',66,164,{size:51,font:'serif',italic:true,color:P.ink,alpha:.80*words});d.line(68,188,68+440*words,188,{color:P.gold,width:5,alpha:.54*words});
  });
  const user=easeOut(prog(t,T3+1.35,T3+2.05));if(user>0)point(d,1000,790,{color:P.gold,a:user,r:9,halo:30});
  const link=easeOut(prog(t,T3+1.55,T3+2.70));if(link>0)for(let i=0;i<5;i++){const q=easeOut(prog(link,i*.09,.45+i*.09)),x=lerp(1290,1024,i/4),y=lerp(700,790,i/4)-Math.sin(i/4*Math.PI)*34;d.save(()=>{d.g.translate(x,y);d.g.rotate(-.08+i*.025);d.rrect(-42*q,-13,84*q,26,4,{fill:i%2?P.white:P.gold2,stroke:P.line,width:1,alpha:.88*q});});}
  for(let i=0;i<2;i++){const q=prog(t,T3+.48+i*.30,END-.18+i*.08);nearSheet(d,q,{y:910-i*170,accent:i?P.cobalt:P.gold,rot:-.14+i*.08,w:450,h:155});}
  const quiet=easeOut(prog(t,28.70,29.60));d.text('still revisable.',150,997,{size:26,font:'serif',italic:true,color:P.ink2,alpha:.46*quiet});
}

export function renderDraftsV3(d,t,model){if(t<T1)return shotDesk(d,t,model);if(t<T2)return shotCorrection(d,t,model);if(t<T3)return shotProofs(d,t,model);return shotFinal(d,t,model);}
export const DRAFTS_V3_CUTS=[T0,T1,T2,T3,END];
