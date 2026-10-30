#!/usr/bin/env python3
"""Census structurally distinct high-quality AES S-box circuit seeds.

Seed choice is a first-class search variable.  This script parses public NIST
NCFF SLP circuits, Few Shots certificates, and Jain/gf2m-circuits numeric JSON,
independently verifies all 256 AES inputs, and compares both exact intermediate
functions and nonlinear dependency skeletons.

Exact-function overlap is deliberately not treated as an equivalence test: a
semilinear coordinate change can destroy exact overlap while preserving a broad
architecture.  The recursive AND-dependency fingerprint therefore complements
truth-table overlap and helps distinguish genuinely different nonlinear DAGs.
"""
import argparse, collections, hashlib, json, pathlib, re, urllib.request

MASK=(1<<256)-1
OPS=("AND","XOR","XNOR")

DEFAULTS={
  "nist-a32-g103":"https://raw.githubusercontent.com/usnistgov/Circuits/master/data/slp/aes/aes-sbox/aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt",
  "nist-a32-g104":"https://raw.githubusercontent.com/usnistgov/Circuits/master/data/slp/aes/aes-sbox/aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt",
  "nist-a32-g105":"https://raw.githubusercontent.com/usnistgov/Circuits/master/data/slp/aes/aes-sbox/aes-sbox-a32-ad5-g105-gd26-xx73-5.circ.txt",
  "nist-a33-g105":"https://raw.githubusercontent.com/usnistgov/Circuits/master/data/slp/aes/aes-sbox/aes-sbox-a33-ad4-g105-gd25-xx72-6.circ.txt",
  "nist-a28-g124":"https://raw.githubusercontent.com/usnistgov/Circuits/master/data/slp/aes/aes-sbox/aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt",
  "jain-106-d24":"https://raw.githubusercontent.com/ahrazzle/gf2m-circuits/main/sbox/circuits/sbox106_d24.json",
  "jain-106-d34":"https://raw.githubusercontent.com/ahrazzle/gf2m-circuits/main/sbox/circuits/sbox106_d34.json",
  "fs-101":"https://raw.githubusercontent.com/few-shots/few-shots/main/problems/p008-aes-sbox-circuit/shots/chunfeng11221/aes101-nist-interface-resub/certificate.json",
  "fs-102":"https://raw.githubusercontent.com/few-shots/few-shots/main/problems/p008-aes-sbox-circuit/shots/huangxin-design/aes102-field-plane-offsets/certificate.json",
  "fs-103":"https://raw.githubusercontent.com/few-shots/few-shots/main/problems/p008-aes-sbox-circuit/shots/fancify/aes103-joint-plane-orientations/certificate.json",
}

def get(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read().decode()

def aes_sbox(x):
    def mul(a,b):
        r=0
        for _ in range(8):
            if b&1:r^=a
            hi=a&0x80; a=(a<<1)&255
            if hi:a^=0x1b
            b>>=1
        return r
    if x==0: inv=0
    else:
        inv=1; base=x; e=254
        while e:
            if e&1:inv=mul(inv,base)
            base=mul(base,base); e>>=1
    y=0
    for i in range(8):
        bit=((inv>>i)&1)^((inv>>((i+4)&7))&1)^((inv>>((i+5)&7))&1)^((inv>>((i+6)&7))&1)^((inv>>((i+7)&7))&1)^((0x63>>i)&1)
        y|=bit<<i
    return y

def input_tables(reverse=False):
    d={}
    for i in range(8):
        bit=7-i if reverse else i
        v=0
        for x in range(256):
            if (x>>bit)&1:v|=1<<x
        d[f"x{i}"]=v
    return d

def op_eval(op,a,b):
    if op=="AND":return a&b
    if op=="XOR":return a^b
    if op=="XNOR":return (~(a^b))&MASK
    raise ValueError(op)

def expand_wire_range(spec):
    left,right=spec.strip().split(":")
    ml=re.fullmatch(r"(.*?)(\d+)",left); mr=re.fullmatch(r"(.*?)(\d+)",right)
    if not ml or not mr or ml.group(1)!=mr.group(1): raise ValueError(spec)
    p=ml.group(1); a=int(ml.group(2)); b=int(mr.group(2))
    step=1 if b>=a else -1
    return [f"{p}{i}" for i in range(a,b+step,step)]

def parse_nist(text):
    in_slp=False; gates=[]; outputs=[]; inputs=[]
    for raw in text.splitlines():
        s=raw.strip()
        if s.startswith("Inputs:"):
            inputs=expand_wire_range(s.split(":",1)[1].strip())
        if s.startswith("Outputs:"):
            outputs=expand_wire_range(s.split(":",1)[1].strip())
        if s=="begin SLP":in_slp=True; continue
        if s=="end SLP":break
        if not in_slp or not s or s.startswith("%"):continue
        p=s.split()
        if len(p)==4 and p[0] in OPS:
            gates.append({"op":p[0],"out":p[1],"a":p[2],"b":p[3]})
    if not gates or len(inputs)!=8 or len(outputs)!=8:raise ValueError("failed to parse NIST SLP")
    # Normalize arbitrary NCFF primary-input names (x0..x7, U0..U7, etc.)
    # to the internal x0..x7 convention before determining bit direction.
    imap={w:f"x{i}" for i,w in enumerate(inputs)}
    for g in gates:
        g["a"]=imap.get(g["a"],g["a"]); g["b"]=imap.get(g["b"],g["b"])
    return {"gates":gates,"outputs":outputs}

def parse_numeric_json(raw):
    def w(i): return f"x{i}" if i<8 else f"n{i}"
    gates=[]
    for k,g in enumerate(raw["gates"]):
        if len(g)!=3 or g[0] not in OPS:raise ValueError(g)
        op,a,b=g
        gates.append({"op":op,"a":w(a),"b":w(b),"out":w(8+k)})
    return {"gates":gates,"outputs":[w(o) for o in raw["outputs"]]}

def eval_circuit(c, reverse_inputs=False):
    vals=input_tables(reverse_inputs)
    depth={k:0 for k in vals}; and_depth={k:0 for k in vals}; and_anc={k:frozenset() for k in vals}
    and_idx=0; and_nodes=[]
    for g in c["gates"]:
        vals[g["out"]]=op_eval(g["op"],vals[g["a"]],vals[g["b"]])
        depth[g["out"]]=1+max(depth[g["a"]],depth[g["b"]])
        ad=max(and_depth[g["a"]],and_depth[g["b"]])+(1 if g["op"]=="AND" else 0)
        and_depth[g["out"]]=ad
        anc=set(and_anc[g["a"]])|set(and_anc[g["b"]])
        if g["op"]=="AND":
            anc.add(and_idx); and_nodes.append((g["out"],and_idx,ad,len(and_anc[g["a"]]),len(and_anc[g["b"]]))); and_idx+=1
        and_anc[g["out"]]=frozenset(anc)
    return vals,depth,and_depth,and_anc,and_nodes

def identify_mapping(c):
    for rin in (False,True):
        vals,*_=eval_circuit(c,rin)
        for rout in (False,True):
            outs=list(c["outputs"])
            if rout:outs=list(reversed(outs))
            ok=True
            for x in range(256):
                y=sum(((vals[w]>>x)&1)<<i for i,w in enumerate(outs))
                if y!=aes_sbox(x):ok=False;break
            if ok:return rin,rout
    raise AssertionError("circuit did not match AES under natural bit orders")

def normalize_mapping(c):
    rin,rout=identify_mapping(c)
    mp={f"x{i}":f"x{7-i}" if rin else f"x{i}" for i in range(8)}
    gates=[]
    for g in c["gates"]:
        gates.append({"op":g["op"],"a":mp.get(g["a"],g["a"]),"b":mp.get(g["b"],g["b"]),"out":g["out"]})
    outs=list(c["outputs"])
    if rout:outs.reverse()
    return {"gates":gates,"outputs":outs},{"reverse_inputs":rin,"reverse_outputs":rout}

identify_nist_mapping=identify_mapping
normalize_nist=normalize_mapping

def recursive_and_shape(c):
    anc={f"x{i}":frozenset() for i in range(8)}
    colors=[]
    for g in c["gates"]:
        au=set(anc[g["a"]]); av=set(anc[g["b"]])
        merged=au|av
        if g["op"]=="AND":
            def side(ids): return sorted(colors[j] for j in ids)
            sides=sorted([side(au),side(av)],key=lambda z:json.dumps(z,separators=(",",":")))
            color=hashlib.sha256(json.dumps(sides,separators=(",",":")).encode()).hexdigest()[:24]
            idx=len(colors); colors.append(color); merged.add(idx)
        anc[g["out"]]=frozenset(merged)
    out_sigs=[sorted(colors[j] for j in anc[o]) for o in c["outputs"]]
    payload={"and_colors":sorted(colors),"outputs":sorted(out_sigs,key=lambda z:json.dumps(z,separators=(",",":")))}
    return hashlib.sha256(json.dumps(payload,separators=(",",":"),sort_keys=True).encode()).hexdigest()

def load(name,url):
    text=get(url)
    if text.lstrip().startswith("{"):
        raw=json.loads(text)
        if raw.get("gates") and isinstance(raw["gates"][0],list):
            c,m=normalize_mapping(parse_numeric_json(raw)); mapping={"format":"numeric-json",**m}
        else:
            c=raw; mapping={"format":"few-shots-json"}
    else:
        c,m=normalize_mapping(parse_nist(text)); mapping={"format":"nist-ncff",**m}
    vals,depth,ad,anc,and_nodes=eval_circuit(c,False)
    for x in range(256):
        y=sum(((vals[w]>>x)&1)<<i for i,w in enumerate(c["outputs"]))
        assert y==aes_sbox(x),(name,x,y,aes_sbox(x))
    ops=collections.Counter(g["op"] for g in c["gates"])
    wire_functions={vals[g["out"]] for g in c["gates"]}
    and_functions={vals[g["out"]] for g in c["gates"] if g["op"]=="AND"}
    adprof=collections.Counter(ad[g["out"]] for g in c["gates"] if g["op"]=="AND")
    shape=sorted((ad[g["out"]],len(anc[g["a"]]),len(anc[g["b"]])) for g in c["gates"] if g["op"]=="AND")
    shape_hash=hashlib.sha256(json.dumps(shape,separators=(",",":")).encode()).hexdigest()
    return {
      "name":name,"url":url,"circuit":c,"vals":vals,
      "wire_functions":wire_functions,"and_functions":and_functions,
      "summary":{"gates":len(c["gates"]),"ops":dict(ops),"gate_depth":max(depth[o] for o in c["outputs"]),
                 "and_depth":max(ad[o] for o in c["outputs"]),"and_depth_profile":dict(sorted(adprof.items())),
                 "and_shape_hash":shape_hash,"recursive_and_shape_hash":recursive_and_shape(c),
                 "mapping":mapping,"verified_all_256":True}
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",default="seed-family-census.json")
    args=ap.parse_args()
    seeds=[load(n,u) for n,u in DEFAULTS.items()]
    out={"seeds":{s["name"]:s["summary"] for s in seeds},"pairs":{}}
    for i,a in enumerate(seeds):
        for b in seeds[i+1:]:
            wa,wb=a["wire_functions"],b["wire_functions"]; aa,ab=a["and_functions"],b["and_functions"]
            key=f"{a['name']}__{b['name']}"
            out["pairs"][key]={
              "shared_wire_functions":len(wa&wb),"wire_union":len(wa|wb),
              "shared_and_functions":len(aa&ab),"and_union":len(aa|ab),
              "and_jaccard":round(len(aa&ab)/len(aa|ab),6),
              "same_and_shape_hash":a["summary"]["and_shape_hash"]==b["summary"]["and_shape_hash"],
              "same_recursive_and_shape_hash":a["summary"]["recursive_and_shape_hash"]==b["summary"]["recursive_and_shape_hash"]}
    pathlib.Path(args.out).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,indent=2,sort_keys=True))

if __name__=="__main__":main()
