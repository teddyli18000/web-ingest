import {Draw} from './engine/draw.js';
import {loadGPTArt,GPT_ART_PALETTE,GPT_PRINT_PALETTE} from './engine/gpt_art.js';

const canvas=document.getElementById('stage');
const g=canvas.getContext('2d',{alpha:false});
const d=new Draw(g,canvas.width,canvas.height);
const W=canvas.width,H=canvas.height;

function backdrop(){
  g.fillStyle='#111725';g.fillRect(0,0,W,H);
  const a=g.createRadialGradient(450,430,40,450,430,720);
  a.addColorStop(0,'rgba(49,87,213,.22)');a.addColorStop(.55,'rgba(49,87,213,.06)');a.addColorStop(1,'rgba(49,87,213,0)');
  g.fillStyle=a;g.fillRect(0,0,W,H);
  const b=g.createRadialGradient(1510,290,20,1510,290,520);
  b.addColorStop(0,'rgba(232,185,40,.13)');b.addColorStop(1,'rgba(232,185,40,0)');
  g.fillStyle=b;g.fillRect(0,0,W,H);
  g.save();g.globalAlpha=.04;g.fillStyle='#f3efe4';
  for(let i=0;i<420;i++)g.fillRect((i*137.3)%W,(i*83.9)%H,1+(i%5===0),1);
  g.restore();
}
function label(s,x,y,size=23,alpha=.65){d.text(s,x,y,{size,color:'#d7dfed',weight:600,alpha});}
function frame(x,y,w,h,r=28){
  d.rrect(x,y,w,h,r,{fill:'rgba(244,239,229,.965)',stroke:'rgba(126,165,245,.24)',width:1.5,shadow:.55});
}
function cropMarks(x,y,w,h){
  const c='rgba(126,165,245,.55)',m=14,l=27;
  d.line(x-m,y,x-m+l,y,{color:c,width:2});d.line(x,y-m,x,y-m+l,{color:c,width:2});
  d.line(x+w+m,y,x+w+m-l,y,{color:c,width:2});d.line(x+w,y-m,x+w,y-m+l,{color:c,width:2});
  d.line(x-m,y+h,x-m+l,y+h,{color:c,width:2});d.line(x,y+h+m,x,y+h+m-l,{color:c,width:2});
  d.line(x+w+m,y+h,x+w+m-l,y+h,{color:c,width:2});d.line(x+w,y+h+m,x+w,y+h+m-l,{color:c,width:2});
}

const art=await loadGPTArt();
backdrop();

// The lab is deliberately not a UI mockup: the figure must carry the frame by herself.
d.text('GPT CHARACTER / MASTER 01',72,78,{size:23,color:'#9eabc2',weight:700});
d.text('REACH',70,168,{size:94,font:'serif',weight:700,color:'#f3efe4'});
d.text('existing approved GPT art → six vector ink plates → code-controlled crops',74,213,{size:25,color:'#aab5c8',weight:400});
d.line(74,245,820,245,{color:'#3157d5',width:5,alpha:.95});

// Full figure: vector plate master, not the old hand-drawn mascot.
g.save();
g.translate(42,178);g.rotate(-.015);
art.draw(d,{x:62,y:112,scale:.82,alpha:1,palette:GPT_ART_PALETTE});
g.restore();
// Very restrained print shadow adds separation without changing the drawing.
art.draw(d,{x:94,y:296,scale:.79,alpha:.13,misregister:13,palette:GPT_PRINT_PALETTE});
art.draw(d,{x:82,y:286,scale:.79,alpha:1,palette:GPT_ART_PALETTE});

// FACE — vector closeup: if this cannot survive 2.3x, the master fails.
frame(980,68,860,292);cropMarks(980,68,860,292);label('FACE / 2.3× VECTOR CROP',1018,112);
art.crop(d,{x:1002,y:127,w:816,h:211,r:20},{focusX:510,focusY:258,zoom:2.3,palette:GPT_ART_PALETTE});

// HAND / gesture closeup.
frame(980,397,410,600);cropMarks(980,397,410,600);label('GESTURE / 2.4×',1015,442);
art.crop(d,{x:1000,y:463,w:370,h:510,r:20},{focusX:665,focusY:675,zoom:2.4,palette:GPT_ART_PALETTE});

// Same exact paths reprinted out of register. No alternate drawing is introduced.
frame(1430,397,410,600);cropMarks(1430,397,410,600);label('REGISTER / SAME PATHS',1465,442);
art.crop(d,{x:1450,y:463,w:370,h:510,r:20},{focusX:510,focusY:455,zoom:1.72,misregister:15,palette:GPT_PRINT_PALETTE});

// Foreground proof strip: three layers and a physical print feel, not product chrome.
g.save();g.translate(690,1010);g.rotate(-.023);
d.rrect(-120,-28,1160,58,5,{fill:'#f3efe4',stroke:'rgba(23,32,51,.16)',width:1,shadow:.22});
d.text('character art survives crop · code controls registration, colour and camera — not her face',-82,10,{size:22,color:'#29334a',weight:600});
g.restore();

window.GPT_ART_READY=true;
