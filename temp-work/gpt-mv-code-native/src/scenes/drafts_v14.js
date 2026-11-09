import {Draw} from '../engine/draw.js';
import {renderDraftsV13} from './drafts_v13.js';
import {renderConstructV6} from './construct_v6.js';
import {easeOut,easeInOut,lerp,prog} from '../engine/timing.js';

// Act II: an error is a physical wrong turn, a repair is shared labor.
// Everything except the approved GPT bust/hand source is code-drawn paper sculpture.
const W=1920,H=1080;
const DARK='#172033',SKY='#111827',BLUE='#3157d5',BLUE2='#7891e8',GOLD='#e8b928',YELLOW='#fff0b4';
const PAPER='#e7dac8',WHITE='#fff9ec',MID='#a99d8d',RED='#d94b3d';
const CUTS=[15,16.85,18.35,20.30,22.05,24.30,26.45,28.38,30];
const clamp=x=>Math.max(0,Math.min(1,x));
const smooth=x=>{x=clamp(x);return x*x*(3-2*x)};
const unit=(t,i)=>prog(t,CUTS[i],CUTS[i+1]);
let buffer=null, bufferDraw=null;
function poly(d,pts,fill,shadow=0,alpha=1,stroke=null){
  const g=d.g;d.save(()=>{g.globalAlpha=alpha;
    if(shadow){g.shadowColor='rgba(8,15,30,'+(.34*shadow)+')';g.shadowBlur=34*shadow;g.shadowOffsetY=22*shadow;}
    g.beginPath();g.moveTo(pts[0][0],pts[0][1]);
    for(let i=1;i<pts.length;i++)g.lineTo(pts[i][0],pts[i][1]);g.closePath();
    if(fill){g.fillStyle=fill;g.fill();}
    if(stroke){g.strokeStyle=stroke;g.lineWidth=2;g.stroke();}
  });
}
function line(d,points,color,width=5,alpha=1){
  d.save(()=>{const g=d.g;g.globalAlpha=alpha;g.strokeStyle=color;g.lineWidth=width;
    g.lineCap='round';g.lineJoin='round';g.beginPath();g.moveTo(points[0][0],points[0][1]);
    for(let i=1;i<points.length;i++)g.lineTo(points[i][0],points[i][1]);g.stroke();});
}
function label(d,text,x,y,size=44,color=DARK,a=1){d.text(text,x,y,{size,font:'serif',weight:700,color,alpha:a});}
function set(d,t,night=false){
  d.rect(0,0,W,H,{fill:night?SKY:PAPER});
  d.gradRect(0,0,W,H,night?
    [[0,'#18273e'],[.52,'#3e485c'],[1,'#938576']]:
    [[0,'#faecda'],[.54,'#dfd0bb'],[1,'#a7998a']],true);
  d.glow(1510,245,820,GOLD,night?.17:.19);d.glow(250,780,720,BLUE,.09);
  for(let i=0;i<250;i++){
    const x=(i*153.7+31)%W,y=(i*97.5+62)%H;
    d.line(x,y,x+3+(i%4),y-1,{color:i%6?DARK:BLUE,width:.9,alpha:night?.05:.035});
  }
}
function strip(d,points,width,progress,colors){
  const n=points.length-1,travel=clamp(progress)*n;
  for(let i=0;i<n;i++){
    const u=clamp(travel-i);if(u<=0)continue;
    const p=points[i],q=[lerp(p[0],points[i+1][0],u),lerp(p[1],points[i+1][1],u)];
    const dx=q[0]-p[0],dy=q[1]-p[1],r=Math.hypot(dx,dy);if(r<.1)continue;
    const nx=-dy/r*width/2,ny=dx/r*width/2;
    poly(d,[[p[0]+nx+12,p[1]+ny+18],[q[0]+nx+12,q[1]+ny+18],[q[0]-nx+12,q[1]-ny+18],[p[0]-nx+12,p[1]-ny+18]],DARK,.12,.19);
    poly(d,[[p[0]+nx,p[1]+ny],[q[0]+nx,q[1]+ny],[q[0]-nx,q[1]-ny],[p[0]-nx,p[1]-ny]],colors[i%colors.length],.2);
    line(d,[[p[0]+nx*.54,p[1]+ny*.54],[q[0]+nx*.54,q[1]+ny*.54]],WHITE,2,.24);
  }
}
function page(d,x,y,w,h,rot,face=WHITE){
  d.save(()=>{d.g.translate(x,y);d.g.rotate(rot);
    poly(d,[[-w/2,-h/2],[w/2,-h/2],[w/2,h/2],[-w/2,h/2]],face,.85,1,'rgba(35,42,53,.22)');
    poly(d,[[w/2,-h/2],[w/2+22,-h/2+17],[w/2+22,h/2+17],[w/2,h/2]],'#a99d8e',.2);
  });
}
function pencil(d,x,y,rotation){
  d.save(()=>{d.g.translate(x,y);d.g.rotate(rotation);
    poly(d,[[-25,-490],[25,-490],[22,150],[-22,150]],'#e3b945',.48);
    poly(d,[[-16,-485],[0,-485],[0,145],[-16,145]],'#ffe388');
    poly(d,[[-22,150],[22,150],[0,240]],'#edcba0');
    poly(d,[[-8,207],[8,207],[0,244]],'#333643');
  });
}
function stitch(d,x,y,rot,progress){
  d.save(()=>{d.g.translate(x,y);d.g.rotate(rot);
    line(d,[[-450,-3],[470,2]],DARK,5,.21);
    for(let i=0;i<16;i++){
      const u=i/16,appear=easeOut(prog(progress,u*.67,u*.67+.28));
      if(!appear)continue;
      const px=-410+i*54;
      line(d,[[px,-28],[px+29,27]],i%3?BLUE:GOLD,6,.45*appear);
      d.circle(px+14,0,2.5,{fill:DARK,alpha:.22*appear});
    }
  });
}
function lens(d,x,y,r,fn){
  d.save(()=>{const g=d.g;g.beginPath();g.ellipse(x,y,r,r*.78,-.09,0,Math.PI*2);g.clip();fn();});
}
function redRoute(d,u){
  // A wrong choice splits the blue route and physically tears the street surface.
  strip(d,[[735,822],[900,800],[1100,827],[1350,900],[1690,1060]],55,easeOut(prog(u,.1,.83)),[RED,'#e17863','#ad4235']);
  for(let i=0;i<9;i++){
    const k=easeOut(prog(u,.24+i*.05,.51+i*.05));
    d.save(()=>{d.g.translate(1030+i*86,860+i*22);d.g.rotate(.11*i+.22*k);
      poly(d,[[-50,-50],[50,-50],[50,50],[-50,50]],i%2?'#c9aa9a':'#f5dfcd',.22,.55*k);
    });
  }
}
function baseOld(d,model,poses,plate){renderDraftsV13(d,15,model,poses,plate);}
function shotWrong(d,t,model,poses,plate){
  const u=unit(t,0);baseOld(d,model,poses,plate);
  redRoute(d,u);
  d.save(()=>{d.g.translate(1510,870);d.g.rotate(-.1-.15*u);
    poly(d,[[-235,-15],[280,-30],[292,138],[-225,153]],'#c7b6a3',.55,.20+.30*u);
  });
  d.glow(1300,900,230,RED,.07+.12*u);
  label(d,'THE WRONG TURN.',114,178,47,WHITE,.5*easeOut(prog(u,.4,.85)));
  poly(d,[[-120,860],[360,805],[500,1180],[-120,1180]],'#514c4c',.48,.5*u);
}
function shotFall(d,t,model,poses,plate){
  const u=unit(t,1);baseOld(d,model,poses,plate);
  // Camera overtakes the snapped road; the paper scraps now fill the foreground.
  d.save(()=>{d.g.translate(270*u,165*u);d.g.scale(1+.20*u,1+.20*u);
    redRoute(d,1);
    for(let i=0;i<8;i++){
      const k=easeOut(prog(u,i*.06,.3+i*.06)),xx=940+i*110,yy=670+i*38;
      d.save(()=>{d.g.translate(xx+160*k,yy+210*k);d.g.rotate(.22*i+.50*k);
        poly(d,[[-65,-90],[65,-90],[55,75],[-55,75]],i%2?'#c8bab0':'#eedfcb',.5,.78*k);
      });
    }
  });
  const wipe=easeInOut(prog(u,.78,1));
  if(wipe)poly(d,[[-100,1180-1520*wipe],[2100,1120-1520*wipe],[2180,1530-1520*wipe],[-100,1600-1520*wipe]],WHITE,.6);
}
function shotRed(d,t){
  const u=unit(t,2);set(d,t);
  d.save(()=>{d.g.translate(-50+55*u,30);d.g.rotate(-.06);
    page(d,940,570,2250,1010,0);
    for(let i=0;i<35;i++)d.line(30,140+i*31,1960,125+i*31,{color:'#7f7263',width:1,alpha:.045});
    label(d,'THIS IS NOT IT.',180,435,170,DARK,.77);
    strip(d,[[40,550],[550,515],[1010,462],[1510,410]],51,easeOut(prog(u,.08,.61)),[RED,'#f07966','#b04435']);
    const reject=easeOut(prog(u,.29,.88));
    for(let i=0;i<12;i++){
      const k=easeOut(prog(reject,i*.035,.22+i*.035));
      d.line(240+i*112,610-i*10,295+i*112,680-i*10,{color:RED,width:5,alpha:.62*k});
    }
    label(d,'TRY AGAIN.',530,850,127,BLUE,easeOut(prog(u,.58,.99)));
  });
  pencil(d,1420-260*u,675-150*easeOut(prog(u,.24,.8)),-.32+.21*u);
  poly(d,[[-110,-20],[350,-75],[350,95],[-110,165]],'#344255',.6,.65);
}
function shotNotice(d,t,plate){
  const u=unit(t,3);set(d,t,true);
  // A bold performance close-up within the world, not a circular portrait badge.
  d.glow(1240,350,900,GOLD,.22);
  poly(d,[[-130,-70],[490,-110],[540,1200],[-150,1220]],'#2b374d',.84);
  poly(d,[[355,-40],[805,-100],[570,1190],[220,1190]],'#6d7788',.35,.48);
  plate.silhouette(d.g,{x:850-65*u,y:-120,w:1100,h:1220},{color:'#1b347d',alpha:.15});
  plate.draw(d.g,{x:820-105*u,y:-135+55*u,w:1120,h:1230},{alpha:.98,rot:-.012+.018*u});
  // A broad, tilted physical page occludes the bust below her shoulder line.
  poly(d,[[-80,900],[2260,685],[2260,1250],[-140,1250]],'#8c8176',.8);
  poly(d,[[-85,888],[2260,681],[2260,781],[-100,995]],'#dbcdb9',.3);
  strip(d,[[-190,1020],[270,940],[620,855],[1030,775]],53,easeOut(prog(u,.12,.90)),
    [GOLD,YELLOW,'#b8912c']);
  // The correction note sits on the real paper surface, not inside a UI box.
  label(d,'I MISREAD',120,250,81,WHITE,.90);
  label(d,'THE FOLD.',126,343,81,WHITE,.90);
  line(d,[[126,372],[640,351]],GOLD,4,.37);
  poly(d,[[1640,-70],[2050,-70],[2020,320],[1810,290]],'#222e41',.57,.57);
}
function shotRepair(d,t){
  const u=unit(t,4);set(d,t);
  page(d,960,540,2230,1020,-.028);
  const crack=[[60,800],[370,720],[750,755],[1020,670],[1420,700],[1860,590]];
  line(d,crack,'#787063',11,.22);
  for(let i=0;i<crack.length-1;i++){
    const a=crack[i],b=crack[i+1];line(d,[[a[0],a[1]+12],[b[0],b[1]+12]],RED,11,.27*(1-prog(u,.38,.9)));
  }
  stitch(d,970,720,-.12,easeOut(prog(u,.12,.86)));
  strip(d,[[-130,1000],[350,900],[725,820],[1100,710],[1530,605]],50,easeOut(prog(u,.25,.94)),[BLUE,BLUE2,BLUE]);
  strip(d,[[2100,325],[1730,460],[1490,550],[1160,700]],40,easeOut(prog(u,.42,.98)),[GOLD,YELLOW,GOLD]);
  d.glow(1130,700,280,GOLD,.19*u);
  label(d,'REPAIR THE EDGE.',120,245,93,DARK,.74);
  // A transparent tracing-paper overlay sweeps off the camera, revealing the repaired seam.
  const peel=easeOut(prog(u,.66,1));
  poly(d,[[1180+900*peel,180-200*peel],[2080+1100*peel,100-300*peel],
    [2120+1400*peel,900-250*peel],[1270+940*peel,990-140*peel]],'#f1e4d1',.55,.55*(1-peel));
}
function shotAlign(d,t){
  const u=unit(t,5);set(d,t,true);
  const q=easeOut(prog(u,.10,.82));
  // Oversized material planes fill the lens: two draft layers overlap as they register.
  d.save(()=>{d.g.translate(360+210*q,500+90*q);d.g.rotate(-.31+.18*q);
    poly(d,[[-980,-660],[530,-660],[530,850],[-980,850]],'#c7b9a7',.9);
    for(let j=0;j<24;j++)d.line(-800,-540+j*62,380,-540+j*62,
      {color:DARK,width:1.3,alpha:.065});
    line(d,[[-760,-250],[350,-250]],RED,20,.27*(1-q));
    line(d,[[-650,330],[310,330]],GOLD,13,.35);
  });
  d.save(()=>{d.g.translate(1460-350*q,510+80*q);d.g.rotate(.31-.26*q);
    poly(d,[[-490,-740],[1010,-740],[1010,880],[-490,880]],WHITE,.88);
    poly(d,[[880,-740],[1020,-740],[1020,880],[880,880]],'#b4a897',.2,.86);
    for(let j=0;j<19;j++)d.line(-370,-520+j*69,820,-520+j*69,
      {color:DARK,width:1,alpha:.058});
    line(d,[[-360,-260],[810,-260]],BLUE,17,.42);
    for(let j=0;j<7;j++){
      const x=-285+j*160,y=90+(j%3)*34;
      d.circle(x,y,14,{fill:j%2?GOLD:BLUE,alpha:.14+.2*q});
    }
  });
  // Tracing paper briefly crosses the near lens to make alignment a 3D action.
  const near=easeOut(prog(u,.24,.92));
  d.save(()=>{d.g.translate(-250+820*near,1000-120*near);d.g.rotate(-.18);
    poly(d,[[-500,-110],[1530,-110],[1530,110],[-500,110]],'#f3e9d7',.54,.62);
    line(d,[[-330,-12],[1250,-12]],BLUE,9,.24);
  });
  strip(d,[[-120,990],[310,860],[720,755],[1100,675],[1660,505]],52,near,
    [GOLD,YELLOW,BLUE2,BLUE]);
  label(d,'ALIGNED.',110,158,92,WHITE,.8*near);
  poly(d,[[-110,1040],[620,915],[685,1210],[-120,1210]],'#343d4b',.6,.83);
}
function shotGive(d,t){
  const u=unit(t,6);set(d,t,true);
  // A proof physically unfolds between both contributors, not a floating document card.
  poly(d,[[-150,900],[845,730],[1050,1260],[-170,1260]],'#958674',.67);
  poly(d,[[900,770],[2100,640],[2150,1260],[890,1260]],'#a79a86',.68);
  const k=easeOut(prog(u,.08,.87));
  strip(d,[[2160,1040],[1750,930],[1400,830],[1110,710],[870,640]],87,k,
    [BLUE,BLUE2,BLUE,'#253e95']);
  strip(d,[[-180,1100],[270,950],[635,825],[940,705],[1180,625]],82,k,
    [GOLD,YELLOW,GOLD,'#bb922b']);
  const open=easeOut(prog(u,.29,.88));
  d.save(()=>{d.g.translate(1030,690-115*(1-open));d.g.rotate(-.65+.53*open);
    poly(d,[[-230,-20],[0,-158],[245,-18],[0,130]],WHITE,.9,open);
    poly(d,[[-230,-20],[0,-158],[0,130]],'#ece0ce',.26,.91*open);
    poly(d,[[0,-158],[245,-18],[0,130]],'#d9c9b3',.26,.90*open);
    line(d,[[-175,-24],[169,-24]],BLUE,11,.46*open);
    line(d,[[-110,22],[114,22]],GOLD,8,.44*open);
  });
  d.glow(1010,700,570,GOLD,.08+.12*open);
  label(d,'TAKE THIS.',95,200,104,WHITE,.86);
  poly(d,[[-150,990],[260,915],[400,1280],[-180,1280]],'#404450',.35,.71);
}
function shotRebuild(d,t,model,poses,plate){
  const u=unit(t,7);set(d,t,true);
  poly(d,[[-50,310],[2050,270],[2050,1170],[-80,1170]],'#c6b7a2',.3);
  d.gradRect(0,290,W,810,[[0,'#a49685'],[.52,'#d2c1ae'],[1,'#938478']],true);
  for(let i=0;i<9;i++)d.line(1010,290,lerp(-500,2470,i/8),1140,{color:DARK,width:2,alpha:.074});
  // The corrected line travels out into a large stage, becoming structural material.
  strip(d,[[-120,990],[400,895],[760,790],[1080,710],[1420,575],[1840,430]],85,
    easeOut(prog(u,.07,.77)),[BLUE,BLUE2,'#304ba8']);
  strip(d,[[2090,1010],[1740,880],[1460,800],[1160,705],[890,590]],78,
    easeOut(prog(u,.13,.84)),[GOLD,YELLOW,'#b98e22']);
  for(let i=0;i<6;i++){
    const a=easeOut(prog(u,.10+i*.09,.42+i*.09));
    const x=130+i*290,y=890-i*65,h=(240+(i%3)*85)*a;
    poly(d,[[x,y],[x+180,y-4],[x+180,y-h],[x,y-h+7]],i%2?WHITE:'#eadcca',.33);
    poly(d,[[x+180,y-4],[x+212,y-25],[x+212,y-h-21],[x+180,y-h]],'#8b8279',.10);
    d.line(x+20,y-h+36,x+142,y-h+36,{color:i%2?BLUE:GOLD,width:7,alpha:.33*a});
  }
  const wipe=smooth(prog(u,.73,1));
  if(wipe){
    if(!buffer){buffer=document.createElement('canvas');buffer.width=W;buffer.height=H;
      bufferDraw=new Draw(buffer.getContext('2d'),W,H);}
    bufferDraw.g.setTransform(1,0,0,1,0,0);bufferDraw.g.clearRect(0,0,W,H);
    renderConstructV6(bufferDraw,30,model,poses);
    const x=lerp(-360,2280,wipe);
    d.save(()=>{const g=d.g;g.beginPath();g.moveTo(-100,-50);g.lineTo(x-220,-50);
      g.lineTo(x+270,1140);g.lineTo(-100,1140);g.closePath();g.clip();g.drawImage(buffer,0,0);});
    d.save(()=>{d.g.translate(x,540);d.g.rotate(-.35);
      poly(d,[[-43,-850],[36,-850],[36,850],[-43,850]],YELLOW,.24,.66);
      line(d,[[12,-850],[12,850]],BLUE,6,.38);
    });
  }
}
export function renderDraftsV14(d,t,model,poses,plate){
  if(t<CUTS[1])return shotWrong(d,t,model,poses,plate);
  if(t<CUTS[2])return shotFall(d,t,model,poses,plate);
  if(t<CUTS[3])return shotRed(d,t);
  if(t<CUTS[4])return shotNotice(d,t,plate);
  if(t<CUTS[5])return shotRepair(d,t);
  if(t<CUTS[6])return shotAlign(d,t);
  if(t<CUTS[7])return shotGive(d,t);
  return shotRebuild(d,t,model,poses,plate);
}
export const DRAFTS_V14_CUTS=CUTS;

