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
  rect(0,0,W,H,'#171d2b');
  const gr=g.createRadialGradient(520,360,60,520,360,720);gr.addColorStop(0,'rgba(49,87,213,.18)');gr.addColorStop(1,'rgba(49,87,213,0)');g.fillStyle=gr;g.fillRect(0,0,W,H);
  g.save();g.fillStyle='#f3efe4';g.globalAlpha=.035;for(let i=0;i<360;i++){const x=(i*137.7)%W,y=(i*83.3)%H;g.fillRect(x,y,1+(i%3===0),1)}g.restore();
}

const art=await loadGPTArt();
paperNoise();

// Left: the character must hold the frame before any interface is added.
text('GPT / character master 01',74,86,24,{color:'#9ba8be',weight:600});
text('REACH',72,168,86,{font:'Georgia,serif',weight:700});
text('approved existing art → transparent character asset → code-directed performance',76,214,25,{color:'#b8c1d1',weight:400});
line(76,246,808,246,'#3157d5',5,.82);

art.draw(g,{x:58,y:268,w:900,h:770},{crop:'full',alpha:1});
// shadow/keyline behind the actual figure, not a UI card
art.plate(g,{x:44,y:282,w:900,h:770},{crop:'full',color:'#0e1421',alpha:.20});
art.draw(g,{x:58,y:268,w:900,h:770},{crop:'full',alpha:1});

// Right column: prove that one high-quality master survives cinematic crops.
panel(1040,70,800,290);
cropMarks(1040,70,800,290);
text('BUST CROP',1080,118,22,{color:'#5d687b',weight:700});
art.draw(g,{x:1070,y:125,w:735,h:215},{crop:'bust',cover:true});

panel(1040,390,380,610,'rgba(246,242,233,.98)');
cropMarks(1040,390,380,610);
text('CLOSE',1072,440,22,{color:'#5d687b',weight:700});
art.draw(g,{x:1055,y:458,w:350,h:515},{crop:'close',cover:true});

panel(1460,390,380,610,'rgba(246,242,233,.98)');
cropMarks(1460,390,380,610);
text('REGISTER',1492,440,22,{color:'#5d687b',weight:700});
// no fake redraw: the actual alpha is reprinted in three offsets.
art.register(g,{x:1480,y:470,w:335,h:470},{crop:'full',spread:12});
text('same silhouette',1650,947,21,{color:'#5d687b',align:'center',weight:500});
text('three code-controlled plates',1650,977,19,{color:'#7f8898',align:'center',weight:400});

// A restrained foreground strip makes the lab itself obey the three-layer rule.
g.save();g.globalAlpha=.8;g.translate(730,1000);g.rotate(-.035);rect(-90,-18,1280,52,'#f3efe4');text('no Path2D face redraw · no full-frame still · asset stays character-only',-55,18,22,{color:'#273046',weight:600});g.restore();

window.GPT_ART_READY=true;
