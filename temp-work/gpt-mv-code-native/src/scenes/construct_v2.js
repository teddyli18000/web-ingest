import {PALETTE as P} from '../engine/palette.js';
import {easeInOut,easeOut,lerp,prog,smooth} from '../engine/timing.js';
import {renderDraftsV10} from './drafts_v10.js';

const T0=30,T1=33.20,T2=36.35,T3=40.55,END=45;
const INK='#172033',INK2='#263249',PAPER='#f5efe3',PAPER2='#ddd4c4',BLUE='#3157d5',BLUE2='#7891e8',GOLD='#e8b928',GOLD2='#f4d96f';

function poly(d,pts,{fill=PAPER,stroke=null,width=1,alpha=1,shadow=0}={}){
  const g=d.g;d.save(()=>{g.globalAlpha=alpha;if(shadow){g.shadowColor=`rgba(0,0,0,${.22*shadow})`;g.shadowBlur=34*shadow;g.shadowOffsetY=18*shadow;}g.beginPath();g.moveTo(pts[0][0],pts[0][1]);for(let i=1;i<pts.length;i++)g.lineTo(pts[i][0],pts[i][1]);g.closePath();if(fill){g.fillStyle=fill;g.fill();}if(stroke){g.strokeStyle=stroke;g.lineWidth=width;g.stroke();}});
}
function curve(d,pts,{color=BLUE,width=6,alpha=1}={}){
  const g=d.g;d.save(()=>{g.globalAlpha=alpha;g.strokeStyle=color;g.lineWidth=width;g.lineCap='round';g.lineJoin='round';g.beginPath();g.moveTo(pts[0][0],pts[0][1]);for(let i=1;i<pts.length;i++){const p=pts[i-1],n=pts[i],cx=(p[0]+n[0])/2,cy=(p[1]+n[1])/2;g.quadraticCurveTo(p[0],p[1],cx,cy);}const z=pts[pts.length-1];g.lineTo(z[0],z[1]);g.stroke();});
}
function art(d,model,dst,{crop='full',alpha=1,register=0,cover=false,rot=0}={}){if(register)model.register(d.g,dst,{crop,spread:register,alpha,rot});else model.draw(d.g,dst,{crop,alpha,cover,rot});}
function glowStage(d,t){
  d.rect(0,0,1920,1080,{fill:INK});
  d.glow(1540,260,730,GOLD,.13);d.glow(360,800,800,BLUE,.17);
  d.gradRect(0,0,1920,1080,[[0,'rgba(4,9,18,.26)'],[.52,'rgba(23,32,51,0)'],[1,'rgba(4,9,18,.24)']],false);
  d.save(()=>{d.g.globalAlpha=.045;d.g.fillStyle='#f3efe4';for(let i=0;i<230;i++){const x=(i*139.7+t*6)%1920,y=(i*83.1+t*4)%1080;d.g.fillRect(x,y,1+(i%4===0),1);}});
}
function mark(d,x,y,color,a=1,r=10){d.glow(x,y,125,color,.20*a);d.circle(x,y,r,{fill:color,alpha:a});d.circle(x,y,r*3.1,{fill:null,stroke:color,width:2,alpha:.34*a});}

const MAP=[[330,826],[535,724],[760,768],[995,622],[1230,656],[1510,490]];
const HUMAN=[[340,545],[575,592],[805,518],[1050,548],[1300,452]];
function mapPlane(d,{alpha=1,grid=.55,labels=.5}={}){
  const q=[[210,265],[1640,205],[1810,875],[315,995]];
  poly(d,[[q[0][0]+28,q[0][1]+38],[q[1][0]+34,q[1][1]+34],[q[2][0]+38,q[2][1]+38],[q[3][0]+28,q[3][1]+42]],{fill:'#070b13',alpha:.26*alpha,shadow:.2});
  poly(d,q,{fill:PAPER,stroke:'rgba(120,145,184,.25)',width:2,alpha,shadow:.62});
  if(grid>0){
    for(let i=1;i<8;i++){const u=i/8,a=[lerp(q[0][0],q[3][0],u),lerp(q[0][1],q[3][1],u)],b=[lerp(q[1][0],q[2][0],u),lerp(q[1][1],q[2][1],u)];d.line(a[0],a[1],b[0],b[1],{color:INK2,width:1.2,alpha:.11*grid*alpha});}
    for(let i=1;i<10;i++){const u=i/10,a=[lerp(q[0][0],q[1][0],u),lerp(q[0][1],q[1][1],u)],b=[lerp(q[3][0],q[2][0],u),lerp(q[3][1],q[2][1],u)];d.line(a[0],a[1],b[0],b[1],{color:BLUE,width:1,alpha:.075*grid*alpha});}
  }
  curve(d,MAP,{color:BLUE,width:8,alpha:.66*alpha});curve(d,HUMAN,{color:GOLD,width:7,alpha:.54*alpha});
  for(const p of MAP)d.circle(p[0],p[1],7,{fill:BLUE,alpha:.72*alpha});for(const p of HUMAN)d.circle(p[0],p[1],6,{fill:GOLD,alpha:.66*alpha});
  if(labels){d.text('SHARED MAP / 01',292,335,{size:20,font:'mono',weight:700,color:INK2,alpha:.46*labels*alpha});d.text('build on the correction',290,378,{size:34,font:'serif',italic:true,color:INK,alpha:.61*labels*alpha});}
  return q;
}
function proofRibbon(d,a,b,k,{count=9,goldEvery=3}={}){
  if(k<=0)return;for(let i=0;i<count;i++){const u=i/(count-1),q=easeOut(prog(k,i*.055,.40+i*.055));if(q<=0)continue;const x=lerp(a[0],b[0],u),y=lerp(a[1],b[1],u)-Math.sin(u*Math.PI)*90,w=lerp(145,74,u),h=lerp(42,26,u);d.save(()=>{d.g.translate(x,y);d.g.rotate(lerp(-.16,.08,u));d.rrect(-w*q/2,-h/2,w*q,h,5,{fill:i%goldEvery===0?GOLD2:'#fffdfa',stroke:'rgba(53,65,92,.20)',width:1,alpha:.97*q,shadow:.18});});}
}
function stagePaperWipe(d,t){
  const q=prog(t,T0+.34,T0+1.35);if(q<=0||q>=1)return;const k=easeInOut(q),x=lerp(-2050,2080,k),w=1940,h=1320;
  d.save(()=>{d.g.translate(x+w/2,530);d.g.rotate(-.055);d.g.translate(-w/2,-660);poly(d,[[0,0],[w,0],[w,h],[0,h]],{fill:INK,alpha:1,shadow:.38});d.line(120,120,w-160,120,{color:BLUE2,width:8,alpha:.22});d.text('SHARED / WORKTABLE',128,208,{size:26,font:'mono',weight:700,color:'#e9edf7',alpha:.30});});
}
function shotPull(d,t,model,poses){
  renderDraftsV10(d,29.999,model,poses);
  const line=easeOut(prog(t,T0+.04,T0+.88));curve(d,[[750,690],[570,715],[420,760],[290,795]],{color:BLUE,width:7,alpha:.48*line});
  const sheet=easeInOut(prog(t,T0+.55,T0+2.05));if(sheet>0){d.save(()=>{const g=d.g;g.translate(960,600);g.scale(lerp(.08,1,sheet),lerp(.05,1,sheet));g.rotate(lerp(-.22,-.018,sheet));g.translate(-960,-600);mapPlane(d,{alpha:sheet,grid:sheet,labels:.5*sheet});});}
  stagePaperWipe(d,t);
  if(t>T0+1.25){glowStage(d,t);const settle=easeInOut(prog(t,T0+1.15,T1-.18));d.save(()=>{d.g.translate(0,lerp(260,0,settle));mapPlane(d,{alpha:settle,grid:settle,labels:settle});});proofRibbon(d,[300,810],[1480,500],settle,{count:10});}
  const cap=easeOut(prog(t,T0+.72,T0+1.45))*(1-smooth(prog(t,T1-.72,T1-.16)));d.text('follow the correction.',112,140,{size:45,font:'serif',italic:true,color:'#f5efe3',alpha:.72*cap});d.text('THE LINE LEAVES THE ANSWER',114,185,{size:18,font:'mono',weight:700,color:BLUE2,alpha:.54*cap});
}
function foldWall(d,x,y,w,h,k,{gold=false,lean=0}={}){
  if(k<=0)return;const H=h*k,c=gold?GOLD:BLUE,front=gold?'#eadb9d':'#dfe6f5',side=gold?'#cdbb77':'#b9c6df',top=gold?'#f4e7b7':'#eef3ff';
  // front, side and top faces share vertices so the object reads as folded paper volume.
  poly(d,[[x,y],[x+w,y],[x+w+lean,y-H],[x+lean,y-H]],{fill:front,stroke:'rgba(54,68,95,.22)',width:1.3,alpha:.99,shadow:.28});
  poly(d,[[x+w,y],[x+w+22,y+16],[x+w+lean+22,y-H+16],[x+w+lean,y-H]],{fill:side,stroke:'rgba(54,68,95,.15)',width:1,alpha:.95});
  poly(d,[[x+lean,y-H],[x+w+lean,y-H],[x+w+lean+22,y-H+16],[x+lean+20,y-H+16]],{fill:top,stroke:'rgba(54,68,95,.14)',width:1,alpha:.98});
  d.line(x+lean+20,y-H+30,x+lean+w-18,y-H+30,{color:c,width:6,alpha:.50});for(let i=0;i<3;i++)d.line(x+lean+24,y-H+63+i*28,x+lean+w*(.62-i*.07),y-H+63+i*28,{color:INK2,width:5,alpha:.16});
}
function foldArch(d,x,y,w,h,k,{gold=false}={}){
  if(k<=0)return;const g=d.g,H=h*k,c=gold?GOLD:BLUE;d.save(()=>{g.translate(x,y);g.globalAlpha=.98;g.fillStyle=gold?'#eadb9d':'#dfe6f5';g.strokeStyle='rgba(54,68,95,.22)';g.lineWidth=1.5;g.beginPath();g.moveTo(-w/2,0);g.lineTo(-w/2,-H*.65);g.quadraticCurveTo(0,-H*1.12,w/2,-H*.65);g.lineTo(w/2,0);g.lineTo(w*.22,0);g.lineTo(w*.22,-H*.48);g.quadraticCurveTo(0,-H*.78,-w*.22,-H*.48);g.lineTo(-w*.22,0);g.closePath();g.fill();g.stroke();g.strokeStyle=c;g.lineWidth=6;g.globalAlpha=.45;g.beginPath();g.moveTo(-w*.34,-H*.62);g.quadraticCurveTo(0,-H*.94,w*.34,-H*.62);g.stroke();});
}
function nearRuler(d,t,a,b){const q=prog(t,a,b);if(q<=0||q>=1)return;d.save(()=>{d.g.translate(lerp(-780,2100,easeInOut(q)),925);d.g.rotate(-.12);d.rrect(0,0,950,135,10,{fill:'#fffdfa',stroke:'rgba(53,65,92,.22)',width:1.3,alpha:.98,shadow:.48});for(let i=0;i<18;i++)d.line(50+i*48,20,50+i*48,20+(i%5===0?48:27),{color:INK2,width:2,alpha:.30});d.line(42,98,860,98,{color:BLUE,width:5,alpha:.22});});}
function shotPlan(d,t){
  glowStage(d,t);mapPlane(d,{alpha:1,grid:.85,labels:.75});
  const human=easeOut(prog(t,T1+.20,T1+.92)),gpt=easeOut(prog(t,T1+.48,T1+1.18));mark(d,340,545,GOLD,human);mark(d,1510,490,BLUE,gpt);
  const join=easeOut(prog(t,T1+.82,T2-.30));proofRibbon(d,[390,560],[1460,500],join,{count:11,goldEvery:2});
  // Folded edge tabs make the sheet read as an object sitting on a desk.
  const fold=easeInOut(prog(t,T1+.12,T1+1.02));poly(d,[[210,265],[315,995],[lerp(315,170,fold),lerp(995,895,fold)],[lerp(210,92,fold),lerp(265,350,fold)]],{fill:'#d9dfeb',stroke:'rgba(120,145,184,.20)',alpha:.96,shadow:.20});poly(d,[[1640,205],[1810,875],[lerp(1810,1950,fold),lerp(875,770,fold)],[lerp(1640,1840,fold),lerp(205,300,fold)]],{fill:'#eadc9f',stroke:'rgba(120,145,184,.18)',alpha:.96,shadow:.20});
  const cap=easeOut(prog(t,T1+.74,T1+1.38));d.text('two marks / one surface',113,145,{size:24,font:'mono',weight:700,color:BLUE2,alpha:.46*cap});d.text('agree on where to build.',110,198,{size:43,font:'serif',italic:true,color:'#f5efe3',alpha:.70*cap});
  nearRuler(d,t,T2-.62,T2+.35);
}
function bridgeDeck(d,k){
  if(k<=0)return;const a=[520,746],b=[1480,492],N=14;for(let i=0;i<N;i++){const u=i/(N-1),q=easeOut(prog(k,i*.045,.44+i*.045));if(q<=0)continue;const x=lerp(a[0],b[0],u),y=lerp(a[1],b[1],u)-Math.sin(u*Math.PI)*130,sc=lerp(1.18,.72,u);d.save(()=>{d.g.translate(x,y);d.g.rotate(-.25+u*.37);d.rrect(-63*sc*q,-20*sc,126*sc*q,40*sc,5,{fill:i%2?PAPER:GOLD2,stroke:'rgba(53,65,92,.21)',width:1,alpha:.98*q,shadow:.24});});}
  curve(d,[[520,746],[740,570],[1010,520],[1260,454],[1480,492]],{color:BLUE,width:5,alpha:.31*k});
}
function shotBuild(d,t){
  glowStage(d,t);mapPlane(d,{alpha:1,grid:.42,labels:.20});
  const items=[['wall',400,790,170,230,false,-25],['arch',675,692,210,270,true,0],['wall',920,705,165,250,false,-9],['arch',1195,590,235,335,false,0],['wall',1450,540,155,255,true,-15]];
  items.forEach((v,i)=>{const k=easeOut(prog(t,T2+.12+i*.17,T2+.95+i*.17));if(v[0]==='arch')foldArch(d,v[1],v[2],v[3],v[4],k,{gold:v[5]});else foldWall(d,v[1],v[2],v[3],v[4],k,{gold:v[5],lean:v[6]});});
  const deck=easeOut(prog(t,T2+.78,T3-.35));bridgeDeck(d,deck);mark(d,385,775,GOLD,easeOut(prog(t,T2+.45,T2+1.0)));mark(d,1515,490,BLUE,easeOut(prog(t,T2+.65,T2+1.18)));
  const cap=easeOut(prog(t,T2+.78,T2+1.48));d.text('THE CORRECTION BECOMES STRUCTURE',100,140,{size:20,font:'mono',weight:700,color:BLUE2,alpha:.48*cap});d.text('build the next move.',98,196,{size:47,font:'serif',italic:true,color:'#f5efe3',alpha:.74*cap});
  nearRuler(d,t,T3-.66,T3+.32);
}
function handWork(d,t,model){
  const settle=easeOut(prog(t,T3+.12,T3+.78));art(d,model,{x:lerp(1110,1240,settle),y:lerp(-140,-40,settle),w:lerp(1120,980,settle),h:lerp(980,900,settle)},{crop:'hand',alpha:1,register:lerp(6,3,settle),cover:true});
}
function shotJoin(d,t,model){
  glowStage(d,t);mapPlane(d,{alpha:1,grid:.25,labels:0});
  // Completed folded environment remains as midground.
  foldWall(d,400,790,170,230,1,{lean:-25});foldArch(d,675,692,210,270,1,{gold:true});foldWall(d,920,705,165,250,1,{lean:-9});foldArch(d,1195,590,235,335,1);foldWall(d,1450,540,155,255,1,{gold:true,lean:-15});bridgeDeck(d,1);
  handWork(d,t,model);
  const human=easeOut(prog(t,T3+.26,T3+.85));mark(d,350,792,GOLD,human);
  const final=easeOut(prog(t,T3+.55,T3+1.70));proofRibbon(d,[410,770],[1345,510],final,{count:10,goldEvery:2});
  const blue=easeOut(prog(t,T3+.62,T3+1.52));curve(d,[[1330,505],[1120,540],[870,610],[620,705],[390,782]],{color:BLUE,width:7,alpha:.40*blue});
  const cap=easeOut(prog(t,T3+.95,T3+1.70));d.text('SHARED CONSTRUCTION / 01',95,972,{size:20,font:'mono',weight:700,color:'#f3efe4',alpha:.38*cap});
  // A finished proof rises into the lens to motivate the next gate.
  const out=easeInOut(prog(t,END-.82,END));if(out>0){const y=lerp(1180,180,out);poly(d,[[-100,y],[2020,y-140],[2020,y+1040],[-100,y+1110]],{fill:'#fffdf8',stroke:'rgba(53,65,92,.18)',width:2,alpha:.997,shadow:.65});d.line(115,y+112,1640,y+15,{color:BLUE,width:8,alpha:.34});d.text('NEXT PROOF',128,y+198,{size:25,font:'mono',weight:700,color:INK2,alpha:.32});d.text('we built this together.',126,y+272,{size:48,font:'serif',italic:true,color:INK,alpha:.34});}
}

export function renderConstructV2(d,t,model,poses){
  if(t<T1)return shotPull(d,t,model,poses);
  if(t<T2)return shotPlan(d,t);
  if(t<T3)return shotBuild(d,t);
  return shotJoin(d,t,model);
}
export const CONSTRUCT_V2_CUTS=[T0,T1,T2,T3,END];
