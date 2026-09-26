import os,shutil,subprocess,tempfile
from pathlib import Path
from app.server import generated_source,parse_output
GO=os.environ.get('GO',shutil.which('go') or '')
if not GO:
    print('SKIP - Go compiler not installed locally; production deployment requires native validation');raise SystemExit(0)
cases=[
 ('parallel_sum',{'values':[1,2,3,4],'workers':2},lambda r:abs(r['value']-10)<1e-12),
 ('parallel_map_affine',{'values':[1,2,3],'scale':2,'offset':1,'workers':2},lambda r:r['values']==[3,5,7]),
 ('concurrent_histogram',{'values':[0,0.5,1,1.5,2],'bins':2,'minimum':0,'maximum':2,'workers':2},lambda r:r['values']==[2,3]),
 ('parallel_matrix_row_sums',{'matrix':[[1,2],[3,4]],'workers':2},lambda r:r['values']==[3,7]),
 ('parallel_graph_degrees',{'adjacency_matrix':[[0,1,1],[1,0,0],[1,0,0]],'workers':2},lambda r:r['values']==[2,1,1]),
 ('batch_sha256',{'texts':['abc'],'workers':1},lambda r:r['values']==['ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad']),
]
with tempfile.TemporaryDirectory() as shared:
    shared=Path(shared);cache=shared/'cache';gopath=shared/'gopath'
    for idx,(op,payload,check) in enumerate(cases):
        td=shared/f'case-{idx}';td.mkdir();src=td/'main.go';out=td/'app';src.write_text(generated_source(op,payload));env=os.environ.copy();env.update({'GOTOOLCHAIN':'local','GOPROXY':'off','GOSUMDB':'off','GO111MODULE':'off','CGO_ENABLED':'0','GOCACHE':str(cache),'GOPATH':str(gopath)});cp=subprocess.run([GO,'build','-trimpath','-o',str(out),str(src)],capture_output=True,text=True,env=env);assert cp.returncode==0,(op,cp.stderr);rp=subprocess.run([str(out)],capture_output=True,text=True);assert rp.returncode==0,(op,rp.stderr);r=parse_output(rp.stdout);assert check(r),(op,r)
print(f'PASS - {len(cases)}/{len(cases)} generated Go kernels compiled and executed')
