import {Draw} from '../engine/draw.js';
import {renderDraftsV13} from './drafts_v13.js';
import {easeOut,easeInOut,lerp,prog} from '../engine/timing.js';

// A physical, seven-shot opening: code-drawn ink and folded architecture.
// Approved character art appears only as an articulated photographic plate.
const W=1920,H=1080;
const SKY='#111827',NAVY='#172033',BLUE='#3157d5',BLUE2='#7891e8',GOLD='#e8b928',YELLOW='#fff0b4';
const PAPER='#eee4d4',WHITE='#fff9ec',MID='#b6a590',RED='#d94b3d';
const CUTS=[0,1.88,3.68,5.82,8.05,10.35,12.55,15];
const clamp=x=>Math.max(0,Math.min(1,x));
const smooth=x=>{x=clamp(x);return x*x*(3-2*x)};
const local=(t,i)=>prog(t,CUTS[i],CUTS[i+1]);
let handoffCanvas=null,handoffDraw=null;

function polygon(d,pts,fill,shadow=0,alpha=1,stroke=null){
  const g=d.g;d.save(()=>{g.globalAlpha=alpha;
    if(shadow){g.shadowColor='rgba(8,14,26,'+(.36*shadow)+')';g.shadowBlur=38*shadow;g.shadowOffsetY=20*shadow;}
    g.beginPath();g.moveTo(pts[0][0],pts[0][1]);
    for(let i=1;i<pts.length;i++)g.lineTo(pts[i][0],pts[i][1]);g.closePath();
    if(fill){g.fillStyle=fill;g.fill();}
    if(stroke){g.strokeStyle=stroke;g.lineWidth=2;g.stroke();}
  });
}
function path(d,pts,color,width=7,alpha=1){
  const g=d.g;d.save(()=>{g.globalAlpha=alpha;g.strokeStyle=color;g.lineWidth=width;g.lineCap='round';g.lineJoin='round';
    g.beginPath();g.moveTo(pts[0][0],pts[0][1]);for(let i=1;i<pts.length;i++)g.lineTo(pts[i][0],pts[i][1]);g.stroke();
  });
}
function ink(d,text,x,y,size=40,{color=NAVY,alpha=1,rotate=0}={}){
  d.save(()=>{d.g.translate(x,y);d.g.rotate(rotate);d.text(text,0,0,{size,font:'serif',weight:700,color,alpha});});
}
function paper(d,t,{night=false}={}){
  d.rect(0,0,W,H,{fill:night?SKY:PAPER});
  d.gradRect(0,0,W,H,night?
    [[0,'#17243a'],[.50,'#34415b'],[1,'#baa28b']]:
    [[0,'#f8ecdb'],[.52,'#dcd0be'],[1,'#a99b89']],true);
  d.glow(1550,200,820,GOLD,night?.15:.24);d.glow(180,810,670,BLUE,.075);
  for(let i=0;i<300;i++){
    const x=(i*177.3+53)%W,y=(i*109.7+21)%H;
    d.line(x,y,x+(i%5)+2,y-1,{color:i%7?NAVY:BLUE,width:1,alpha:night?.055:.035});
  }
}
function flecks(d,x,y,n,radius,color,alpha){
  for(let i=0;i<n;i++){
    const ang=i*2.399963,rad=radius*Math.sqrt(i/n);
    d.circle(x+Math.cos(ang)*rad,y+Math.sin(ang)*rad,1+(i%4)*.6,{fill:color,alpha:alpha*(.65+.35*Math.sin(i*5)**2)});
  }
}
function ribbon(d,pts,width,progress,colors){
  const reach=clamp(progress)*(pts.length-1);
  for(let i=0;i<pts.length-1;i++){
    const k=clamp(reach-i);if(k<=0)continue;
    const a=pts[i],b=[lerp(a[0],pts[i+1][0],k),lerp(a[1],pts[i+1][1],k)];
    const dx=b[0]-a[0],dy=b[1]-a[1],dist=Math.hypot(dx,dy);if(dist<.1)continue;
    const nx=-dy/dist*width/2,ny=dx/dist*width/2;
    polygon(d,[[a[0]+nx+9,a[1]+ny+16],[b[0]+nx+9,b[1]+ny+16],[b[0]-nx+9,b[1]-ny+16],[a[0]-nx+9,a[1]-ny+16]],NAVY,.12,.22);
    polygon(d,[[a[0]+nx,a[1]+ny],[b[0]+nx,b[1]+ny],[b[0]-nx,b[1]-ny],[a[0]-nx,a[1]-ny]],colors[i%colors.length],.18);
    path(d,[[a[0]+nx*.52,a[1]+ny*.52],[b[0]+nx*.52,b[1]+ny*.52]],WHITE,2,.28);
  }
}
function foreground(d,x,y,angle,scale=1){
  d.save(()=>{d.g.translate(x,y);d.g.rotate(angle);d.g.scale(scale,scale);
    polygon(d,[[-50,-50],[480,-90],[410,300],[-85,310]],'#333f50',.8);
    polygon(d,[[-40,-40],[445,-70],[420,24],[-60,76]],'#778092',.2);
  });
}
function seam(d,a,b,color=NAVY,alpha=.20){
  path(d,[a,b],color,3,alpha);
  for(let i=1;i<14;i++){const u=i/14,x=lerp(a[0],b[0],u),y=lerp(a[1],b[1],u);
    d.line(x-8,y-9,x+6,y+9,{color,width:1,alpha:alpha*.5});}
}
function pencil(d,x,y,angle,alpha=1){
  d.save(()=>{d.g.globalAlpha=alpha;d.g.translate(x,y);d.g.rotate(angle);
    polygon(d,[[-30,-445],[30,-445],[27,190],[-27,190]],'#d4aa45',.55,1,'#8d6c36');
    polygon(d,[[-21,-440],[0,-440],[0,188],[-21,188]],'#ffdc73');
    polygon(d,[[-27,190],[27,190],[0,286]],'#e6c498',0,1,'#927951');
    polygon(d,[[-9,254],[9,254],[0,286]],'#28313d');
    for(let i=0;i<7;i++)d.line(-22,-405+i*43,19,-405+i*43,{color:'#66512c',width:1,alpha:.23});
  });
}
function shotA(d,t){
  const u=local(t,0);paper(d,t,{night:true});
  d.save(()=>{d.g.translate(-70+60*u,-130+30*u);d.g.rotate(-.055);
    polygon(d,[[-120,240],[2110,40],[2230,1250],[-70,1290]],WHITE,1);
    for(let k=0;k<22;k++)path(d,[[-80,400+k*30],[2000,210+k*30]],'#6e655b',1,.055);
    for(let i=0;i<11;i++){
      d.save(()=>{const g=d.g;g.globalAlpha=.09+i*.006;g.strokeStyle=i%2?BLUE:NAVY;g.lineWidth=2+i%3;
        g.beginPath();g.ellipse(1030,665,160+i*20,80+i*14,-.24,.09,Math.PI*1.89);g.stroke();});
    }
    flecks(d,1080,680,115,440,BLUE,.16);
    ribbon(d,[[-240,905],[170,830],[520,770],[830,690],[1030,660]],50,easeOut(prog(u,.07,.86)),[GOLD,'#f0cf62','#b98723']);
    ribbon(d,[[2190,155],[1700,280],[1410,425],[1170,590],[1040,661]],52,easeOut(prog(u,.38,.99)),[BLUE,BLUE2,'#213a9b']);
    d.circle(1035,664,25*easeOut(prog(u,.82,1)),{fill:YELLOW,alpha:.8});
  });
  ink(d,'?',1490,950,240,{alpha:.12,rotate:-.18});
  d.text('NOT A COMMAND.   A QUESTION.',130,168,{size:21,font:'mono',color:WHITE,alpha:.85});
  foreground(d,-35,-50,-.12,.78);
  const wipe=easeInOut(prog(u,.88,1));
  if(wipe>0)polygon(d,[[-80,1020-1200*wipe],[2000,940-1200*wipe],[2000,1500-1200*wipe],[-80,1600-1200*wipe]],'#3a3b4d',.45);
}
function shotB(d,t,plate){
  const u=local(t,1),split=easeInOut(prog(u,.09,.83));paper(d,t,{night:true});
  d.glow(1250,510,920,GOLD,.24);
  plate.silhouette(d.g,{x:810,y:-120,w:1050,h:1120},{color:'#1c367d',alpha:.28});
  plate.draw(d.g,{x:770-50*u,y:-155+75*u,w:1110,h:1200},{alpha:.98});
  polygon(d,[[-100,-70],[950-780*split,-70],[865-900*split,1150],[-100,1150]],'#f9efdf',.9);
  polygon(d,[[990+820*split,-60],[2050,-60],[2050,1160],[1030+930*split,1160]],'#e2d4c4',.9);
  path(d,[[970-745*split,0],[875-820*split,1080]],GOLD,9,.66);
  path(d,[[970+800*split,0],[1060+870*split,1080]],BLUE,9,.58);
  ribbon(d,[[-140,1020],[270,855],[600,755],[1015,790]],45,easeOut(prog(u,.25,.95)),[GOLD,YELLOW,'#bf982b']);
  ink(d,'WE BEGIN',85,190,90,{alpha:.77*(1-u*.42)});
  foreground(d,1885,910,Math.PI+.17,.73);
}
function shotC(d,t,plate){
  const u=local(t,2);paper(d,t);
  d.save(()=>{d.g.translate(-90+80*u,0);
    polygon(d,[[-110,785],[2010,680],[2140,1190],[-110,1190]],'#645c55',.7);
    polygon(d,[[-90,790],[2000,690],[2030,835],[-90,925]],'#c6b8a5',.25);
    polygon(d,[[120,400],[1120,315],[1250,940],[200,1070]],WHITE,.7,1,'rgba(55,46,34,.2)');
    for(let k=0;k<18;k++)d.line(220,550+k*24,1080,475+k*24,{color:k%4?NAVY:BLUE,width:1,alpha:k%4?.06:.11});
    ribbon(d,[[55,980],[380,860],[650,752],[910,642],[1270,570]],45,easeOut(prog(u,.14,.95)),[GOLD,'#f3d568','#ad842a']);
  });
  // Occlusion: she is behind the foreground tabletop, not pasted over it.
  plate.draw(d.g,{x:1120-24*u,y:70+24*Math.sin(u*2),w:780,h:860},{alpha:.98,rot:-.01+.015*u});
  polygon(d,[[1020,843],[2080,760],[2080,1190],[900,1190]],'#817667',.55);
  polygon(d,[[1000,839],[2080,756],[2080,849],[990,920]],'#d9ccb8',.3);
  d.glow(1700,270,690,GOLD,.19);
  ink(d,'A SECOND PAIR',118,183,62,{alpha:.7});
  ink(d,'OF HANDS',122,255,64,{color:BLUE,alpha:.86});
  d.text('01  /  SHARED SURFACE',125,325,{size:21,font:'mono',color:NAVY,alpha:.45});
  foreground(d,-70,950,.15,.60);
}
function shotD(d,t){
  const u=local(t,3);paper(d,t);
  d.save(()=>{d.g.translate(-120*u,35+30*u);d.g.rotate(-.05+.02*u);
    polygon(d,[[-120,70],[2130,-45],[2300,1270],[-170,1270]],WHITE,1);
    for(let k=0;k<35;k++)d.line(60,185+k*25,1950,90+k*25,{color:'#786955',width:1,alpha:.052});
    ink(d,'what if',270,460,155,{alpha:.80,rotate:-.03});
    ribbon(d,[[200,540],[570,505],[920,455],[1430,400]],30,easeOut(prog(u,.12,.63)),[BLUE,BLUE2,BLUE]);
    for(let k=0;k<7;k++){const v=easeOut(prog(u,.19+k*.055,.43+k*.055));
      d.line(490+k*98,610-k*9,535+k*98,634-k*9,{color:GOLD,width:4,alpha:.4*v});}
    const a=easeOut(prog(u,.48,.94));
    ink(d,'we try again',430,818,119,{color:BLUE,alpha:.89*a,rotate:-.035});
    path(d,[[420,850],[1430,760]],GOLD,7,.45*a);
    flecks(d,1230,560,74,365,BLUE,.15);
  });
  pencil(d,1250-225*u,660-135*easeOut(prog(u,.21,.79)),-.31+.19*u);
  foreground(d,1960,915,-.45,.61);
}
function shotE(d,t){
  const u=local(t,4);paper(d,t,{night:true});
  polygon(d,[[-80,185],[2100,-40],[2120,1020],[-100,1180]],'#d5c4b0',.65);
  polygon(d,[[-100,230],[2080,0],[2160,850],[-90,1090]],WHITE,.75);
  for(let k=0;k<6;k++)polygon(d,[[110+k*330,245-k*24],[152+k*330,239-k*24],[114+k*330,990-k*19],[72+k*330,993-k*19]],'#aa9e90',.1,.12);
  ink(d,'NOT YET.',290,460,147,{alpha:.74*(1-prog(u,.45,.83)),rotate:-.07});
  ribbon(d,[[160,560],[520,520],[900,470],[1270,420]],44,easeOut(prog(u,.04,.40)),[RED,'#e17763','#aa3529']);
  for(let i=0;i<8;i++){
    const k=easeOut(prog(u,.20+i*.065,.45+i*.065));
    d.save(()=>{d.g.translate(520+i*148,505-i*20);d.g.rotate(.32*k);
      polygon(d,[[-90,-82],[90,-82],[90,82],[-90,82]],i%2?YELLOW:BLUE,.55,.69*k);});
  }
  const v=easeOut(prog(u,.48,1));
  ribbon(d,[[-160,1010],[280,895],[700,785],[1050,685],[1440,610]],67,v,[GOLD,YELLOW,'#b38726']);
  ribbon(d,[[2150,270],[1770,395],[1440,520],[1100,680]],61,v,[BLUE,BLUE2,'#233d99']);
  ink(d,'AGAIN.',1030,906,210,{alpha:.15+.50*v,rotate:-.10});
  foreground(d,-55,875,.16,.58);
}
function buildings(d,t,k){
  paper(d,t,{night:true});
  polygon(d,[[-80,310],[2030,280],[2040,1170],[-80,1170]],'#c2b4a3',.25);
  d.gradRect(0,292,W,820,[[0,'#9f9283'],[.5,'#c7baaa'],[1,'#746d66']],true);
  for(let i=0;i<11;i++)d.line(1030,283,lerp(-500,2470,i/10),1140,{color:NAVY,width:2,alpha:.075});
  for(let i=1;i<8;i++)d.line(-30,lerp(310,1160,(i/8)**1.7),1950,lerp(310,1160,(i/8)**1.7),{color:NAVY,width:2,alpha:.07});
  const blocks=[[200,945,345,610],[685,870,270,480],[1150,810,300,420],[1580,765,265,510],[1930,715,280,570]];
  for(let i=0;i<blocks.length;i++){
    const [x,y,w,h]=blocks[i],p=easeOut(prog(k,i*.13,.40+i*.13));
    if(!p)continue;const top=y-h*p;
    polygon(d,[[x,y],[x+w,y-10],[x+w,top],[x,top+10]],i%2?'#d6c8b8':WHITE,.36);
    polygon(d,[[x+w,y-10],[x+w+55,y-45],[x+w+55,top-35],[x+w,top]],'#968d83',.18);
    polygon(d,[[x,top+10],[x+w,top],[x+w+55,top-35],[x+55,top-23]],'#fff0d2',.2);
    polygon(d,[[x+w*.36,y-10],[x+w*.36,y-150*p],[x+w*.67,y-150*p],[x+w*.67,y-10]],'#93877b',.1,.55*p);
    d.line(x+30,top+83,x+w-35,top+83,{color:i%2?BLUE:GOLD,width:8,alpha:.46*p});
  }
  polygon(d,[[-180,1100],[-50,1100],[-50,255],[180,30],[520,-60],[650,-60],[470,70],[180,335],[180,1100]],'#353c47',.88);
  polygon(d,[[1640,1110],[2080,1110],[2080,-40],[1860,-40],[1720,240],[1720,1110]],'#50525a',.85);
  d.glow(1060,385,610,GOLD,.10);
}
function shotF(d,t){
  const u=local(t,5),open=easeInOut(prog(u,.19,.85));
  buildings(d,t,open);
  d.save(()=>{d.g.translate(230,-970*open);d.g.rotate(.07+.09*open);
    polygon(d,[[-340,-520],[2250,-520],[2290,1430],[-350,1450]],WHITE,.85,1-open*.95);
    seam(d,[70,320],[1720,595],BLUE,.25*(1-open));
    ink(d,'FOLD',350,660,205,{alpha:.30*(1-open)});
  });
  const k=easeOut(prog(u,.53,.99));
  ribbon(d,[[15,1080],[405,925],[800,820],[1110,711]],68,k,[GOLD,YELLOW,GOLD]);
  ribbon(d,[[2020,970],[1580,825],[1250,740],[1100,710]],64,k,[BLUE,BLUE2,BLUE]);
  d.circle(1100,710,13*k,{fill:YELLOW,alpha:.82});
}
function shotG(d,t,model,poses,plate){
  const u=local(t,6);buildings(d,t,1);
  const k=easeOut(prog(u,.06,.65));
  ribbon(d,[[0,1070],[385,930],[740,820],[1040,723],[1350,610],[1690,490]],73,k,[BLUE,BLUE2,BLUE,'#253e97']);
  ribbon(d,[[1960,1050],[1580,925],[1350,830],[1110,716],[850,620]],65,k,[GOLD,YELLOW,GOLD,'#a78022']);
  d.glow(1070,730,310,GOLD,.19*k);
  const key=easeOut(prog(u,.33,.73));
  d.save(()=>{d.g.translate(1040,730-115*(1-key));d.g.rotate(lerp(-.68,0,key));
    polygon(d,[[-73,-30],[75,-30],[73,30],[-73,30]],WHITE,.56,key,NAVY);
    d.line(-50,-8,55,-8,{color:BLUE,width:5,alpha:.48*key});
  });
  // Render the second act's opening from its actual code for a continuous 15s boundary.
  const fade=smooth(prog(u,.74,1));
  if(fade>0){
    if(!handoffCanvas){handoffCanvas=document.createElement('canvas');handoffCanvas.width=W;handoffCanvas.height=H;
      handoffDraw=new Draw(handoffCanvas.getContext('2d'),W,H);}
    handoffDraw.g.setTransform(1,0,0,1,0,0);handoffDraw.g.clearRect(0,0,W,H);
    renderDraftsV13(handoffDraw,15,model,poses,plate);
    d.save(()=>{d.g.globalAlpha=fade;d.g.drawImage(handoffCanvas,0,0);});
  }
}
export function renderOpeningV12(d,t,model,plate,poses){
  if(t<CUTS[1])return shotA(d,t);
  if(t<CUTS[2])return shotB(d,t,plate);
  if(t<CUTS[3])return shotC(d,t,plate);
  if(t<CUTS[4])return shotD(d,t);
  if(t<CUTS[5])return shotE(d,t);
  if(t<CUTS[6])return shotF(d,t);
  return shotG(d,t,model,poses,plate);
}
export const OPENING_V12_CUTS=CUTS;

