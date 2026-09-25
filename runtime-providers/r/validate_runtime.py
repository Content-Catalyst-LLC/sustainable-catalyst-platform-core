#!/usr/bin/env python3
from app.server import ADAPTER_ID,CAPABILITIES,PROVIDER_VERSION,RUNTIME_ID,adapter_descriptor,build_r_script,canonical_operation

assert RUNTIME_ID == "sc-runtime-r"
assert PROVIDER_VERSION == "1.0.0"
assert ADAPTER_ID == "adapter:sc-runtime-r"
assert len(CAPABILITIES) == 6
assert canonical_operation("lm") == "linear_regression"
assert canonical_operation("anova") == "one_way_anova"

desc = adapter_descriptor()
assert desc["status"] == "registered"
assert desc["execution_state"] == "active"
assert desc["boundaries"]["arbitrary_r_source"] is False
assert desc["boundaries"]["runtime_package_install"] is False

script = build_r_script("linear_regression", {
    "data":{"x":[1,2,3],"y":[2,4,6]},
    "outcome":"y",
    "predictors":["x"],
})
assert "reformulate" in script
assert "system(" not in script
assert "eval(parse" not in script

print("PASS - Sustainable Catalyst R Runtime v1.0.0 static validation")
print("RUNTIME_ID=sc-runtime-r")
print("ADAPTER_ID=adapter:sc-runtime-r")
print("CAPABILITIES=6")
print("LEGACY_ANALYTICS_R_COMPATIBILITY=enabled")
print("ARBITRARY_R_SOURCE=false")
print("RUNTIME_PACKAGE_INSTALL=false")
