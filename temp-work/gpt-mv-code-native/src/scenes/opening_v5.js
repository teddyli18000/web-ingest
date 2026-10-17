import {PALETTE as P} from '../engine/palette.js';
import {easeInOut,easeOut,lerp,prog,smooth,beatPulse} from '../engine/timing.js';
import {cursor} from '../components/chat.js';

const BPM=116,OFF=.28,PB=60/BPM;
const B=n=>OFF+n*PB;
const C1=B(6),C2=B(13),C3=B(20),END=15;
const P0={x:850,y:110,w:730,h:805};
const P1={x:-170,y:30,w:1080,h:1000};
const PROMPT={x:390,y:390,w:1290,h:280};

function base(d,t,{dark=.07,blue=.08,warm=.08}={}){
  d.paper(t*.32);d.glow(420,720,700,P.cobalt,blue);d.glow(1510,230,520,P.gold,warm);
  d.gradRect(0,760,1920,320,[[0,'rgba(23,32,51,0)'],[.55,`rgba(23,32,51,${dark*.32})`],[1,`rgba(23,32,51,${dark})`]],true);
}
function camera(d,{zoom=1,x=0,y=0,rot=0}={},fn){d.save(()=>{const g=d.g;g.translate(960,540);g.scale(zoom,zoom);g.rotate(rot);g.translate(-960+x,-540+y);fn();});}
function art(d,model,dst,{crop='full',alpha=1,register=0}={}){
  if(register>0)model.register(d.g,dst,{crop,spread:register,alpha});
  else model.draw(d.g,dst,{crop,alpha});
}
function cropMarks(d,a=.26){const m=42,l=38;for(const [x,y,sx,sy] of [[m,m,1,1],[1878,m,-1,1],[m,1038,1,-1],[1878,1038,-1,-1]]){d.line(x,y,x+sx*l,y,{color:P.ink2,width:2,alpha:a});d.line(x,y,x,y+sy*l,{color:P.ink2,width:2,alpha:a});}}
function inkShelf(d,a=1){d.save(()=>{d.g.translate(-100,835);d.g.rotate(-.032);d.rect(0,0,820,300,{fill:P.ink,alpha:.095*a});d.line(80,62,670,62,{color:P.cobalt,width:7,alpha:.20*a});});}
function sheet(d,x,y,w,h,{rot=0,alpha=1,accent=P.cobalt,shadow=.26}={}){d.save(()=>{d.g.translate(x+w/2,y+h/2);d.g.rotate(rot);d.g.translate(-(x+w/2),-(y+h/2));d.rrect(x+12,y+18,w,h,14,{fill:P.ink,alpha:.055*alpha});d.rrect(x,y,w,h,14,{fill:'rgba(255,253,248,.97)',stroke:'rgba(53,65,92,.18)',width:1.5,alpha,shadow});d.line(x+20,y+26,x+w-22,y+26,{color:accent,width:5,alpha:.62*alpha});});}

// Four distinct physical objects. They must be identifiable by shape before their labels.
function contextObject(d,x,y,s=1,a=1,rot=-.04){const w=310*s,h=146*s;sheet(d,x,y,w,h,{rot,alpha:a,accent:P.cobalt});d.save(()=>{d.g.translate(x,y);d.g.rotate(rot);d.text('“',30*s,91*s,{size:74*s,font:'serif',weight:700,color:P.cobalt,alpha:.55*a});for(let i=0;i<3;i++)d.rrect(88*s,(50+i*25)*s,(178-i*26)*s,7*s,3*s,{fill:P.line,alpha:.36*a});});}
function memoryObject(d,x,y,s=1,a=1,rot=.035){const w=282*s,h=164*s;d.save(()=>{d.g.translate(x+w/2,y+h/2);d.g.rotate(rot);d.g.translate(-(x+w/2),-(y+h/2));for(let k=2;k>=0;k--)d.rrect(x+k*10*s,y-k*9*s,w,h,13*s,{fill:k?'#e7dfd0':'#fffdfa',stroke:P.line,width:1.1,alpha:a,shadow:k?0:.22});d.rrect(x+28*s,y-12*s,92*s,30*s,8*s,{fill:P.ink2,alpha:.16*a});for(let i=0;i<4;i++){d.circle(x+30*s,y+(51+i*25)*s,5*s,{fill:i===0?P.gold:P.cobalt,alpha:.52*a});d.rrect(x+50*s,y+(47+i*25)*s,(178-i*18)*s,7*s,3*s,{fill:P.line,alpha:.34*a});}});}
function toolsObject(d,x,y,s=1,a=1,rot=-.025){const w=288*s,h=160*s;sheet(d,x,y,w,h,{rot,alpha:a,accent:P.gold});d.save(()=>{d.g.translate(x+w/2,y+h/2);d.g.rotate(rot);d.g.translate(-(x+w/2),-(y+h/2));d.text('<>',x+34*s,y+102*s,{size:42*s,font:'mono',weight:700,color:P.ink2,alpha:.68*a});d.circle(x+160*s,y+77*s,27*s,{fill:null,stroke:P.cobalt,width:5*s,alpha:.55*a});d.line(x+179*s,y+97*s,x+208*s,y+124*s,{color:P.cobalt,width:6*s,alpha:.55*a});for(let i=0;i<4;i++){const ang=i*Math.PI/2;d.circle(x+242*s+Math.cos(ang)*17*s,y+73*s+Math.sin(ang)*17*s,7*s,{fill:i%2?P.gold:P.cobalt,alpha:.72*a});}});}
function styleObject(d,x,y,s=1,a=1,rot=.04){const w=300*s,h=170*s;d.save(()=>{d.g.translate(x+w/2,y+h/2);d.g.rotate(rot);d.g.translate(-(x+w/2),-(y+h/2));for(let i=2;i>=0;i--){const xx=x+28*i*s,rr=(-.09+i*.085);d.save(()=>{d.g.translate(xx+96*s,y+88*s);d.g.rotate(rr);d.g.translate(-(xx+96*s),-(y+88*s));d.rrect(xx,y,192*s,162*s,15*s,{fill:i===0?'#fffdfa':i===1?'#e7dfd0':'#dbe5fb',stroke:P.line,width:1,alpha:a,shadow:i===0?.22:0});d.text(i===0?'Aa':i===1?'01':'A',xx+96*s,y+103*s,{size:(i===1?35:46)*s,font:i===0?'serif':i===1?'mono':'sans',weight:700,align:'center',color:i===2?P.cobalt:P.ink2,alpha:.72*a});});}});}
function objectsAt(d,items,a=1){contextObject(d,...items.context,a);memoryObject(d,...items.memory,a);toolsObject(d,...items.tools,a);styleObject(d,...items.style,a);}

function buildFrame(d,t,alpha=1){const k=easeInOut(prog(t,.55,2.45));const x=lerp(560,430,k),y=lerp(420,235,k),w=lerp(800,1200,k),h=lerp(240,650,k);d.rrect(x,y,w,h,lerp(60,28,k),{fill:'rgba(255,253,248,.38)',stroke:'rgba(47,102,213,.30)',width:2.5,alpha:.92*alpha,shadow:.38*k});if(k>.25){const q=smooth(prog(k,.25,.8));d.line(x+280*k,y+26,x+280*k,y+h-26,{color:P.line,width:2,alpha:.55*q*alpha});d.line(x+280*k,y+95*k,x+w-26,y+95*k,{color:P.line,width:2,alpha:.48*q*alpha});}return{x,y,w,h,k};}

function shotBuild(d,t,model){base(d,t,{dark:.12,blue:.08,warm:.07});cropMarks(d,.22);inkShelf(d,.8);
  const pulse=beatPulse(t,BPM,OFF);const F=buildFrame(d,t);
  // Four rails create the frame before the interface exists.
  const rails=[[80,245,520,245,P.cobalt],[1840,820,1420,820,P.gold],[350,1030,350,700,P.ink2],[1610,40,1610,340,P.cobalt2]];
  rails.forEach(([x1,y1,x2,y2,c],i)=>{const q=easeOut(prog(t,.18+i*.12,.92+i*.12));d.line(x1,y1,lerp(x1,x2,q),lerp(y1,y2,q),{color:c,width:3+1.5*pulse,alpha:.72});});
  const char=easeOut(prog(t,1.0,2.25));if(char>0){d.save(()=>{d.g.beginPath();d.g.roundRect(F.x,F.y,F.w,F.h,28);d.g.clip();art(d,model,P0,{crop:'bust',alpha:char,register:6});});}
  const items={context:[520,280,.72,1,-.035],memory:[810,280,.72,1,.025],tools:[1080,280,.72,1,-.025],style:[1350,278,.72,1,.032]};
  Object.entries(items).forEach(([key,v],i)=>{const a=easeOut(prog(t,1.45+i*.16,1.92+i*.16));if(a<=0)return;const vv=[v[0],v[1]-(1-a)*170,v[2],a,v[4]];({context:contextObject,memory:memoryObject,tools:toolsObject,style:styleObject}[key])(d,...vv);});
  const lock=easeOut(prog(t,C1-.45,C1-.04));if(lock>0)for(const [x,y] of [[430,235],[1630,235],[430,885],[1630,885]])d.circle(x,y,28*(1-lock)+5,{fill:null,stroke:P.cobalt,width:3,alpha:.60*(1-lock)});
  d.text('four kinds of context. one answer.',86,958,{size:31,font:'serif',italic:true,color:P.ink2,alpha:.50*(1-smooth(prog(t,C1-.72,C1)))});
}

function shotContext(d,t,model){const u=prog(t,C1,C2),push=easeInOut(prog(t,C1,C1+.72)),dock=easeInOut(prog(t,C2-.92,C2));base(d,t,{dark:.14,blue:.12,warm:.12});cropMarks(d,.20*(1-dock));inkShelf(d,.9);
  // First 0.72 s inherits exactly shot 1's character/frame, then camera pushes through it.
  const dst={x:lerp(P0.x,P1.x,push),y:lerp(P0.y,P1.y,push),w:lerp(P0.w,P1.w,push),h:lerp(P0.h,P1.h,push)};
  const frameA=1-smooth(prog(t,C1+.18,C1+.78));if(frameA>0){d.rrect(430,235,1200,650,28,{fill:'rgba(255,253,248,.28)',stroke:'rgba(47,102,213,.26)',width:2,alpha:frameA,shadow:.34});d.line(710,260,710,860,{color:P.line,width:2,alpha:.45*frameA});}
  art(d,model,dst,{crop:'bust',register:7});
  const starts={context:[520,280,.72,-.035],memory:[810,280,.72,.025],tools:[1080,280,.72,-.025],style:[1350,278,.72,.032]};
  const ends={context:[1130,145,.88,-.045],memory:[1450,280,.82,.035],tools:[1070,655,.88,.032],style:[1440,700,.83,-.04]};
  for(const key of Object.keys(starts)){
    const s=starts[key],e=ends[key],i=['context','memory','tools','style'].indexOf(key),q=easeInOut(prog(t,C1+.18+i*.09,C2-1.05+i*.04));let x=lerp(s[0],e[0],q),y=lerp(s[1],e[1],q)+Math.sin(q*Math.PI)*(i<2?120:-115),sc=lerp(s[2],e[2],q),rot=lerp(s[3],e[3],q);
    if(dock>0){const sx=[470,760,1040,1320][i];x=lerp(x,sx,dock);y=lerp(y,440,dock);sc=lerp(sc,.70,dock);rot=lerp(rot,0,dock);}
    ({context:contextObject,memory:memoryObject,tools:toolsObject,style:styleObject}[key])(d,x,y,sc,1,rot);
  }
  // A foreground proof sheet crosses very close to lens for a third depth plane.
  const fg=prog(t,C1+.55,C1+1.70);if(fg>0&&fg<1)d.save(()=>{d.g.translate(lerp(1980,-520,easeInOut(fg)),865);d.g.rotate(-.12);d.rrect(0,0,650,250,18,{fill:P.white,stroke:P.line,width:2,shadow:.52});d.line(48,55,510,55,{color:P.gold,width:9,alpha:.65});d.text('draft',48,104,{size:28,font:'mono',color:P.ink2,alpha:.44});});
  // Dock becomes the exact prompt geometry used by shot 3.
  if(dock>0){d.rrect(PROMPT.x,PROMPT.y,PROMPT.w,PROMPT.h,38,{fill:'rgba(255,253,248,.97)',stroke:'rgba(53,65,92,.18)',width:2,shadow:.55,alpha:dock});d.circle(PROMPT.x+60,PROMPT.y+58,16,{fill:P.gold,alpha:.90*dock});d.circle(PROMPT.x+PROMPT.w-76,PROMPT.y+PROMPT.h-64,30,{fill:P.line,alpha:.8*dock});}
  const cap=easeOut(prog(t,C1+1.15,C2-1.05))*(1-dock);d.text('context is material, not the answer.',1250,958,{size:34,font:'serif',italic:true,align:'center',color:P.ink,alpha:.62*cap});
}

function typing(t){const a='make it impressive.',b='make it worth watching.',q=(t-C2)/PB;let s='',del=false;if(q<1.65)s=a.slice(0,Math.floor(prog(q,0,1.48)*a.length));else if(q<2.25)s=a;else if(q<3.25){s=a.slice(0,Math.ceil((1-prog(q,2.25,3.25))*a.length));del=true;}else if(q<3.72)s='';else s=b.slice(0,Math.floor(prog(q,3.72,6.35)*b.length));return{s,del,done:s===b,final:b};}
function promptBox(d,t,typed,{alpha=1,fold=0}={}){const k=easeInOut(fold),x=lerp(PROMPT.x,500,k),y=lerp(PROMPT.y,510,k),w=lerp(PROMPT.w,1080,k),h=lerp(PROMPT.h,160,k);d.rrect(x+16,y+22,w,h,38,{fill:P.ink,alpha:.05*alpha});d.rrect(x,y,w,h,38,{fill:'rgba(255,253,248,.985)',stroke:'rgba(53,65,92,.18)',width:2,shadow:.58,alpha});d.circle(x+60,y+58,16,{fill:P.gold,alpha:.92*alpha});if(k<.45)d.text('you',x+92,y+67,{size:24,weight:700,color:P.ink2,alpha:.58*alpha*(1-k)});d.text(typed.s,x+58,y+lerp(168,98,k),{size:lerp(50,40,k),color:P.ink,weight:450,alpha});const tw=d.measure(typed.s,{size:lerp(50,40,k)});if(Math.floor(t*3.2)%2===0&&k<.42)d.rect(x+62+tw,y+118,4,62,{fill:typed.del?P.coral:P.cobalt,alpha:.82*alpha});d.circle(x+w-76,y+h-64,30,{fill:typed.done?P.cobalt:P.line,alpha:.90*alpha});if(typed.done){d.line(x+w-87,y+h-64,x+w-66,y+h-64,{color:P.white,width:4,alpha});d.line(x+w-67,y+h-64,x+w-76,y+h-73,{color:P.white,width:4,alpha});}return{x,y,w,h};}

function shotPrompt(d,t,model){const u=prog(t,C2,C3),typed=typing(t),send=easeOut(prog(t,C3-.58,C3));base(d,t,{dark:.12,blue:.08,warm:.08});
  // Same character geometry as the end of shot 2. Only the crop window changes after the cut.
  d.save(()=>{d.g.beginPath();d.g.rect(0,0,540,1080);d.g.clip();art(d,model,P1,{crop:'bust',alpha:.90,register:5});});
  d.rect(0,0,540,1080,{fill:P.cobalt,alpha:.028});
  const box=promptBox(d,t,typed,{fold:send});
  const key=Math.floor((t-C2)*12);for(let i=0;i<11;i++){const age=((key-i)+100)%11/11,a=.22*(1-age)*(1-send);d.rrect(box.x+105+(i*97)%930,box.y+box.h-22+age*68,25+(i%3)*15,4,2,{fill:typed.del?P.coral:P.gold,alpha:a});}
  const cx=lerp(1820,1588,easeInOut(prog(t,C2+.08,C2+.9))),cy=lerp(790,606,easeInOut(prog(t,C2+.08,C2+.9)));cursor(d,cx,cy,{alpha:(1-send)*easeOut(prog(t,C2+.05,C2+.35)),click:prog(t,C3-.31,C3-.05)});
  // The next world's dark paper starts BEFORE the cut, so there is no palette jump at C3.
  const ink=easeOut(prog(t,C3-.50,C3+.26));if(ink>0){const top=lerp(1140,565,ink);d.save(()=>{d.g.translate(0,top);d.g.rotate(-.012*(1-ink));d.rect(-30,0,1980,650,{fill:P.ink,alpha:.98*ink});d.line(0,56,1920,56,{color:P.cobalt2,width:3,alpha:.20*ink});});}
  // Prompt folds into the exact nine strips inherited by shot 4.
  if(send>0)for(let i=0;i<9;i++){const k=easeOut(prog(send,i*.045,.45+i*.04)),sx=620+i*98,sy=568+(i%3)*18,ex=500+i*138,ey=640+(i%2?55:-55);d.save(()=>{d.g.translate(lerp(sx,ex,k),lerp(sy,ey,k));d.g.rotate(lerp(0,(i-4)*.025,k));d.rrect(-86,-23,172,46,11,{fill:i%3===0?P.gold2:P.white,stroke:P.line,width:1.2,shadow:.18,alpha:k});});}
}

function tower(d,x,baseY,w,h,k,{accent=P.cobalt2,flip=false}={}){const H=h*k,y=baseY-H;d.rrect(x+13,y+17,w,H,7,{fill:'#0c1423',alpha:.25*k});d.rrect(x,y,w,H,7,{fill:'#ece6d9',stroke:'rgba(126,165,245,.24)',width:1.4,alpha:.98*k});const f=26;d.save(()=>{d.g.beginPath();d.g.moveTo(x+w-f,y);d.g.lineTo(x+w,y+f);d.g.lineTo(x+w,y);d.g.closePath();d.g.fillStyle=flip?P.gold2:P.cobalt2;d.g.globalAlpha=.38*k;d.g.fill();});for(let j=0;j<5;j++){const yy=y+42+j*34;if(yy<baseY-18)d.rrect(x+18,yy,w*.56-(j%2)*12,6,3,{fill:P.ink2,alpha:.22*k});}d.line(x+15,y+26,x+w-18,y+26,{color:accent,width:5,alpha:.55*k});}

function shotWorld(d,t,model){const u=prog(t,C3,END),ink=easeOut(prog(t,C3-.50,C3+.26));
  // Continue shot 3's paper flood: warm paper remains visible until the ink sheet actually covers it.
  base(d,t,{dark:.08,blue:.06,warm:.07});const top=lerp(1140,-20,ink);d.save(()=>{d.g.translate(0,top);d.g.rotate(-.012*(1-ink));d.rect(-30,0,1980,1140,{fill:P.ink,alpha:.99*ink});});
  d.glow(1450,250,760,P.gold,.16*ink);d.glow(520,720,760,P.cobalt,.19*ink);
  // Character is one continuous full asset moving from the left crop to the reaching composition.
  const move=easeInOut(prog(t,C3,C3+1.18));const dst={x:lerp(-300,735,move),y:lerp(92,65,move),w:lerp(1020,1080,move),h:lerp(940,995,move)};art(d,model,dst,{crop:'full',alpha:.98,register:7});
  // Nine prompt strips become nine folded page towers.
  d.line(0,654,1920,654,{color:P.gold2,width:3,alpha:.32*ink});
  for(let i=0;i<9;i++){const a=easeOut(prog(t,C3+.05+i*.055,C3+.68+i*.055));const x=lerp(500+i*138,180+i*188,a),h=160+(i%4)*62,w=112+(i%3)*26;tower(d,x,654,w,h,a,{accent:i%3===0?P.gold:P.cobalt2,flip:i%3===0});}
  for(let i=0;i<6;i++){const q=easeOut(prog(t,C3+.30+i*.055,C3+.86+i*.055));d.line(960,654,lerp(960,100+i*355,q),1080,{color:i%2?P.gold:P.cobalt2,width:2.3,alpha:.18*q*ink});}
  // User is a single mark. A paper bridge grows from her gesture towards it.
  const user=easeOut(prog(t,C3+.95,C3+1.42));if(user>0){d.glow(430,824,135,P.gold,.30*user);d.circle(430,824,11,{fill:P.gold,alpha:user});d.circle(430,824,35,{fill:null,stroke:P.gold2,width:2,alpha:.42*user});}
  const bridge=easeOut(prog(t,C3+1.15,C3+2.15));if(bridge>0){for(let i=0;i<7;i++){const q=easeOut(prog(bridge,i*.08,.42+i*.08));const x=lerp(920,455,i/6),y=lerp(760,820,i/6)-Math.sin(i/6*Math.PI)*65;d.save(()=>{d.g.translate(x,y);d.g.rotate(-.10+i*.025);d.rrect(-54*q,-17,108*q,34,5,{fill:i%2?P.white:P.gold2,stroke:P.line,width:1,alpha:.90*q});});}}
  const title=easeOut(prog(t,C3+1.32,C3+2.16));if(title>0){d.text('MAKE IT',112,152,{size:34,font:'mono',weight:700,color:P.cobalt2,alpha:.72*title});d.text('WORTH WATCHING.',110,224,{size:74,font:'serif',weight:700,color:P.white,alpha:.94*title});d.line(114,252,710,252,{color:P.gold,width:6,alpha:.64*title});}
  // Near-lens sheets: moving foreground, never random particles.
  for(let i=0;i<3;i++){const q=prog(t,C3+.48+i*.18,END-.28+i*.06);if(q>0&&q<1)d.save(()=>{d.g.translate(lerp(-380,2100,easeInOut(q)),900-i*175);d.g.rotate(-.15+i*.08);d.rrect(0,0,380,150,12,{fill:P.white,stroke:P.line,width:1.2,alpha:.90,shadow:.35});d.line(34,42,292,42,{color:i===1?P.gold:P.cobalt,width:7,alpha:.55});});}
}

export function renderOpeningV5(d,t,model){if(t<C1)return shotBuild(d,t,model);if(t<C2)return shotContext(d,t,model);if(t<C3)return shotPrompt(d,t,model);return shotWorld(d,t,model);}
export const OPENING_V5_CUTS=[0,C1,C2,C3,END];
