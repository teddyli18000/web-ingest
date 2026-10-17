import {PALETTE as P} from './palette.js';

const ROLES=['shadow','ink','skinDeep','skin','hair','paper'];
const OFFSETS=[[-.70,.20],[-.28,.08],[.42,.18],[.28,-.16],[.08,-.42],[0,0]];

export const GPT_ART_PALETTE={
  shadow:'#65739a',
  ink:P.ink,
  skinDeep:'#d59a8f',
  skin:'#f1c9bd',
  hair:'#c7c7da',
  paper:'#fbf6ed'
};

export const GPT_PRINT_PALETTE={
  shadow:P.cobalt,
  ink:P.ink,
  skinDeep:P.gold,
  skin:P.gold2,
  hair:P.cobalt2,
  paper:P.white
};

export async function loadGPTArt(){
  const url=new URL('../../assets/gpt/reach.svg',import.meta.url);
  const source=await fetch(url).then(r=>{
    if(!r.ok)throw new Error(`GPT art load failed: ${r.status}`);
    return r.text();
  });
  const doc=new DOMParser().parseFromString(source,'image/svg+xml');
  const nodes=[...doc.querySelectorAll('path')];
  if(nodes.length!==ROLES.length)throw new Error(`reach.svg: expected ${ROLES.length} plates, got ${nodes.length}`);
  const paths=nodes.map((node,i)=>({role:ROLES[i],path:new Path2D(node.getAttribute('d'))}));
  return new GPTArt(paths);
}

export class GPTArt{
  constructor(paths){this.paths=paths;this.w=788;this.h=887;}

  draw(d,{x=0,y=0,scale=1,alpha=1,misregister=0,palette=GPT_ART_PALETTE,plateAlpha=null}={}){
    const g=d.g??d;
    g.save();
    g.translate(x,y);g.scale(scale,scale);
    for(let i=0;i<this.paths.length;i++){
      const {role,path}=this.paths[i];
      const [ox,oy]=OFFSETS[i];
      g.save();
      g.translate(ox*misregister,oy*misregister);
      g.globalAlpha=alpha*(plateAlpha?.[role]??1);
      g.fillStyle=palette[role]??GPT_ART_PALETTE[role];
      g.fill(path,'evenodd');
      g.restore();
    }
    g.restore();
  }

  // A crop is still the same vector master; no bitmap enlargement happens.
  crop(d,rect,{focusX,focusY,zoom=1,misregister=0,palette=GPT_ART_PALETTE,alpha=1}={}){
    const g=d.g??d;
    const fit=Math.max(rect.w/this.w,rect.h/this.h)*zoom;
    const fx=focusX??this.w/2,fy=focusY??this.h/2;
    const x=rect.x+rect.w/2-fx*fit,y=rect.y+rect.h/2-fy*fit;
    g.save();
    g.beginPath();g.roundRect(rect.x,rect.y,rect.w,rect.h,rect.r??24);g.clip();
    this.draw(d,{x,y,scale:fit,misregister,palette,alpha});
    g.restore();
  }
}
