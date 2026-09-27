#!/usr/bin/env bash
set -euo pipefail
export SC_KOTLINC_BIN="/opt/sustainable-catalyst/toolchains/kotlin-2.4.20/bin/kotlinc"
export SC_SCALA_BIN="/opt/sustainable-catalyst/toolchains/scala3-3.9.0/bin/scala"
export SC_SCALAC_BIN="/opt/sustainable-catalyst/toolchains/scala3-3.9.0/bin/scalac"

python3 /opt/sustainable-catalyst/jvm-runtime/validate_language_profiles_native.py

curl -fsS http://127.0.0.1:18105/v1/language-profiles | tee /tmp/sc-jvm-language-profiles.json | python3 -m json.tool
python3 - <<'PY'
import json
p=json.load(open('/tmp/sc-jvm-language-profiles.json'))
assert p['runtime_id']=='sc-runtime-jvm'
assert p['provider_version']=='1.0.0'
assert [x['language'] for x in p['profiles']]==['java','kotlin','scala']
assert [x['language_version'] for x in p['profiles']]==['21','2.4.20','3.9.0']
assert p['explicit_profile_binding_required'] is True
assert p['autonomous_profile_selection'] is False
print('PASS - live JVM language profile descriptor')
PY

echo 'PASS - SUSTAINABLE CATALYST JVM LANGUAGE PROFILES v1.0.0 BACKEND CERTIFICATION COMPLETE'
