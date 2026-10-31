const SOURCE={
  name:'gpt-bust-print-v2', prefix:'bust_plate.b64.', chunks:4,
  sha:'7220862191e495dccfae7a917f2d65713c4b6b7e8dcd06c68cf7f2d79e822e0a',
  width:550, height:640,
};

async function loadImage(){
  const parts=await Promise.all(Array.from({length:SOURCE.chunks},async(_,i)=>{
    const r=await fetch(`/assets/gpt/${SOURCE.prefix}${i}`,{cache:'no-store'});
    if(!r.ok)throw new Error(`bust plate chunk ${i} HTTP ${r.status}`);
    return (await r.text()).trim();
  }));
  const b64=parts.join('');
  const raw=atob(b64),bytes=new Uint8Array(raw.length);
  for(let i=0;i<raw.length;i++)bytes[i]=raw.charCodeAt(i);
  const digest=await crypto.subtle.digest('SHA-256',bytes);
  const sha=[...new Uint8Array(digest)].map(b=>b.toString(16).padStart(2,'0')).join('');
  if(sha!==SOURCE.sha)throw new Error(`bust plate sha mismatch: ${sha}`);
  const img=new Image(); img.src=`data:image/webp;base64,${b64}`; await img.decode();
  if(img.naturalWidth!==SOURCE.width||img.naturalHeight!==SOURCE.height){
    throw new Error(`bust plate size ${img.naturalWidth}x${img.naturalHeight}`);
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
