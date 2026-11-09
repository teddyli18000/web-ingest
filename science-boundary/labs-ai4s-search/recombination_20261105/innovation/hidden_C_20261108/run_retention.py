#!/usr/bin/env python3
"""Two genuinely costed same-X branch policies, followed by separate C-only verifier.

N50 is already exposed, so these are posthoc mechanistic experiments only.
"""
import argparse,gzip,hashlib,json,os,pathlib,shutil,subprocess,sys
def digest(p):
    h=hashlib.sha256()
    with pathlib.Path(p).open('rb') as f:
        for z in iter(lambda:f.read(1<<20),b''):h.update(z)
    return h.hexdigest()
def call(args,**kw):subprocess.run(args,check=True,**kw)
def main():
    p=argparse.ArgumentParser();p.add_argument('--exe',required=True)
    p.add_argument('--output',default='results/branch_deploy_v1')
    p.add_argument('--budget-ms',type=int,default=150)
    a=p.parse_args();dest=pathlib.Path(a.output)
    src=pathlib.Path('results/test50_forced_v1')
    mdl=pathlib.Path('results/forced_models_v1/frozen_models.tsv')
    frozen=json.loads(pathlib.Path('results/forced_models_v1/training_audit.json').read_text())
    expected='2abb727677b9c065b624322f1446fc950987d2c64fc41396e4b90e80c5ad576b'
    assert frozen['model_sha256']==expected and digest(mdl)==expected
    assert not dest.exists(),'Do not overwrite prior scientific trial'
    assert json.loads((src/'verdict.json').read_text())['run_rows']==864
    for mode,flag in [('control','0'),('retained_X','1')]:
        d=dest/mode;d.mkdir(parents=True)
        env=os.environ.copy();env['LABS_FORCE_NONZERO']='1';env['LABS_RETAIN_ORIGINAL_X']=flag
        # This search executable has no CLI argument or file descriptor for C.
        call([str(pathlib.Path(a.exe).resolve()),'deploy',str(src/'scenario-input.tsv'),
            str(mdl),str(d/'events.tsv'),str(d/'sessions.tsv'),str(a.budget_ms)],env=env)
        print('BLIND SEARCH COMPLETE',mode,flush=True)
    # Only NOW can separate independent scorer read target C vault.
    for mode in ('control','retained_X'):
        d=dest/mode
        call([sys.executable,'verify_hidden.py','deploy',
            '--input',str(src/'scenario-input.tsv'),
            '--vault',str(src/'target-vault.tsv'),
            '--events',str(d/'events.tsv'),'--sessions',str(d/'sessions.tsv'),
            '--output',str(d)])
        report=json.loads((d/'verdict.json').read_text())
        assert report['states']==144 and report['run_rows']==864 and report['n']==[50]
        raw=d/'events.tsv';archive=d/'events.tsv.gz'
        assert digest(raw)==report['hashes']['events']
        with raw.open('rb') as srcf,archive.open('wb') as dst:
            with gzip.GzipFile(filename='',fileobj=dst,mode='wb',compresslevel=6,mtime=0) as g:
                shutil.copyfileobj(srcf,g,1<<20)
        assert archive.stat().st_size<90*(1<<20)
        h=hashlib.sha256()
        with gzip.open(archive,'rb') as f:
            for z in iter(lambda:f.read(1<<20),b''):h.update(z)
        assert h.hexdigest()==report['hashes']['events']
        (d/'archive_provenance.json').write_text(json.dumps({
            'exact_uncompressed_sha256':h.hexdigest(),
            'compressed_sha256':digest(archive),'events':report['events'],
            'original_bytes':raw.stat().st_size,
            'compressed_bytes':archive.stat().st_size},indent=2)+'\n')
        raw.unlink()
    call([sys.executable,'analyze_branch_deploy.py',
        '--input',str(src/'scenario-input.tsv'),
        '--vault',str(src/'target-vault.tsv'),
        '--control',str(dest/'control'),
        '--retained',str(dest/'retained_X'),'--out',str(dest)])
    r=json.loads((dest/'retention_search_verdict.json').read_text())
    assert r['states']==144 and r['paired_arm_runs']==864
    assert all(z['cases']==72 and z['source_C_orbit_groups']==3 and
               z['control_wall_ms']>=a.budget_ms and z['retained_wall_ms']>=a.budget_ms
               for m in ('AB_blind','C_shell') for z in r['outcomes'][m].values())
    (dest/'protocol.json').write_text(json.dumps({
       'original_frozen_model_sha256':expected,
       'already_exposed_N50_orbit_population':True,
       'two_branch_only_difference':'retain original X as alternate proposal anchor every odd iteration',
       'tested_modes':['control','retained_X'],'all_costed_wall_budget_ms':a.budget_ms,
       'C_never_given_to_search_binary':True,
       'posthoc_vault_only_for_external_independent_verifier':True,
       'paired_scenarios':144,'paired_arm_treatments':864,
    },indent=2)+'\n')
    print('PASS EXACT FULL SEARCH + REPRODUCIBLE RETENTION CAUSAL AUDIT',flush=True)
if __name__=='__main__':main()
