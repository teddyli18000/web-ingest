import {PALETTE as P} from '../engine/palette.js';
import {easeInOut,easeOut,lerp,prog,smooth} from '../engine/timing.js';
import {renderDraftsV6} from './drafts_v6.js';

const T1=18.30,T2=21.80;

function coverImage(g,img,x,y,w,h,{alpha=1,pan=0}={}){
  const dar=w/h,iar=img.naturalWidth/img.naturalHeight;
  let sx=0,sy=0,sw=img.naturalWidth,sh=img.naturalHeight;
  if(iar>dar){sw=sh*dar;sx=(img.naturalWidth-sw)*(.58+pan*.08);}
  else{sh=sw/dar;sy=(img.naturalHeight-sh)*.5;}
  g.save();g.globalAlpha=alpha;g.drawImage(img,sx,sy,sw,sh,x,y,w,h);g.restore();
}

function cropMarks(d,x,y,w,h,a){
  const m=15,l=30,c=P.cobalt2;
  d.line(x-m,y,x+l,y,{color:c,width:2,alpha:a});d.line(x,y-m,x,y+l,{color:c,width:2,alpha:a});
  d.line(x+w+m,y,x+w-l,y,{color:c,width:2,alpha:a});d.line(x+w,y-m,x+w,y+l,{color:c,width:2,alpha:a});
  d.line(x-m,y+h,x+l,y+h,{color:c,width:2,alpha:a});d.line(x,y+h+m,x,y+h-l,{color:c,width:2,alpha:a});
  d.line(x+w+m,y+h,x+w-l,y+h,{color:c,width:2,alpha:a});d.line(x+w,y+h+m,x+w,y+h-l,{color:c,width:2,alpha:a});
}

function thinkingPortrait(d,t,img){
  const enter=easeOut(prog(t,T1,T1+.58));
  const leave=1-smooth(prog(t,T2-.58,T2));
  const a=enter*leave;if(a<=0)return;

  const x=lerp(-720,54,enter),y=lerp(238,166,enter),w=650,h=603;
  const rot=lerp(-.065,-.018,enter)+easeInOut(prog(t,T2-.58,T2))*.045;
  const lift=easeInOut(prog(t,T2-.58,T2))*150;
  const pan=prog(t,T1,T2);

  d.save(()=>{
    const g=d.g;
    g.translate(x+w/2,y+h/2-lift);g.rotate(rot);g.translate(-w/2,-h/2);

    // Physical proof-card stack. The source scene stays intact inside the card.
    d.rrect(19,23,w,h,18,{fill:P.ink,alpha:.12*a});
    d.rrect(7,10,w,h,18,{fill:'#dbe5fb',alpha:.38*a});
    d.rrect(0,0,w,h,18,{fill:'#fffdf8',stroke:'rgba(53,65,92,.22)',width:2,shadow:.44,alpha:a});

    g.save();g.beginPath();g.roundRect(18,18,w-36,h-92,12);g.clip();
    coverImage(g,img,18,18,w-36,h-92,{alpha:a,pan});
    // Very light print treatment around the real pose, not over the face.
    d.rect(18,18,8,h-92,{fill:P.cobalt,alpha:.24*a});
    d.rect(w-30,18,12,h-92,{fill:P.gold,alpha:.15*a});
    g.restore();

    d.line(34,h-58,w-36,h-58,{color:P.cobalt,width:5,alpha:.46*a});
    d.text('RECHECK / PASS 02',34,h-27,{size:20,font:'mono',weight:700,color:P.ink2,alpha:.58*a});
    d.text('look again.',w-38,h-27,{size:24,font:'serif',italic:true,align:'right',color:P.ink,alpha:.68*a});
    cropMarks(d,0,0,w,h,.34*a);
  });
}

export function renderDraftsV8(d,t,model,poses){
  renderDraftsV6(d,t,model);
  if(t>=T1&&t<T2&&poses?.think)thinkingPortrait(d,t,poses.think);
}

export const DRAFTS_V8_CUTS=[15,T1,T2,25.20,30];
