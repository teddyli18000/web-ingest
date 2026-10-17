import {PALETTE as P} from './palette.js';

export class Draw{
  constructor(g,w=1920,h=1080){this.g=g;this.w=w;this.h=h;this.font='Inter,Arial,sans-serif';}
  save(fn){this.g.save();try{fn();}finally{this.g.restore();}}
  alpha(a,fn){this.save(()=>{this.g.globalAlpha=a;fn();});}
  rect(x,y,w,h,{fill=P.ink,stroke=null,width=1,alpha=1}={}){
    this.save(()=>{this.g.globalAlpha=alpha;if(fill){this.g.fillStyle=fill;this.g.fillRect(x,y,w,h)}if(stroke){this.g.strokeStyle=stroke;this.g.lineWidth=width;this.g.strokeRect(x,y,w,h)}})
  }
  rrect(x,y,w,h,r,{fill=P.white,stroke=null,width=1,alpha=1,shadow=0}={}){
    const g=this.g;this.save(()=>{g.globalAlpha=alpha;if(shadow){g.shadowColor=`rgba(18,28,44,${.15*shadow})`;g.shadowBlur=28*shadow;g.shadowOffsetY=12*shadow}g.beginPath();g.roundRect(x,y,w,h,r);if(fill){g.fillStyle=fill;g.fill()}if(stroke){g.strokeStyle=stroke;g.lineWidth=width;g.stroke()}})
  }
  line(x1,y1,x2,y2,{color=P.ink,width=2,alpha=1,dash=[]}={}){
    const g=this.g;this.save(()=>{g.globalAlpha=alpha;g.strokeStyle=color;g.lineWidth=width;g.setLineDash(dash);g.beginPath();g.moveTo(x1,y1);g.lineTo(x2,y2);g.stroke()})
  }
  circle(x,y,r,{fill=P.ink,stroke=null,width=1,alpha=1}={}){
    const g=this.g;this.save(()=>{g.globalAlpha=alpha;g.beginPath();g.arc(x,y,r,0,Math.PI*2);if(fill){g.fillStyle=fill;g.fill()}if(stroke){g.strokeStyle=stroke;g.lineWidth=width;g.stroke()}})
  }
  path(path,{fill=P.ink,stroke=null,width=1,alpha=1,rule='nonzero'}={}){
    const g=this.g;this.save(()=>{g.globalAlpha=alpha;if(fill){g.fillStyle=fill;g.fill(path,rule)}if(stroke){g.strokeStyle=stroke;g.lineWidth=width;g.stroke(path)}})
  }
  text(text,x,y,{size=36,color=P.ink,alpha=1,weight=400,font='sans',align='left',baseline='alphabetic',italic=false}={}){
    const g=this.g;this.save(()=>{g.globalAlpha=alpha;g.fillStyle=color;g.textAlign=align;g.textBaseline=baseline;g.font=`${italic?'italic ':''}${weight} ${size}px ${font==='serif'?'Georgia,serif':font==='mono'?'ui-monospace,SFMono-Regular,Menlo,monospace':this.font}`;g.fillText(text,x,y)})
  }
  measure(text,{size=36,weight=400,font='sans'}={}){const g=this.g;g.save();g.font=`${weight} ${size}px ${font==='serif'?'Georgia,serif':font==='mono'?'ui-monospace,SFMono-Regular,Menlo,monospace':this.font}`;const w=g.measureText(text).width;g.restore();return w}
  glow(x,y,r,color=P.cobalt,alpha=.25){
    const g=this.g;this.save(()=>{const gr=g.createRadialGradient(x,y,0,x,y,r);gr.addColorStop(0,this.rgba(color,alpha));gr.addColorStop(.45,this.rgba(color,alpha*.45));gr.addColorStop(1,this.rgba(color,0));g.fillStyle=gr;g.fillRect(x-r,y-r,r*2,r*2)})
  }
  gradRect(x,y,w,h,stops,vertical=false){const g=this.g;this.save(()=>{const gr=vertical?g.createLinearGradient(x,y,x,y+h):g.createLinearGradient(x,y,x+w,y);for(const [p,c] of stops)gr.addColorStop(p,c);g.fillStyle=gr;g.fillRect(x,y,w,h)})}
  paper(t=0){
    const g=this.g;g.fillStyle=P.paper;g.fillRect(0,0,this.w,this.h);
    const gr=g.createRadialGradient(this.w*.68,this.h*.30,30,this.w*.68,this.h*.30,this.w*.72);gr.addColorStop(0,'rgba(255,224,161,.24)');gr.addColorStop(.55,'rgba(126,165,245,.08)');gr.addColorStop(1,'rgba(244,239,229,0)');g.fillStyle=gr;g.fillRect(0,0,this.w,this.h);
    g.save();g.globalAlpha=.045;g.fillStyle=P.ink;for(let i=0;i<210;i++){const x=(i*137.3+t*7)%this.w,y=(i*83.7+t*4)%this.h;g.fillRect(x,y,1+(i%3===0),1)}g.restore();
  }
  clipRect(x,y,w,h,r,fn){const g=this.g;this.save(()=>{g.beginPath();g.roundRect(x,y,w,h,r);g.clip();fn()})}
  rgba(hex,a){const h=hex.replace('#','');if(h.length!==6)return hex;const n=parseInt(h,16);return `rgba(${n>>16},${(n>>8)&255},${n&255},${a})`}
}
