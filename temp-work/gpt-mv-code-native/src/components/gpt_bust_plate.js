const SOURCE={
  name:'gpt-bust-color-v3',
  url:'/assets/gpt/bust_v3.webp',
  sha:'76164bf82a81c67b9efb795033e71972a6c8512d1fa73370026736028dd6b0eb',
  width:550,height:640,
};

async function loadImage(){
  const raw=await fetch(SOURCE.url,{cache:'no-store'}).then(r=>r.arrayBuffer());
  const hash=await crypto.subtle.digest('SHA-256',raw);
  const sha=[...new Uint8Array(hash)].map(b=>b.toString(16).padStart(2,'0')).join('');
  if(sha!==SOURCE.sha)throw new Error('bust plate sha mismatch: '+sha);
  const url=URL.createObjectURL(new Blob([raw],{type:'image/webp'}));
  const img=new Image();img.src=url;await img.decode();URL.revokeObjectURL(url);
  if(img.naturalWidth!==SOURCE.width||img.naturalHeight!==SOURCE.height){
    throw new Error('bust plate dimension mismatch');
  }
  return img;
}

function fit(src,dst,cover=false){
  const ar=src.w/src.h,dar=dst.w/dst.h;let w,h,x,y;
  if((cover&&ar>dar)||(!cover&&ar<dar)){h=dst.h;w=h*ar;x=dst.x+(dst.w-w)/2;y=dst.y;}
  else{w=dst.w;h=w/ar;x=dst.x;y=dst.y+(dst.h-h)/2;}
  return{x,y,w,h};
}

export class GPTBustPlate{
  constructor(img){this.img=img;this.source=SOURCE.name;this.width=img.naturalWidth;this.height=img.naturalHeight;this.tintCache=new Map();}
  crop(name='full'){
    if(name==='face')return{x:0,y:38,w:455,h:355};
    if(name==='eyes')return{x:65,y:135,w:310,h:185};
    return{x:0,y:0,w:this.width,h:this.height};
  }
  _draw(ctx,source,dst,{crop='full',alpha=1,rot=0,flip=false,cover=false}={}){
    const c=this.crop(crop),f=fit(c,dst,cover);ctx.save();ctx.globalAlpha=alpha;
    ctx.translate(f.x+f.w/2,f.y+f.h/2);ctx.rotate(rot);ctx.scale(flip?-1:1,1);
    ctx.drawImage(source,c.x,c.y,c.w,c.h,-f.w/2,-f.h/2,f.w,f.h);ctx.restore();return f;
  }
  draw(ctx,dst,opts={}){return this._draw(ctx,this.img,dst,opts);}
  tinted(color){
    if(this.tintCache.has(color))return this.tintCache.get(color);
    const c=document.createElement('canvas');c.width=this.width;c.height=this.height;
    const g=c.getContext('2d');g.drawImage(this.img,0,0);g.globalCompositeOperation='source-in';g.fillStyle=color;g.fillRect(0,0,c.width,c.height);g.globalCompositeOperation='source-over';this.tintCache.set(color,c);return c;
  }
  silhouette(ctx,dst,{color='#3157d5',...opts}={}){return this._draw(ctx,this.tinted(color),dst,opts);}
  register(ctx,dst,{alpha=1,spread=10,rot=0,crop='full'}={}){
    this.silhouette(ctx,{x:dst.x-spread,y:dst.y+spread*.5,w:dst.w,h:dst.h},{color:'#172033',alpha:alpha*.62,rot,crop});
    this.silhouette(ctx,{x:dst.x+spread*.72,y:dst.y-spread*.55,w:dst.w,h:dst.h},{color:'#3157d5',alpha:alpha*.68,rot,crop});
    this.draw(ctx,dst,{alpha,rot,crop});
  }
}

export async function loadGPTBustPlate(){return new GPTBustPlate(await loadImage());}
