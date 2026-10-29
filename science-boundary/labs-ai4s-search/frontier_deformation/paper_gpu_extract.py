"""Extract and independently verify published 2025 GPU MTS LABS Table 2 records.
Source https://arxiv.org/html/2504.00987v2; table entries are hexadecimal with
ZERO bits padding appended at the END to nibble boundary. Zero is sign -1.
The paper treats negation/reversal as symmetries (fourfold); for this project's
more complete eightfold energy symmetry we additionally factor alternation.
"""
import json,pathlib
RECORDS=[
(92,490,"EE01C0E77667DD34DAE94B5"),(92,490,"BB5495B2233288618FBC1E0"),
(98,529,"993A76393CDB4BCF78FF00AA8"),
(104,600,"0F80F3C20AAB1844295B6ED666"),
(106,645,"696D27CA748C66071EAFDD1177C"),
(108,670,"F2401F3D9FF1CF46D58D96AA959"),
(110,707,"33F83762F128DF55064B5B7BE79"), # malformed in HTML/PDF text: only 108 bits
(112,728,"A0496A493FAECCC8AFC3D50E738F"),
(114,777,"B6C3648DB19C8C387A9EAA8578000"),
(116,802,"52DF72096B92DCC87407044C8E1D5"),
(118,807,"E003FB9F87C674E5CD6D34CCB2AD54"),
(120,824,"84AD68060864EE7989E1A6C0BA7551"),
(99,553,"0CF30C003783CBCC8DA92AAD4"),
(107,645,"E3C5CA9D21C2792DED3FC88AEEE"),
(109,658,"DA62534CFBB114B94A3EBE3BE1F8"),
(113,736,"5C3E8E2CC45A6DD1B794047295800"),
(119,787,"81F0200DDD2B8C4E654E18ACA9A69A"),
]
def energy(s):
 n=len(s);return sum(sum(1 if s[i]==s[i+k] else -1 for i in range(n-k))**2 for k in range(1,n))
def negate(s):return s.translate(str.maketrans("01","10"))
def alternate(s):return "".join(v if i%2==0 else ("1" if v=="0" else "0") for i,v in enumerate(s))
def orbit(s):return [v for b in (s,s[::-1]) for v in (b,negate(b),alternate(b),negate(alternate(b)))]
def skew(s):
 if len(s)%2==0:return False
 m=len(s)//2
 return all((s[m+j]==s[m-j]) if j%2==0 else (s[m+j]!=s[m-j]) for j in range(1,m+1))
def near(s):return skew(s) if len(s)%2 else skew(s[:-1]) or skew(s[1:])
def run():
 seen={};skipped=[];valid=[]
 for n,e,h in RECORDS:
  bits="".join(f"{int(v,16):04b}" for v in h)
  if len(bits)<n or "1" in bits[n:] or energy(bits[:n])!=e:
   skipped.append(dict(n=n,expected=e,hex=h,length=len(bits),truncated_energy=energy(bits[:n])))
   continue
  bits=bits[:n];c=min(orbit(bits))
  r=dict(n=n,energy=e,bits=bits,provenance="published_GPU_MTS_v2",parent="arxiv_2504.00987v2",
         seed=0,near_skew=int(near(bits)),canonical=c,hex=h)
  valid.append(r)
  seen.setdefault((n,c),r)
 assert len(valid)==16 and len(seen)==15
 assert len(skipped)==1 and skipped[0]["n"]==110
 assert int(RECORDS[0][2],16)^int(RECORDS[1][2],16)==int("5"*23,16)
 p=pathlib.Path(__file__).resolve().parent/"results";p.mkdir(exist_ok=True)
 cols=("n","energy","bits","provenance","parent","seed","near_skew","canonical")
 with (p/"2026-10-29-paper-gpu-elite.tsv").open("w") as f:
  f.write("\t".join(cols)+"\n")
  for r in sorted(seen.values(),key=lambda x:(x["n"],x["energy"])):
   f.write("\t".join(str(r[c]) for c in cols)+"\n")
 (p/"2026-10-29-paper-gpu-elite-audit.json").write_text(json.dumps(dict(
  source="https://arxiv.org/html/2504.00987v2",
  entries_in_paper=len(RECORDS),verified=len(valid),different_8fold_orbits=len(seen),
  malformed=skipped,n92_equivalence="EE01... XOR BB54... = 0x55555555555555555555555; alternate-sign symmetry",
  published_records=[{k:v for k,v in r.items() if k!="bits"} for r in valid]),indent=2)+"\n")
 print("PASS:16 decoded, 15 symmetry-distinct, 1 malformed N110 excluded, 0 score errors")
if __name__=="__main__":run()
