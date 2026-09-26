#!/usr/bin/env python3
import os, shutil, subprocess, tempfile
from pathlib import Path
from app.server import generated_source, parse_output

rustc=os.environ.get("RUSTC") or shutil.which("rustc")
if not rustc:
    print("SKIP - local rustc unavailable; production deployment performs mandatory native Rust compilation/execution")
    raise SystemExit(0)

cases=[
    ("prefix_sum",{"integers":[1,2,3,4,5]},lambda r:r["values"]==[1,3,6,10,15]),
    ("moving_average",{"values":[1,2,3,4],"window":2},lambda r:r["values"]==[1.5,2.5,3.5]),
    ("connected_components",{"adjacency_matrix":[[0,1,0],[1,0,0],[0,0,0]]},lambda r:r["values"]==[0,0,1]),
    ("topological_sort",{"vertex_count":4,"edge_list":[[0,1],[0,2],[1,3],[2,3]]},lambda r:r["values"] in ([0,1,2,3],[0,2,1,3])),
    ("levenshtein_distance",{"text_a":"kitten","text_b":"sitting"},lambda r:r["value"]==3),
    ("fnv1a_64",{"text":"abc"},lambda r:r["value"]=="e71fa2190541574b"),
]
with tempfile.TemporaryDirectory(prefix="sc-rust-native-") as td:
    td=Path(td)
    for idx,(operation,payload,check) in enumerate(cases):
        src=td/f"case{idx}.rs"; exe=td/f"case{idx}.bin"
        src.write_text(generated_source(operation,payload))
        cp=subprocess.run([rustc,"--edition=2021","-Copt-level=2","-Coverflow-checks=on",str(src),"-o",str(exe)],capture_output=True,text=True)
        assert cp.returncode==0,(operation,cp.stderr)
        run=subprocess.run([str(exe)],capture_output=True,text=True)
        assert run.returncode==0,(operation,run.stderr)
        result=parse_output(run.stdout)
        assert check(result),(operation,result)
        print(f"PASS - native Rust kernel {operation}")
print(f"PASS - {len(cases)}/{len(cases)} generated Rust kernels compiled and executed")
