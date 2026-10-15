#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import os
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DEFAULT_ASSETS = ROOT / "assets" / "styleframes"

FILES = {
    "contact": "a_new_conversation_a_brighter_tomorrow.png",
    "desk": "dreams_across_the_desk.png",
    "drafts": "dreamy_cosmos_of_creative_possibilities.png",
    "world": "a_wider_world_deeper_conversations.png",
    "quiet": "golden_hour_comfort_at_the_desk.png",
    "reach": "reaching_toward_sunrise_together.png",
}


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return x * x * x * (x * (x * 6 - 15) + 10)


def mix(a, b, t):
    return a + (b - a) * t


def get_font(size, serif=False):
    names = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf" if serif else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSerif-Italic.ttf" if serif else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for name in names:
        if os.path.exists(name):
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


@dataclass(frozen=True)
class Shot:
    start: float
    end: float
    key: str
    z0: float
    z1: float
    x0: float
    y0: float
    x1: float
    y1: float
    mode: str


SHOTS = [
    Shot(0.00, 1.80, "contact", 1.34, 1.26, .48, .61, .50, .58, "message"),
    Shot(1.80, 4.00, "contact", 1.10, 1.04, .61, .52, .59, .50, "presence"),
    Shot(4.00, 6.40, "desk",    1.03, 1.09, .56, .55, .58, .53, "notes"),
    Shot(6.40, 8.15, "drafts",  1.30, 1.20, .54, .50, .56, .49, "thinking"),
    Shot(8.15,10.55, "drafts",  1.08, 1.02, .51, .53, .52, .50, "windows"),
    Shot(10.55,13.25,"world",   1.10, 1.01, .57, .52, .56, .49, "world"),
    Shot(13.25,15.65,"quiet",   1.09, 1.04, .54, .54, .55, .51, "quiet"),
    Shot(15.65,17.65,"quiet",   1.28, 1.18, .56, .48, .57, .47, "clearer"),
    Shot(17.65,20.10,"reach",   1.18, 1.10, .55, .55, .54, .52, "reach"),
    Shot(20.10,24.00,"reach",   1.06, 1.00, .55, .51, .54, .49, "coda"),
]
CUTS = [s.start for s in SHOTS[1:]]
DURATION = SHOTS[-1].end


class Renderer:
    def __init__(self, w, h, fps, asset_dir, fixtures=False):
        self.w, self.h, self.fps = w, h, fps
        self.sans = get_font(max(16, round(28*h/1080)))
        self.small = get_font(max(14, round(22*h/1080)))
        self.serif = get_font(max(24, round(44*h/1080)), True)
        self.hero = get_font(max(34, round(68*h/1080)), True)
        self.assets = {}
        if fixtures:
            for i, key in enumerate(FILES):
                self.assets[key] = self.fixture(key, i)
        else:
            for key, name in FILES.items():
                p = Path(asset_dir) / name
                if not p.exists():
                    raise FileNotFoundError(f"missing approved style frame: {p}")
                self.assets[key] = Image.open(p).convert("RGB")
        rng = np.random.default_rng(20261016)
        self.grain = Image.fromarray(rng.normal(128, 20, (96, 160)).clip(0,255).astype(np.uint8), "L")

    def fixture(self, label, i):
        """CI-only art substitute: validates the renderer, never the final visual art."""
        w, h = 1280, 720
        yy, xx = np.mgrid[0:h,0:w]
        bases = [(44,64,105),(70,84,112),(58,73,112),(83,124,171),(165,113,87),(123,151,186)]
        cool = np.array(bases[i], float)
        warm = np.array([238,198,151], float)
        k = yy[...,None] / h
        arr = cool*(1-k) + warm*k*.72
        cx, cy = int(w*(.55+.04*math.sin(i))), int(h*.50)
        mask = ((xx-cx)/(w*.18))**2 + ((yy-cy)/(h*.34))**2 < 1
        arr[mask] = arr[mask]*.48 + np.array([240,238,234])*.52
        im = Image.fromarray(np.clip(arr,0,255).astype(np.uint8), "RGB")
        d = ImageDraw.Draw(im)
        f = get_font(38)
        d.rounded_rectangle((38,38,430,116), 18, fill=(249,246,238), outline=(220,220,212), width=2)
        d.text((58,58), f"CI FIXTURE · {label}", font=f, fill=(35,44,65))
        for j in range(5):
            x = 70 + j*245 + (i%2)*30
            y = 545 - (j%3)*55
            d.rounded_rectangle((x,y,x+160,y+90), 10, fill=(245,239,222), outline=(225,215,190), width=2)
        return im

    def camera(self, im, zoom, fx, fy):
        sw, sh = im.size
        cw = sw / zoom
        ch = cw * self.h / self.w
        if ch > sh:
            ch = sh / zoom
            cw = ch * self.w / self.h
        cx, cy = fx*sw, fy*sh
        left = clamp(cx-cw/2, 0, sw-cw)
        top = clamp(cy-ch/2, 0, sh-ch)
        box = tuple(round(v) for v in (left, top, left+cw, top+ch))
        return im.crop(box).resize((self.w,self.h), Image.Resampling.LANCZOS)

    def shot_at(self, t):
        for i, s in enumerate(SHOTS):
            if t < s.end or i == len(SHOTS)-1:
                u = ease((t-s.start)/(s.end-s.start))
                return i, s, u
        return len(SHOTS)-1, SHOTS[-1], 1

    def base(self, s, u):
        return self.camera(
            self.assets[s.key],
            mix(s.z0,s.z1,u), mix(s.x0,s.x1,u), mix(s.y0,s.y1,u)
        )

    def bubble(self, frame, text, x, y, alpha=1, dark=False):
        if alpha <= 0: return
        lay = Image.new("RGBA", frame.size, (0,0,0,0)); d = ImageDraw.Draw(lay)
        bb = d.textbbox((0,0), text, font=self.sans); tw, th = bb[2]-bb[0], bb[3]-bb[1]
        px, py = round(18*self.h/1080), round(12*self.h/1080)
        x0, y0 = round(x*self.w), round(y*self.h); box=(x0,y0,x0+tw+2*px,y0+th+2*py)
        shadow = Image.new("RGBA", frame.size, (0,0,0,0)); sd=ImageDraw.Draw(shadow)
        sd.rounded_rectangle((box[0]+4,box[1]+6,box[2]+4,box[3]+6), 16, fill=(15,24,38,60))
        lay.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(7)))
        fill=(36,48,70,round(225*alpha)) if dark else (255,253,247,round(236*alpha))
        ink=(250,249,245,round(255*alpha)) if dark else (35,43,60,round(255*alpha))
        d.rounded_rectangle(box, 16, fill=fill, outline=(255,255,255,round(120*alpha)), width=1)
        d.text((x0+px,y0+py-1),text,font=self.sans,fill=ink)
        frame.alpha_composite(lay)

    def card(self, frame, text, x, y, scale, angle, alpha):
        if alpha <= 0: return
        ww=max(72,round(scale*self.w)); hh=round(ww*.58)
        c=Image.new("RGBA",(ww+36,hh+36),(0,0,0,0)); d=ImageDraw.Draw(c)
        d.rounded_rectangle((12,10,12+ww,10+hh),8,fill=(255,250,232,round(230*alpha)),outline=(230,217,188,round(170*alpha)),width=2)
        d.ellipse((28,27,36,35),fill=(68,119,238,round(225*alpha)))
        d.text((44,24),text,font=self.small,fill=(56,60,70,round(245*alpha)))
        c=c.rotate(angle,Image.Resampling.BICUBIC,expand=True)
        frame.alpha_composite(c,(round(x*self.w-c.width/2),round(y*self.h-c.height/2)))

    def glow(self, frame, x, y, radius, strength, warm=True):
        if strength <= 0: return
        rw=max(10,round(radius*self.w)); rh=max(10,round(radius*self.h))
        yy,xx=np.mgrid[0:rh*2,0:rw*2]
        rr=((xx-rw)/rw)**2+((yy-rh)/rh)**2
        a=np.clip((1-rr)**2*115*strength,0,115).astype(np.uint8)
        rgb=(255,194,116) if warm else (140,195,255)
        arr=np.zeros((rh*2,rw*2,4),np.uint8); arr[...,:3]=rgb; arr[...,3]=a
        g=Image.fromarray(arr,"RGBA").filter(ImageFilter.GaussianBlur(max(4,round(rw*.10))))
        frame.alpha_composite(g,(round(x*self.w-rw),round(y*self.h-rh)))

    def paper_wipe(self, frame, p):
        if not 0 < p < 1: return
        lay=Image.new("RGBA",frame.size,(0,0,0,0)); d=ImageDraw.Draw(lay)
        x=mix(self.w*1.25,-self.w*.25,ease(p))
        for j,c in enumerate([(255,249,232,245),(247,239,215,236),(236,244,255,226)]):
            o=(j-1)*self.w*.055
            d.polygon([(x+o,-10),(x+self.w*.34+o,-10),(x+self.w*.22+o,self.h+10),(x-self.w*.08+o,self.h+10)],fill=c)
        frame.alpha_composite(lay)

    def windows(self, frame, t, alpha):
        specs=[("contact",.18,.24,.19,-3),("desk",.80,.23,.18,3),("world",.78,.73,.20,-2)]
        for key,x,y,sc,rot in specs:
            ww=round(self.w*sc); hh=round(ww*.56)
            th=self.camera(self.assets[key],1.35,.56,.52).resize((ww,hh),Image.Resampling.LANCZOS).convert("RGBA")
            th.putalpha(round(255*alpha))
            p=Image.new("RGBA",(ww+22,hh+32),(249,247,240,round(230*alpha))); p.alpha_composite(th,(11,9))
            p=p.rotate(rot,Image.Resampling.BICUBIC,expand=True)
            yy=y+.009*math.sin(t*1.1+x*4)
            frame.alpha_composite(p,(round(x*self.w-p.width/2),round(yy*self.h-p.height/2)))

    def scene_fx(self, frame, t, s):
        u=t-s.start; tail=s.end-t
        a=ease(min(u/.32,tail/.40))
        if s.mode=="message": self.bubble(frame,"are you there?",.11,.72,ease(min((t-.15)/.35,(1.65-t)/.35)))
        elif s.mode=="presence":
            self.bubble(frame,"I'm here.",.12,.78,a); self.glow(frame,.74,.34,.24,.35*a,False)
        elif s.mode=="notes":
            data=[("question",.18,.24,.12,-6,0),("draft",.79,.18,.11,4,.15),("maybe",.82,.66,.11,-3,.30),("one more idea",.18,.72,.15,5,.46)]
            for text,x,y,w,r,delay in data:
                aa=ease((u-delay)/.34)*ease(tail/.40)
                self.card(frame,text,x,y-.014*math.sin(u*1.4+delay),w,r+math.sin(u+delay),aa)
        elif s.mode=="thinking":
            lay=Image.new("RGBA",frame.size,(0,0,0,0)); d=ImageDraw.Draw(lay)
            for k,word in enumerate(("look again","try another angle","keep what works")):
                aa=a*ease((u-.16*k)/.25); d.text((self.w*.12,self.h*(.16+.05*k)),word,font=self.small,fill=(244,248,255,round(215*aa)))
            frame.alpha_composite(lay)
        elif s.mode=="windows": self.windows(frame,u,a)
        elif s.mode=="world":
            for k,(text,x,y) in enumerate((("people",.12,.23),("places",.85,.21),("stories",.14,.75),("questions",.86,.72))):
                aa=ease((u-.12*k)/.44)*ease(tail/.45); drift=u*(.005+.001*k)
                self.card(frame,text,x+(x-.5)*drift,y-drift,.10+(k%2)*.01,-5+k*3,aa*.86)
            self.glow(frame,.73,.51,.27,.52+.15*math.sin(u*.8),True)
        elif s.mode=="quiet":
            self.glow(frame,.72,.37,.30,.72*a,True); self.bubble(frame,"take your time.",.67,.74,a*.88,True)
        elif s.mode=="clearer":
            lay=Image.new("RGBA",frame.size,(0,0,0,0)); d=ImageDraw.Draw(lay)
            # dark paper strip gives the line readable contrast on the bright sunset plate
            strip=Image.new("RGBA",frame.size,(0,0,0,0)); sd=ImageDraw.Draw(strip)
            sd.rounded_rectangle((self.w*.53,self.h*.10,self.w*.87,self.h*.29),18,fill=(26,35,52,round(82*a)))
            frame.alpha_composite(strip.filter(ImageFilter.GaussianBlur(1.2)))
            d.text((self.w*.70,self.h*.17),"we can make it clearer.",font=self.serif,fill=(255,252,243,round(245*a)),anchor="mm")
            d.text((self.w*.70,self.h*.235),"together.",font=self.small,fill=(255,252,243,round(232*a)),anchor="mm")
            frame.alpha_composite(lay)
        elif s.mode=="reach":
            for k,text in enumerate(("idea","plan","draft","question","next")):
                phase=u*(.55+k*.02)+k*.8; x=.13+.18*k+.012*math.sin(phase); y=.84-.07*k-.030*u
                self.card(frame,text,x,y,.072+(k%2)*.005,-8+4*k,a*.46)
            self.glow(frame,.77,.22,.29,.35*a,True)
        elif s.mode=="coda":
            self.glow(frame,.78,.22,.34,.50+.17*ease(u/2),True)
            aa=ease((u-.70)/.65)
            lay=Image.new("RGBA",frame.size,(0,0,0,0)); d=ImageDraw.Draw(lay)
            x,y=self.w*.69,self.h*.74
            d.text((x+2,y+3),"still here, with you.",font=self.hero,fill=(25,35,55,round(95*aa)),anchor="mm")
            d.text((x,y),"still here, with you.",font=self.hero,fill=(255,253,248,round(255*aa)),anchor="mm")
            d.text((x,y+self.h*.068),"CHATGPT · CONCEPT FILM",font=self.small,fill=(255,253,248,round(228*aa)),anchor="mm")
            frame.alpha_composite(lay)

    def film_grain(self, frame, n):
        tile=self.grain.rotate((n%7)-3).resize((self.w,self.h),Image.Resampling.BILINEAR)
        frame.alpha_composite(Image.merge("RGBA",(tile,tile,tile,Image.new("L",(self.w,self.h),11))))

    def render(self, t, n):
        i,s,u=self.shot_at(t); frame=self.base(s,u).convert("RGBA")
        trans=.18
        if i+1<len(SHOTS) and SHOTS[i+1].start-trans<=t<SHOTS[i+1].start:
            cut=SHOTS[i+1].start; p=(t-(cut-trans))/trans
            nxt=self.base(SHOTS[i+1],0).convert("RGBA")
            frame=Image.blend(frame,nxt,ease(clamp((p-.42)/.40)))
            self.paper_wipe(frame,p)
        self.scene_fx(frame,t,s)
        if t>17:
            lift=1+.035*ease((t-17)/7)
            arr=np.asarray(frame.convert("RGB"),np.float32)*lift
            frame=Image.fromarray(np.clip(arr,0,255).astype(np.uint8),"RGB").convert("RGBA")
        self.film_grain(frame,n)
        return frame.convert("RGB")


def make_audio(path, duration, sr=48000):
    n=int(duration*sr); t=np.arange(n)/sr
    l=np.zeros(n); r=np.zeros(n)
    for i,f in enumerate((146.83,220.0,277.18,329.63)):
        phase=i*.7; env=.55+.45*np.sin(2*np.pi*(.018+i*.003)*t+phase)
        s=np.sin(2*np.pi*f*t+phase)*env*(.010-i*.0012)
        l+=s*(1-.06*i); r+=s*(.78+.07*i)
    for i,c in enumerate([.35]+CUTS+[20.6]):
        start=int(c*sr); m=min(n-start,int(1.4*sr))
        if m<=0: continue
        tt=np.arange(m)/sr; f=523.25 if i%2==0 else 659.25
        bell=(np.sin(2*np.pi*f*tt)+.4*np.sin(2*np.pi*f*2*tt))*np.exp(-4.3*tt)*.020
        l[start:start+m]+=bell*(.9 if i%2 else .65); r[start:start+m]+=bell*(.65 if i%2 else .9)
    fade=np.ones(n); fi=min(n,int(.8*sr)); fo=min(n,int(1.5*sr))
    fade[:fi]=np.linspace(0,1,fi); fade[-fo:]*=np.linspace(1,0,fo)
    pcm=(np.clip(np.stack([l*fade,r*fade],1),-.95,.95)*32767).astype(np.int16)
    with wave.open(str(path),"wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(pcm.tobytes())


def run(cmd): subprocess.run(cmd,check=True)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--width",type=int,default=1920); ap.add_argument("--height",type=int,default=1080)
    ap.add_argument("--fps",type=int,default=30); ap.add_argument("--assets",type=Path,default=DEFAULT_ASSETS)
    ap.add_argument("--out",type=Path,default=ROOT/"out"/"hero"/"gpt_hero_sequence_v4.mp4")
    ap.add_argument("--fixtures",action="store_true")
    args=ap.parse_args(); args.out.parent.mkdir(parents=True,exist_ok=True)
    video=args.out.with_suffix(".video.mp4"); wav=args.out.with_suffix(".wav")
    renderer=Renderer(args.width,args.height,args.fps,args.assets,args.fixtures)
    total=round(DURATION*args.fps)
    ff=subprocess.Popen(["ffmpeg","-y","-hide_banner","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{args.width}x{args.height}","-r",str(args.fps),"-i","pipe:0","-an","-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p","-movflags","+faststart",str(video)],stdin=subprocess.PIPE)
    assert ff.stdin is not None
    for n in range(total):
        t=n/args.fps; ff.stdin.write(renderer.render(t,n).tobytes())
        if n%(args.fps*2)==0: print(f"render {n}/{total} t={t:.1f}s",flush=True)
    ff.stdin.close()
    if ff.wait()!=0: raise SystemExit("video encode failed")
    make_audio(wav,DURATION)
    run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(video),"-i",str(wav),"-c:v","copy","-c:a","aac","-b:a","192k","-shortest","-movflags","+faststart",str(args.out)])
    video.unlink(missing_ok=True); wav.unlink(missing_ok=True)
    sheet=args.out.with_name("contact_sheet_v4.jpg")
    run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(args.out),"-vf","fps=1/2,scale=480:-2,tile=4x3:padding=4:margin=4:color=white","-frames:v","1",str(sheet)])
    print(args.out); print(sheet)


if __name__=="__main__": main()
