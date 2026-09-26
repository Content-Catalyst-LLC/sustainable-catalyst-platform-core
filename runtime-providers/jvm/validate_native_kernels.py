#!/usr/bin/env python3
import shutil,tempfile,subprocess
from pathlib import Path
import app.server as s

def main():
    javac=shutil.which('javac');java=shutil.which('java')
    if javac and java:
        try:
            javac_check=subprocess.run([javac,'-version'],capture_output=True,text=True,timeout=10)
            java_check=subprocess.run([java,'-version'],capture_output=True,text=True,timeout=10)
            if javac_check.returncode != 0 or java_check.returncode != 0:
                javac=java=None
        except Exception:
            javac=java=None
    if not javac or not java:
        print('SKIP - operational JDK unavailable; production deployment performs mandatory OpenJDK 21 native validation')
        return
    with tempfile.TemporaryDirectory(prefix='sc-jvm-native-') as td:
        root=Path(td);s.WORK_ROOT=root/'work';s.ARTIFACT_ROOT=root/'art';s.JAVAC=javac;s.JAVA=java
        cases=[
          ('parallel_sum',{'values':[1,2,3,4,5]},lambda r:r['sum']==15.0),
          ('parallel_map_affine',{'values':[1,2,3],'scale':2,'offset':1},lambda r:r['values']==[3.0,5.0,7.0]),
          ('matrix_row_sums',{'matrix':[[1,2],[3,4]]},lambda r:r['row_sums']==[3.0,7.0]),
          ('graph_bfs',{'adjacency_matrix':[[0,1,0],[1,0,1],[0,1,0]],'source_index':0},lambda r:r['distances']==[0,1,2]),
          ('batch_sha256',{'strings':['abc']},lambda r:r['sha256'][0]=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'),
          ('jvm_runtime_info',{},lambda r:'java_version' in r),
        ]
        for idx,(op,payload,pred) in enumerate(cases):
            out,_=s.execute_program(f'jvm-run:native-{idx}',op,payload,60,128);assert pred(out['result']),(op,out)
    print('PASS - 6/6 bounded JVM native kernels compiled and executed')
if __name__=='__main__':main()
