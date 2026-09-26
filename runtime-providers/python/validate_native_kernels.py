import json, os, subprocess, sys, tempfile
from pathlib import Path
from app.server import generated_source, validate_payload
PY=os.environ.get('SC_PYTHON_BIN') or sys.executable
CASES=[
 ('descriptive_summary',{'values':[1,2,3,4,5]},lambda r:abs(r['mean']-3)<1e-12),
 ('linear_regression',{'x':[1,2,3],'y':[2,4,6]},lambda r:abs(r['slope']-2)<1e-12 and abs(r['r_squared']-1)<1e-12),
 ('matrix_multiply',{'matrix_a':[[1,2],[3,4]],'matrix_b':[[5,6],[7,8]]},lambda r:r['matrix']==[[19,22],[43,50]]),
 ('standardize',{'values':[1,2,3]},lambda r:abs(sum(r['values']))<1e-12),
 ('bootstrap_mean_ci',{'values':[1,2,3,4],'iterations':100,'confidence':.95,'seed':42},lambda r:r['seed']==42 and r['lower']<=r['observed_mean']<=r['upper']),
 ('token_frequency',{'text':'alpha beta alpha gamma','top_k':3,'lowercase':True},lambda r:r['frequencies'][0]=={'token':'alpha','count':2}),
]
for op,payload,check in CASES:
    validate_payload(op,payload)
    with tempfile.TemporaryDirectory(prefix='sc-python-kernel-') as td:
        p=Path(td);(p/'program.py').write_text(generated_source(op,payload));(p/'input.json').write_text(json.dumps({'operation':op,'payload':payload},sort_keys=True))
        cp=subprocess.run([PY,'-I','-S',str(p/'program.py')],cwd=p,text=True,capture_output=True,timeout=120)
        if cp.returncode!=0:raise SystemExit(f'{op} failed: {cp.stderr or cp.stdout}')
        r=json.loads((p/'result.json').read_text());assert check(r),f'{op} result check failed: {r}'
        print(f'PASS - Python native kernel {op}')
print(f'PASS - {len(CASES)}/{len(CASES)} bounded Python kernels executed')
