export const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
export const lerp=(a,b,t)=>a+(b-a)*t;
export const prog=(t,a,b)=>clamp((t-a)/(b-a));
export const smooth=t=>{t=clamp(t);return t*t*(3-2*t)};
export const easeOut=t=>1-(1-clamp(t))**3;
export const easeInOut=t=>{t=clamp(t);return t<.5?4*t*t*t:1-((-2*t+2)**3)/2};
export const back=t=>{t=clamp(t);const c=1.70158;return 1+(c+1)*(t-1)**3+c*(t-1)**2};
export const pulse=(t,w=.18)=>Math.exp(-Math.max(0,t)*Math.max(0,t)/(w*w));
export const beat=(t,bpm=116,offset=.28)=>Math.max(0,(t-offset)*bpm/60);
export const beatPulse=(t,bpm=116,offset=.28)=>{
  const b=beat(t,bpm,offset), f=b-Math.floor(b);
  return Math.exp(-f*8);
};
