#!/usr/bin/env python3
"""Conservative classic repeated-X restarts: no target C until after all searches."""
import argparse,os,pathlib,subprocess,gzip,shutil,hashlib,json,sys
def sha(p):
    h=hashlib.sha256()
    with pathlib.Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def run(cmd,**kw):subprocess.run(cmd,check=True,**kw)
def main():
    p=argparse.ArgumentParser();p.add_argument('--exe',required=True)
    p.add_argument('--budget-ms',type=int,default=150)
    p.add_argument('--out',required=True)
    p.add_argument('--scenario',required=True)
    p.add_argument('--prior',required=True)
    p.add_argument('--source-N',type=int,required=True)
    p.add_argument('--source-orbits',type=int,required=True)
    z=p.parse_args()
    root=pathlib.Path(z.out)
    assert not root.exists()
    scenario=pathlib.Path(z.scenario)
    inp=scenario/'scenario-input.tsv'
    vault=scenario/'target-vault.tsv'
    manifest=json.loads((scenario/'manifest.json').read_text())
    assert manifest['lengths']==[z.source_N] and manifest['count']==144
    model=pathlib.Path('results/forced_models_v1/frozen_models.tsv')
    previous=pathlib.Path(z.prior)
    frozen=json.load(open('results/forced_models_v1/training_audit.json'))
    assert sha(model)==frozen['model_sha256']=='2abb727677b9c065b624322f1446fc950987d2c64fc41396e4b90e80c5ad576b'
    assert json.load(open(previous/'retention_search_verdict.json'))['states']==144
    root.mkdir(parents=True)
    env=os.environ.copy()
    env['LABS_FORCE_NONZERO']='1'
    env['LABS_RETAIN_ORIGINAL_X']='0'
    env['LABS_ALWAYS_ORIGINAL_X']='1'
    run([str(pathlib.Path(z.exe).resolve()),'deploy',str(inp),str(model),
         str(root/'events.tsv'),str(root/'sessions.tsv'),str(z.budget_ms)],env=env)
    print('FINISHED C-BLIND ALL-X ORIGINAL-STATE CLASSICAL SEARCH',flush=True)
    # Only after all 864 sessions complete may the independent evaluator see target C.
    run([sys.executable,'verify_hidden.py','deploy','--input',str(inp),
         '--vault',str(vault),'--events',str(root/'events.tsv'),
         '--sessions',str(root/'sessions.tsv'),'--output',str(root)])
    v=json.loads((root/'verdict.json').read_text())
    assert v['states']==144 and v['run_rows']==864 and v['n']==[z.source_N]
    assert sha(root/'events.tsv')==v['hashes']['events']
    gz=root/'events.tsv.gz'
    with (root/'events.tsv').open('rb') as src,gz.open('wb') as dst:
        with gzip.GzipFile(filename='',fileobj=dst,mode='wb',compresslevel=6,mtime=0) as f:
            shutil.copyfileobj(src,f,1<<20)
    assert gz.stat().st_size<90*(1<<20)
    h=hashlib.sha256()
    with gzip.open(gz,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    assert h.hexdigest()==v['hashes']['events']
    (root/'archive_provenance.json').write_text(json.dumps({
        'model_sha256':frozen['model_sha256'],
        'original_exact_event_sha256':h.hexdigest(),
        'compressed_sha256':sha(gz),'row_count':v['events'],
        'original_bytes':(root/'events.tsv').stat().st_size,
        'compressed_bytes':gz.stat().st_size},indent=2)+'\n')
    (root/'events.tsv').unlink()
    run([sys.executable,'compare_all_x_by_length.py','--input',str(inp),
       '--vault',str(vault),'--new',str(root),'--old',str(previous),'--out',str(root)])
    summary=json.load(open(root/'all_X_vs_alternating_verdict.json'))
    assert summary['states']==144 and summary['paired_strategy_sessions']==864
    assert all(s['states']==72 and s['shared_optimum_orbits']==z.source_orbits and s['mean_always_X_wall_ms']>=z.budget_ms
      for t in ('AB_blind','C_shell') for s in summary['by_tier'][t].values())
    (root/'protocol.json').write_text(json.dumps({
      'original_fixed_X_can_be_generated_without_C_vault':False,
      'C_shell_is_privileged_positive_control':True,
      'C_never_given_to_online_search':True,
      'frozen_model':frozen['model_sha256'],
      'source_N':z.source_N,
      'model_development_has_seen_source_orbits':True,
      'per_state_per_method_full_budget_ms':z.budget_ms,
      'all_X_restarts_experiment_is_posthoc':True,
      'candidate_bank_rules_unchanged':True},indent=2)+'\n')
    print('PASS C-BLIND STATIC X RESTART COMPARED WITH EXACT CLASSICAL CONTROL AND ALTERNATING X',flush=True)
if __name__=='__main__':main()
