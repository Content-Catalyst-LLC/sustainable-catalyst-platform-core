#!/usr/bin/env python3
import json,os,shutil,subprocess,tempfile
from pathlib import Path
from app.server import build_program
SWIPL=os.environ.get("SC_PROLOG_BIN") or shutil.which("swipl")
if not SWIPL:
    print("SKIP - swipl not installed; production deployment performs mandatory native validation")
    raise SystemExit(0)
cases=[
("relation_reachable",{"edges":[{"source":"a","target":"b"},{"source":"b","target":"c"}],"source":"a","target":"c"},lambda r:r["reachable"] is True),
("transitive_closure",{"edges":[{"source":"a","target":"b"},{"source":"b","target":"c"}]},lambda r:["a","c"] in r["pairs"]),
("contradiction_scan",{"assertions":["claim_a","claim_b"],"negations":["claim_b"]},lambda r:r["contradictions"]==["claim_b"]),
("temporal_consistency",{"temporal_edges":[{"source":"a","target":"b"},{"source":"b","target":"c"}]},lambda r:r["consistent"] is True),
("graph_coloring",{"vertex_count":3,"max_colors":3,"undirected_edges":[[0,1],[1,2],[0,2]]},lambda r:r["satisfiable"] is True and len(r["colors"])==3),
]
with tempfile.TemporaryDirectory() as td:
    for op,payload,check in cases:
        src=Path(td)/f"{op}.pl";src.write_text(build_program(op,payload));cp=subprocess.run([SWIPL,"-q","-f","none","-s",str(src),"-g","main","-t","halt"],capture_output=True,text=True)
        if cp.returncode!=0: raise SystemExit(f"FAIL {op}: {cp.stderr or cp.stdout}")
        lines=[x for x in cp.stdout.splitlines() if x.strip()];r=json.loads(lines[-1]);assert check(r), (op,r);print(f"PASS - native Prolog {op}")
print("PASS - native Prolog kernel validation")
