#!/usr/bin/env python3
from app.server import ADAPTER_ID,OPERATIONS,PROVIDER_VERSION,RUNTIME_ID,adapter_descriptor,build_source

BASE_OPERATIONS={
    "jvm_runtime_info",
    "parallel_sum",
    "parallel_map_affine",
    "matrix_row_sums",
    "graph_bfs",
    "batch_sha256",
}

def main():
    assert RUNTIME_ID=='sc-runtime-jvm'
    assert ADAPTER_ID=='adapter:sc-runtime-jvm'
    assert PROVIDER_VERSION=='1.0.0'
    assert BASE_OPERATIONS.issubset(set(OPERATIONS))
    assert len(OPERATIONS)==len(set(OPERATIONS))
    d=adapter_descriptor()
    assert d['provider_version']=='1.0.0'
    assert d['runtime_kind']=='execution-target'
    assert d['boundaries']['arbitrary_jvm_bytecode'] is False
    assert d['boundaries']['runtime_dependency_install'] is False
    assert 'parallel().sum()' in build_source('parallel_sum',{'values':[1,2,3]})
    print('PASS - Sustainable Catalyst JVM Runtime v1.0.0 compatibility contract validation')
    print('RUNTIME_ID=sc-runtime-jvm')
    print('ADAPTER_ID=adapter:sc-runtime-jvm')
    print('JVM_MAJOR_VERSION=21')
    print('BASE_OPERATIONS=' + ','.join(sorted(BASE_OPERATIONS)))
    print('OPERATIONS=' + ','.join(OPERATIONS))
    print('ADDITIVE_OPERATIONS=' + ','.join([op for op in OPERATIONS if op not in BASE_OPERATIONS]))
if __name__=='__main__':main()
