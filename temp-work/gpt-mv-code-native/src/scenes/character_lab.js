const PAPER='#f3efe4',PAPER2='#fffaf0',INK='#172033',INK2='#5d6064',BLUE='#3157d5',GOLD='#e8b928',SKIN='#edb19e';

function panel(d,x,y,w,h,{fill=PAPER2,label='',sub=''}={}){
  d.rrect(x,y,w,h,22,{fill,stroke:'rgba(23,32,51,.15)',width:1.5,shadow:.34});
  d.text(label,x+32,y+42,{size:18,font:'mono',weight:700,color:fill===INK?'#f3efe4':INK2,alpha:.55});
  if(sub)d.text(sub,x+32,y+70,{size:16,font:'mono',color:fill===INK?'#c8d0df':INK2,alpha:.34});
}

export function renderCharacterLab(d,t,plate){
  d.rect(0,0,1920,1080,{fill:'#d8d0c5'});
  d.gradRect(0,0,1920,1080,[[0,'rgba(255,245,222,.32)'],[1,'rgba(49,87,213,.05)']],true);
  d.text('GPT / CHARACTER PLATE LAB',62,72,{size:24,font:'mono',weight:700,color:INK,alpha:.62});
  d.text('clean bust plate · no scene pixels · 550×640 source',62,108,{size:19,font:'mono',color:INK2,alpha:.38});

  panel(d,58,145,855,390,{label:'01 / RAW PRINT',sub:'paper · intended working size'});
  plate.draw(d.g,{x:270,y:198,w:440,h:310},{alpha:1});
  d.line(235,520,750,520,{color:GOLD,width:4,alpha:.28});

  panel(d,1007,145,855,390,{label:'02 / REGISTRATION',sub:'graphite + cobalt misregistration'});
  plate.register(d.g,{x:1220,y:188,w:445,h:325},{spread:13,alpha:1,rot:.008});
  d.line(1170,520,1710,520,{color:BLUE,width:4,alpha:.26});

  panel(d,58,575,855,430,{label:'03 / FACE CROP',sub:'large crop · edge/face stress test'});
  d.save(()=>{
    const g=d.g;g.beginPath();g.roundRect(90,640,790,330,16);g.clip();
    plate.draw(g,{x:55,y:570,w:895,h:470},{crop:'face',cover:true});
  });
  d.line(100,958,860,958,{color:GOLD,width:4,alpha:.28});

  panel(d,1007,575,855,430,{fill:INK,label:'04 / SILHOUETTE',sub:'alpha integrity on dark field'});
  d.glow(1435,800,360,BLUE,.12);
  plate.silhouette(d.g,{x:1200,y:625,w:470,h:350},{color:BLUE,alpha:.94});
  plate.silhouette(d.g,{x:1211,y:631,w:470,h:350},{color:'#f3efe4',alpha:.14});
  d.circle(1740,920,8,{fill:GOLD,alpha:.78});
  d.text(plate.source,1835,1037,{size:16,font:'mono',align:'right',color:INK2,alpha:.34});
}
