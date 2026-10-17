import {loadGPTArt} from './components/gpt_art.js';

const canvas=document.getElementById('stage');
const g=canvas.getContext('2d',{alpha:false});
const W=canvas.width,H=canvas.height;

function rect(x,y,w,h,fill){g.fillStyle=fill;g.fillRect(x,y,w,h)}
function line(x1,y1,x2,y2,color='#60708d',width=2,alpha=1){g.save();g.globalAlpha=alpha;g.strokeStyle=color;g.lineWidth=width;g.beginPath();g.moveTo(x1,y1);g.lineTo(x2,y2);g.stroke();g.restore()}
function text(s,x,y,size,{color='#eef2f7',font='Inter,Arial,sans-serif',weight=500,align='left',alpha=1}={}){g.save();g.globalAlpha=alpha;g.fillStyle=color;g.font=`${weight} ${size}px ${font}`;g.textAlign=align;g.textBaseline='alphabetic';g.fillText(s,x,y);g.restore()}
function panel(x,y,w,h,fill='rgba(246,242,233,.97)'){g.save();g.shadowColor='rgba(0,0,0,.18)';g.shadowBlur=30;g.shadowOffsetY=14;g.fillStyle=fill;g.beginPath();g.roundRect(x,y,w,h,28);g.fill();g.restore()}
function cropMarks(x,y,w,h,c='#8391aa'){const m=18,l=24;line(x-m,y,x-m+l,y,c,2,.55);line(x,y-m,x,y-m+l,c,2,.55);line(x+w+m,y,x+w+m-l,y,c,2,.55);line(x+w,y-m,x+w,y-m+l,c,2,.55);line(x-m,y+h,x-m+l,y+h,c,2,.55);line(x,y+h+m,x,y+h+m-l,c,2,.55);line(x+w+m,y+h,x+w+m-l,y+h,c,2,.55);line(x+w,y+h+m,x+w,y+h+m-l,c,2,.55)}
function paperNoise(){
  rect(0,0,W,H,'#121927');
  const gr=g.createRadialGradient(500,410,60,500,410,760);gr.addColorStop(0,'rgba(49,87,213,.18)');gr.addColorStop(1,'rgba(49,87,213,0)');g.fillStyle=gr;g.fillRect(0,0,W,H);
  const warm=g.createRadialGradient(1540,260,20,1540,260,500);warm.addColorStop(0,'rgba(242,184,75,.12)');warm.addColorStop(1,'rgba(242,184,75,0)');g.fillStyle=warm;g.fillRect(0,0,W,H);
  g.save();g.fillStyle='#f3efe4';g.globalAlpha=.035;for(let i=0;i<360;i++){const x=(i*137.7)%W,y=(i*83.3)%H;g.fillRect(x,y,1+(i%3===0),1)}g.restore();
}

const art=await loadGPTArt();
paperNoise();

text('GPT CHARACTER / MASTER 01',62,70,23,{color:'#9ba8be',weight:700});
text('REACH',60,158,92,{font:'Georgia,serif',weight:700,color:'#f3efe4'});
text('approved character art · code controls crop, registration and colour treatment',64,205,24,{color:'#b8c1d1',weight:400});
line(64,238,800,238,'#3157d5',5,.86);

// Character first. No interface and no redraw.
art.plate(g,{x:45,y:285,w:900,h:750},{crop:'full',color:'#0d1422',alpha:.20});
art.draw(g,{x:62,y:265,w:900,h:770},{crop:'full',alpha:1});

panel(1010,58,850,300);cropMarks(1010,58,850,300);
text('FACE / SOURCE DETAIL',1044,104,22,{color:'#5d687b',weight:700});
art.draw(g,{x:1030,y:116,w:810,h:222},{crop:'close',cover:true});

panel(1010,394,395,610);cropMarks(1010,394,395,610);
text('HAND / GESTURE',1044,440,22,{color:'#5d687b',weight:700});
art.draw(g,{x:1030,y:457,w:355,h:523},{crop:'hand',cover:true});

panel(1445,394,395,610);cropMarks(1445,394,395,610);
text('REGISTER / SAME ART',1479,440,22,{color:'#5d687b',weight:700});
art.register(g,{x:1465,y:462,w:355,h:510},{crop:'bust',spread:10});
text('dark plate',1642,941,18,{color:'#697489',align:'center'});
text('+ cobalt plate + original',1642,968,18,{color:'#697489',align:'center'});

g.save();g.globalAlpha=.92;g.translate(640,1011);g.rotate(-.022);rect(-100,-27,1210,57,'#f3efe4');text('normal shots keep the original art · print treatments happen around it, never instead of it',-62,10,22,{color:'#273046',weight:650});g.restore();

window.GPT_ART_READY=true;
