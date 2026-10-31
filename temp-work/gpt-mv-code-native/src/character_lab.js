import {loadGPTBustPlate} from './components/gpt_bust_plate.js';

const canvas=document.getElementById('stage');
const g=canvas.getContext('2d',{alpha:false});
const W=canvas.width,H=canvas.height;
const PAPER='#f3efe4',PAPER2='#fffaf0',INK='#172033',INK2='#5d6064',BLUE='#3157d5',GOLD='#e8b928';

function rect(x,y,w,h,fill){g.fillStyle=fill;g.fillRect(x,y,w,h)}
function line(x1,y1,x2,y2,color=INK2,width=2,alpha=1){g.save();g.globalAlpha=alpha;g.strokeStyle=color;g.lineWidth=width;g.beginPath();g.moveTo(x1,y1);g.lineTo(x2,y2);g.stroke();g.restore()}
function text(s,x,y,size,{color=INK,font='Inter,Arial,sans-serif',weight=500,align='left',alpha=1}={}){g.save();g.globalAlpha=alpha;g.fillStyle=color;g.font=`${weight} ${size}px ${font}`;g.textAlign=align;g.textBaseline='alphabetic';g.fillText(s,x,y);g.restore()}
function panel(x,y,w,h,fill=PAPER2){g.save();g.shadowColor='rgba(17,24,39,.15)';g.shadowBlur=28;g.shadowOffsetY=13;g.fillStyle=fill;g.beginPath();g.roundRect(x,y,w,h,24);g.fill();g.restore();g.strokeStyle='rgba(23,32,51,.13)';g.lineWidth=1.4;g.beginPath();g.roundRect(x,y,w,h,24);g.stroke()}
function cropMarks(x,y,w,h,c='#8391aa'){const m=15,l=22;line(x-m,y,x-m+l,y,c,2,.48);line(x,y-m,x,y-m+l,c,2,.48);line(x+w+m,y,x+w+m-l,y,c,2,.48);line(x+w,y-m,x+w,y-m+l,c,2,.48);line(x-m,y+h,x-m+l,y+h,c,2,.48);line(x,y+h+m,x,y+h+m-l,c,2,.48);line(x+w+m,y+h,x+w+m-l,y+h,c,2,.48);line(x+w,y+h+m,x+w,y+h+m-l,c,2,.48)}
function heading(x,y,label,sub,dark=false){text(label,x,y,19,{color:dark?'#f3efe4':INK2,weight:700,alpha:.58});text(sub,x,y+28,15,{color:dark?'#c4ccda':INK2,alpha:.35});}

const plate=await loadGPTBustPlate();
rect(0,0,W,H,'#d8d0c5');
const glow=g.createRadialGradient(1480,180,40,1480,180,660);glow.addColorStop(0,'rgba(232,185,40,.16)');glow.addColorStop(1,'rgba(232,185,40,0)');g.fillStyle=glow;g.fillRect(0,0,W,H);
text('GPT / CHARACTER PLATE LAB',62,66,23,{color:INK,weight:700,alpha:.62});
text('bust-print-v2 · 4-colour plate · no scene pixels',62,101,18,{color:INK2,alpha:.38});
line(62,124,760,124,BLUE,5,.60);

panel(58,155,855,380);cropMarks(58,155,855,380);heading(90,198,'01 / RAW PRINT','paper field · intended working scale');
plate.draw(g,{x:265,y:205,w:470,h:305},{alpha:1});
line(215,507,760,507,GOLD,4,.28);

panel(1007,155,855,380);cropMarks(1007,155,855,380);heading(1039,198,'02 / REGISTRATION','graphite + cobalt offsets around the same plate');
plate.register(g,{x:1215,y:203,w:470,h:310},{spread:13,alpha:1,rot:.006});
line(1175,507,1720,507,BLUE,4,.26);

panel(58,585,855,420);cropMarks(58,585,855,420);heading(90,628,'03 / FACE CROP','large crop · face and edge stress test');
g.save();g.beginPath();g.roundRect(88,660,795,310,15);g.clip();plate.draw(g,{x:45,y:590,w:900,h:455},{crop:'face',cover:true});g.restore();
line(100,958,862,958,GOLD,4,.28);

panel(1007,585,855,420,INK);cropMarks(1007,585,855,420,'#73809a');heading(1039,628,'04 / SILHOUETTE','alpha integrity · no rectangular residue',true);
const gl=g.createRadialGradient(1440,810,40,1440,810,380);gl.addColorStop(0,'rgba(49,87,213,.19)');gl.addColorStop(1,'rgba(49,87,213,0)');g.fillStyle=gl;g.fillRect(1040,650,790,330);
plate.silhouette(g,{x:1210,y:650,w:470,h:320},{color:BLUE,alpha:.95});
plate.silhouette(g,{x:1220,y:656,w:470,h:320},{color:PAPER,alpha:.12});
text(plate.source,1828,984,15,{color:'#aeb8ca',align:'right',alpha:.38});

window.GPT_ART_SOURCE=plate.source;
window.GPT_ART_READY=true;
