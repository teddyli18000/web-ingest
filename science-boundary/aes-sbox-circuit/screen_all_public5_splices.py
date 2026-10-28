#!/usr/bin/env python3
"""Screen all known public 32-AND AES cores against the live 102-gate prefix."""
import json, urllib.request
import analyze_public5_cores as A

ROOT='https://raw.githubusercontent.com/ahrazzle/gf2m-circuits/main/'
FILES=[
    'sbox/circuits/sbox106_d34.json',
    'sbox/circuits/sbox110_d38.json',
    'sbox/circuits/invsbox109_d30.json',
    'sbox/circuits/invsbox109_d31.json',
    'sbox/prior/aes-sbox-a32-ad5-g110-gd22-xx78-3.json',
    'sbox/prior/SLP_AES_113.json',
    'sbox/prior/aes-invsbox-a32-ad5-g112-gd26-xx80-9.json',
]

def fetch(path):
    with urllib.request.urlopen(ROOT+path,timeout=30) as r:
        return json.load(r)

A.fetch=fetch
A.FILES=FILES

import screen_public5_splices as S

if __name__=='__main__':
    S.main()
