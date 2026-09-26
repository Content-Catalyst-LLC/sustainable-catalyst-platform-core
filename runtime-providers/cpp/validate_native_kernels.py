#!/usr/bin/env python3
from __future__ import annotations
import json, os, subprocess, tempfile
from pathlib import Path
from app.server import generated_source, parse_output

CC = os.environ.get("CC", "cc")
CXX = os.environ.get("CXX", "c++")
CASES = [
    ("dot_product", {"a":[1,2,3],"b":[4,5,6]}, {"kind":"scalar","value":32.0}),
    ("matrix_multiply", {"a":[[1,2],[3,4]],"b":[[5,6],[7,8]]}, {"kind":"matrix","rows":2,"cols":2,"values":[[19.0,22.0],[43.0,50.0]]}),
    ("linear_interpolation", {"x":[0,10,20],"y":[0,10,20],"query_x":15}, {"kind":"scalar","value":15.0}),
    ("polynomial_evaluate", {"coefficients":[1,2,3],"x":2}, {"kind":"scalar","value":17.0}),
    ("fir_filter", {"signal":[1,2,3],"kernel":[0.5,0.5]}, {"kind":"vector","values":[0.5,1.5,2.5]}),
    ("dijkstra_shortest_path", {"adjacency":[[0,1,4],[1,0,2],[4,2,0]],"source":0,"target":2}, {"kind":"scalar","value":3.0}),
]

def approx_equal(a,b,tol=1e-9):
    if isinstance(a,(int,float)) and isinstance(b,(int,float)):
        return abs(float(a)-float(b)) <= tol
    if isinstance(a,list) and isinstance(b,list) and len(a)==len(b):
        return all(approx_equal(x,y,tol) for x,y in zip(a,b))
    if isinstance(a,dict) and isinstance(b,dict) and set(a)==set(b):
        return all(approx_equal(a[k],b[k],tol) for k in a)
    return a==b

with tempfile.TemporaryDirectory(prefix="sc-cpp-native-") as td:
    td = Path(td)
    for idx,(op,payload,expected) in enumerate(CASES,1):
        lang, src = generated_source(op,payload)
        source = td / (f"case{idx}.c" if lang=="c11" else f"case{idx}.cpp")
        binary = td / f"case{idx}.bin"
        source.write_text(src)
        cmd = [CC,"-O2","-std=c11","-fno-fast-math",str(source),"-lm","-o",str(binary)] if lang=="c11" else [CXX,"-O2","-std=c++17","-fno-fast-math",str(source),"-o",str(binary)]
        cp = subprocess.run(cmd,capture_output=True,text=True)
        if cp.returncode != 0:
            raise SystemExit(f"FAIL compile {op}: {cp.stderr}")
        rp = subprocess.run([str(binary)],capture_output=True,text=True)
        if rp.returncode != 0:
            raise SystemExit(f"FAIL execute {op}: {rp.stderr}")
        actual = parse_output(rp.stdout)
        if not approx_equal(actual,expected):
            raise SystemExit(f"FAIL result {op}: expected={expected} actual={actual}")
        print(f"PASS - native {lang} kernel {op}")
print("PASS - Sustainable Catalyst C/C++ Runtime native kernel validation 6/6")
