const CROP_N = {
  full:  {x:0,          y:0,          w:1,          h:1},
  bust:  {x:.125,       y:.0277778,   w:.75,        h:.6666667},
  close: {x:.2578125,   y:.0763889,   w:.5234375,   h:.4305556},
  hand:  {x:.28125,     y:.4166667,   w:.71875,     h:.5833333},
};

const CHUNKS=8;
const EXPECTED_SHA='33e1f43e1df5fed02d32928673158dbcc3f1eb0ba16f59fbe51bf1579ed2e271';

async function loadPayload(){
  const parts=await Promise.all(Array.from({length:CHUNKS},async(_,i)=>{
    const r=await fetch(`/assets/gpt/reach.b64.${i}`,{cache:'no-store'});
    if(!r.ok)throw new Error(`character chunk ${i} HTTP ${r.status}`);
    return (await r.text()).trim();
  }));
  const b64=parts.join('');
  const raw=atob(b64), bytes=new Uint8Array(raw.length);
  for(let i=0;i<raw.length;i++)bytes[i]=raw.charCodeAt(i);
  const digest=await crypto.subtle.digest('SHA-256',bytes);
  const sha=[...new Uint8Array(digest)].map(b=>b.toString(16).padStart(2,'0')).join('');
  if(sha!==EXPECTED_SHA)throw new Error(`character payload sha mismatch: ${sha}`);
  return `data:image/webp;base64,${b64}`;
}

export async function loadGPTArt(){
  const img=new Image();
  img.src=await loadPayload();
  await img.decode();
  if(img.naturalWidth!==420||img.naturalHeight!==473)throw new Error(`unexpected character size ${img.naturalWidth}x${img.naturalHeight}`);
  return new GPTArt(img);
}

export class GPTArt{
  constructor(img){
    this.img=img;
    this.mask=document.createElement('canvas');
    this.mask.width=img.naturalWidth; this.mask.height=img.naturalHeight;
    const g=this.mask.getContext('2d');
    g.clearRect(0,0,this.mask.width,this.mask.height);
    g.drawImage(img,0,0);
    g.globalCompositeOperation='source-in';
    g.fillStyle='#fff'; g.fillRect(0,0,this.mask.width,this.mask.height);
    g.globalCompositeOperation='source-over';
    this.tintCache=new Map();
  }

  crop(name='full'){
    const n=CROP_N[name]??CROP_N.full,W=this.img.naturalWidth,H=this.img.naturalHeight;
    return {x:n.x*W,y:n.y*H,w:n.w*W,h:n.h*H};
  }

  _fit(dst,crop,cover=false){
    const ar=crop.w/crop.h,dar=dst.w/dst.h;
    let w,h,x,y;
    if((cover&&ar>dar)||(!cover&&ar<dar)){
      h=dst.h; w=h*ar; x=dst.x+(dst.w-w)/2; y=dst.y;
    }else{
      w=dst.w; h=w/ar; x=dst.x; y=dst.y+(dst.h-h)/2;
    }
    return {x,y,w,h};
  }

  _drawSource(ctx,source,dst,{crop='full',alpha=1,flip=false,rot=0,cover=false}={}){
    const c=this.crop(crop),f=this._fit(dst,c,cover);
    ctx.save();
    ctx.globalAlpha=alpha;
    ctx.translate(f.x+f.w/2,f.y+f.h/2);
    if(rot)ctx.rotate(rot);
    ctx.scale(flip?-1:1,1);
    ctx.drawImage(source,c.x,c.y,c.w,c.h,-f.w/2,-f.h/2,f.w,f.h);
    ctx.restore();
    return f;
  }

  draw(ctx,dst,opts={}){return this._drawSource(ctx,this.img,dst,opts);}

  tinted(color){
    if(this.tintCache.has(color))return this.tintCache.get(color);
    const c=document.createElement('canvas');c.width=this.mask.width;c.height=this.mask.height;
    const g=c.getContext('2d');g.drawImage(this.mask,0,0);g.globalCompositeOperation='source-in';
    g.fillStyle=color;g.fillRect(0,0,c.width,c.height);g.globalCompositeOperation='source-over';
    this.tintCache.set(color,c);return c;
  }

  plate(ctx,dst,{color='#3157d5',...opts}={}){
    return this._drawSource(ctx,this.tinted(color),dst,opts);
  }

  // Registration is a treatment around the real artwork, not a replacement for it.
  register(ctx,dst,{crop='full',alpha=1,spread=12,flip=false,rot=0}={}){
    this.plate(ctx,{x:dst.x-spread,y:dst.y+spread*.55,w:dst.w,h:dst.h},{crop,color:'#172033',alpha:alpha*.62,flip,rot});
    this.plate(ctx,{x:dst.x+spread*.72,y:dst.y-spread*.58,w:dst.w,h:dst.h},{crop,color:'#3157d5',alpha:alpha*.72,flip,rot});
    this.draw(ctx,dst,{crop,alpha,flip,rot});
  }
}

export const GPT_CROPS=CROP_N;
