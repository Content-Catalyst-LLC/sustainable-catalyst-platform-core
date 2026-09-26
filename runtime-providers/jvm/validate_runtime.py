#!/usr/bin/env python3
from app.server import ADAPTER_ID,OPERATIONS,PROVIDER_VERSION,RUNTIME_ID,adapter_descriptor,build_source

def main():
    assert RUNTIME_ID=='sc-runtime-jvm';assert ADAPTER_ID=='adapter:sc-runtime-jvm';assert PROVIDER_VERSION=='1.0.0';assert len(OPERATIONS)==6
    d=adapter_descriptor();assert d['runtime_kind']=='execution-target';assert d['boundaries']['arbitrary_jvm_bytecode'] is False;assert d['boundaries']['runtime_dependency_install'] is False
    assert 'parallel().sum()' in build_source('parallel_sum',{'values':[1,2,3]})
    print('PASS - Sustainable Catalyst JVM Runtime v1.0.0 contract validation')
    print('RUNTIME_ID=sc-runtime-jvm');print('ADAPTER_ID=adapter:sc-runtime-jvm');print('JVM_MAJOR_VERSION=21');print('OPERATIONS='+','.join(OPERATIONS))
if __name__=='__main__':main()
