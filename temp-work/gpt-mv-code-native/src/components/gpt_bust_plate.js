const SOURCE={
  name:'gpt-bust-matted-v4',
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
  return matteCharacter(img);
}


function matteCharacter(img){
  const w=img.naturalWidth,h=img.naturalHeight,n=w*h;
  const canvas=document.createElement('canvas');
  canvas.width=w;canvas.height=h;
  const ctx=canvas.getContext('2d',{willReadFrequently:true});
  ctx.drawImage(img,0,0);
  const frame=ctx.getImageData(0,0,w,h),rgba=frame.data;
  const navy=new Uint8Array(n);
  for(let y=0;y<190;y++)for(let x=231;x<w;x++){
    const p=y*w+x,i=p*4;
    const r=rgba[i],g=rgba[i+1],b=rgba[i+2],a=rgba[i+3];
    if(a>16&&b>r+12&&b>g+5&&r<125&&g<130&&b<169)navy[p]=1;
  }
  // Keep only substantial patches in the limited region behind the hair.
  const morph=(source,dilate)=>{
    const target=new Uint8Array(n),v=dilate?1:0;
    for(let y=0;y<195;y++)for(let x=227;x<w;x++){
      let hit=!dilate;
      for(let dy=-2;dy<=2;dy++)for(let dx=-2;dx<=2;dx++){
        const xx=x+dx,yy=y+dy;
        const px=xx>=0&&xx<w&&yy>=0&&yy<h?source[yy*w+xx]:0;
        if(dilate&&px){hit=true;break;}
        if(!dilate&&!px){hit=false;break;}
      }
      target[y*w+x]=hit?1:0;
    }
    return target;
  };
  const joined=morph(morph(navy,true),false);
  const visited=new Uint8Array(n),patch=new Uint8Array(n);
  const queue=new Int32Array(n);
  for(let y=0;y<195;y++)for(let x=227;x<w;x++){
    const start=y*w+x;
    if(!joined[start]||visited[start])continue;
    let head=0,tail=1;queue[0]=start;visited[start]=1;
    while(head<tail){
      const p=queue[head++],px=p%w,py=Math.floor(p/w);
      for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){
        const xx=px+dx,yy=py+dy;
        if(xx<227||xx>=w||yy<0||yy>=195)continue;
        const q=yy*w+xx;
        if(joined[q]&&!visited[q]){visited[q]=1;queue[tail++]=q;}
      }
    }
    if(tail>=20)for(let j=0;j<tail;j++)patch[queue[j]]=1;
  }
  // Small blur avoids cutout stair steps at the edge of the navy paper.
  const kernel=[1,2,1],tmp=new Float32Array(n);
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){
    let sum=0;
    for(let k=-1;k<=1;k++){
      const xx=Math.max(0,Math.min(w-1,x+k));
      sum+=patch[y*w+xx]*kernel[k+1];
    }
    tmp[y*w+x]=sum/4;
  }
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){
    const p=y*w+x,i=p*4;
    let top=0;
    for(let k=-1;k<=1;k++){
      const yy=Math.max(0,Math.min(h-1,y+k));
      top+=tmp[yy*w+x]*kernel[k+1];
    }
    top/=4;
    const begin=372+Math.max(-8,Math.min(10,(350-x)*.035));
    let t=Math.max(0,Math.min(1,(y-begin)/65));
    t=t*t*(3-2*t);
    rgba[i+3]=Math.round(rgba[i+3]*(1-top)*(1-t));
  }
  ctx.putImageData(frame,0,0);
  return canvas;
}

function fit(src,dst,cover=false){
  const ar=src.w/src.h,dar=dst.w/dst.h;let w,h,x,y;
  if((cover&&ar>dar)||(!cover&&ar<dar)){h=dst.h;w=h*ar;x=dst.x+(dst.w-w)/2;y=dst.y;}
  else{w=dst.w;h=w/ar;x=dst.x;y=dst.y+(dst.h-h)/2;}
  return{x,y,w,h};
}

export class GPTBustPlate{
  constructor(img){this.img=img;this.source=SOURCE.name;this.width=img.width;this.height=img.height;this.tintCache=new Map();}
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
