#!/usr/bin/env python3
from app.server import ADAPTER_ID,OPERATIONS,PROVIDER_VERSION,RUNTIME_ID,SWI_PROLOG_VERSION,adapter_descriptor,build_program

def main():
    assert RUNTIME_ID=="sc-runtime-prolog";assert ADAPTER_ID=="adapter:sc-runtime-prolog";assert PROVIDER_VERSION=="1.0.0";assert SWI_PROLOG_VERSION=="9.0.4";assert len(OPERATIONS)==6
    a=adapter_descriptor();assert a["boundaries"]["arbitrary_prolog_source"] is False
    s=build_program("relation_reachable",{"edges":[{"source":"a","target":"b"},{"source":"b","target":"c"}],"source":"a","target":"c"});assert "reach(a,c)" in s
    print("PASS - Sustainable Catalyst Prolog Runtime v1.0.0 contract validation")
    print("RUNTIME_ID=sc-runtime-prolog");print("ADAPTER_ID=adapter:sc-runtime-prolog");print("OPERATIONS="+",".join(OPERATIONS))
if __name__=="__main__": main()
