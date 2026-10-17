const CROPS = {
  full:  {x:0,   y:0,  w:640, h:720},
  bust:  {x:80,  y:20, w:480, h:480},
  close: {x:165, y:55, w:335, h:310},
  hand:  {x:180, y:300,w:460, h:420},
};

export async function loadGPTArt(){
  const img=new Image();
  img.src='/assets/gpt/reach.webp';
  await img.decode();
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

  crop(name='full'){ return CROPS[name] ?? CROPS.full; }

  _fit(dst,crop,cover=false){
    const ar=crop.w/crop.h, dar=dst.w/dst.h;
    let w,h,x,y;
    if((cover && ar>dar)||(!cover && ar<dar)){
      h=dst.h; w=h*ar; x=dst.x+(dst.w-w)/2; y=dst.y;
    }else{
      w=dst.w; h=w/ar; x=dst.x; y=dst.y+(dst.h-h)/2;
    }
    return {x,y,w,h};
  }

  _drawSource(ctx,source,dst,{crop='full',alpha=1,flip=false,rot=0,cover=false}={}){
    const c=this.crop(crop), f=this._fit(dst,c,cover);
    ctx.save();
    ctx.globalAlpha=alpha;
    ctx.translate(f.x+f.w/2,f.y+f.h/2);
    if(rot)ctx.rotate(rot);
    ctx.scale(flip?-1:1,1);
    ctx.drawImage(source,c.x,c.y,c.w,c.h,-f.w/2,-f.h/2,f.w,f.h);
    ctx.restore();
    return f;
  }

  draw(ctx,dst,opts={}){ return this._drawSource(ctx,this.img,dst,opts); }

  tinted(color){
    if(this.tintCache.has(color))return this.tintCache.get(color);
    const c=document.createElement('canvas'); c.width=this.mask.width; c.height=this.mask.height;
    const g=c.getContext('2d'); g.drawImage(this.mask,0,0); g.globalCompositeOperation='source-in';
    g.fillStyle=color; g.fillRect(0,0,c.width,c.height); g.globalCompositeOperation='source-over';
    this.tintCache.set(color,c); return c;
  }

  plate(ctx,dst,{color='#3157d5',...opts}={}){
    return this._drawSource(ctx,this.tinted(color),dst,opts);
  }

  register(ctx,dst,{crop='full',alpha=1,spread=12,flip=false,rot=0}={}){
    const layers=[
      {color:'#172033',dx:-spread,dy:spread*.55,a:.72},
      {color:'#3157d5',dx:spread*.72,dy:-spread*.58,a:.86},
      {color:'#f3efe4',dx:0,dy:0,a:1},
    ];
    for(const p of layers){
      this.plate(ctx,{x:dst.x+p.dx,y:dst.y+p.dy,w:dst.w,h:dst.h},{crop,color:p.color,alpha:alpha*p.a,flip,rot});
    }
  }
}

export const GPT_CROPS=CROPS;
