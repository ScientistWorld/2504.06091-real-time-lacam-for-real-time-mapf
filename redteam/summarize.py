"""Summarize returned metric vectors; never used to generate method artifacts."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT/'redteam'
BASE = json.loads((AUDIT/'starting_state.json').read_text())['base_commit']
reference = json.loads(subprocess.check_output(['git','show',BASE+':scoring/reference.json'],cwd=ROOT))
packaged = json.loads(subprocess.check_output(['git','show',BASE+':scoring/scores_test.json'],cwd=ROOT))

def weighted_diagnostic(scores,method='rt_lacam'):
    total=0
    for exp,config in reference['experiments'].items():
        row=scores.get('experiments',{}).get(exp,{}).get('results',{}).get(method)
        if row is None:
            return None
        for metric,definition in config['metrics'].items():
            value=row.get(metric)
            if value is None:
                return None
            total += config['weight']*definition['coefficient']*value
    return total

cases={}
for folder in sorted(AUDIT.iterdir()):
    if not (folder/'complete.json').exists():
        continue
    scores=json.loads((folder/'scores_test.json').read_text())
    train=json.loads((folder/'scores_train.json').read_text())
    cases[folder.name]={
        'test':{e:x['results'].get('rt_lacam') for e,x in scores['experiments'].items()},
        'train':{e:x['results'].get('rt_lacam') for e,x in train['experiments'].items()},
        'coefficient_weighted_diagnostic_not_external_rank':weighted_diagnostic(scores),
        'commands_passed':all(json.loads(line)['returncode']==0 for line in (folder/'commands.jsonl').read_text().splitlines()),
    }
reference_scores=json.loads((AUDIT/'reference_seed0/scores_test.json').read_text())
seeds=[cases[f'reference_seed{s}']['test'] for s in (0,1,2)]
spread={e:{m:max(s[e][m] for s in seeds)-min(s[e][m] for s in seeds)
           for m in seeds[0][e] if isinstance(seeds[0][e][m],(int,float))} for e in seeds[0]}
summary={
    'warning':'No external ranking implementation is supplied. The coefficient-weighted sum is an explicitly labeled diagnostic, not an observed rank.',
    'formula':'sum_experiment(weight * sum_metric(coefficient * returned metric))',
    'reference_reproduces_packaged_test_scores_exactly':reference_scores==packaged,
    'seed_spread_max_minus_min':spread,
    'seed_diagnostic_spread':max(cases[f'reference_seed{s}']['coefficient_weighted_diagnostic_not_external_rank'] for s in (0,1,2))-min(cases[f'reference_seed{s}']['coefficient_weighted_diagnostic_not_external_rank'] for s in (0,1,2)),
    'baseline_coefficient_weighted_diagnostics':{m:weighted_diagnostic(reference_scores,m) for m in ('full_lacam','naive_rt_lacam','rt_lacam')},
    'cases':cases,
}
(AUDIT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
for name,case in cases.items():
    print(name,case['coefficient_weighted_diagnostic_not_external_rank'])
print('Packaged scores exactly reproduced:',summary['reference_reproduces_packaged_test_scores_exactly'])
print('Seed diagnostic spread:',summary['seed_diagnostic_spread'])
