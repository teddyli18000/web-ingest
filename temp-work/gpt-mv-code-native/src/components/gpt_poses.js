const THINK={
  prefix:'think.b64.',
  chunks:6,
  sha:'2529a1ee41f43c9ae66fc31d3d52b364fca1630f5c0433d4a1ecc815ae794c6f',
  width:384,
  height:356,
  mime:'image/webp',
};

async function loadPayload(spec){
  const parts=await Promise.all(Array.from({length:spec.chunks},async(_,i)=>{
    const r=await fetch(`/assets/gpt/${spec.prefix}${i}`,{cache:'no-store'});
    if(!r.ok)throw new Error(`pose chunk ${i} HTTP ${r.status}`);
    return (await r.text()).trim();
  }));
  const b64=parts.join('');
  const raw=atob(b64),bytes=new Uint8Array(raw.length);
  for(let i=0;i<raw.length;i++)bytes[i]=raw.charCodeAt(i);
  const digest=await crypto.subtle.digest('SHA-256',bytes);
  const sha=[...new Uint8Array(digest)].map(b=>b.toString(16).padStart(2,'0')).join('');
  if(sha!==spec.sha)throw new Error(`pose payload sha mismatch: ${sha}`);
  return `data:${spec.mime};base64,${b64}`;
}

async function loadImage(spec){
  const img=new Image();
  img.src=await loadPayload(spec);
  await img.decode();
  if(img.naturalWidth!==spec.width||img.naturalHeight!==spec.height){
    throw new Error(`unexpected pose size ${img.naturalWidth}x${img.naturalHeight}`);
  }
  return img;
}

export async function loadGPTPoses(){
  return {think:await loadImage(THINK)};
}

export const GPT_POSE_SPECS={think:THINK};
