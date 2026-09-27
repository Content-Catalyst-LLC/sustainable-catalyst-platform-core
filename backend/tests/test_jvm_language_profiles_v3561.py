import pytest
from pydantic import ValidationError

from app.services.jvm_language_profiles import (
    ADAPTER_ID,
    CONTRACT_VERSION,
    JAVA_PROFILE_ID,
    KOTLIN_PROFILE_ID,
    RUNTIME_ID,
    SCALA_PROFILE_ID,
    JVMLanguageProfileResolutionRequest,
    canonical_profiles,
    contract_document,
    reference_catalog,
    resolve_profile,
    to_scientific_profile_artifact,
)


def test_identity():
    assert CONTRACT_VERSION == "sc.core.jvm-language-profiles.v1"
    assert RUNTIME_ID == "sc-runtime-jvm"
    assert ADAPTER_ID == "adapter:sc-runtime-jvm"


def test_three_canonical_profiles():
    p = canonical_profiles()
    assert [x.profile_id for x in p] == [JAVA_PROFILE_ID, KOTLIN_PROFILE_ID, SCALA_PROFILE_ID]
    assert [x.language.value for x in p] == ["java", "kotlin", "scala"]


def test_versions():
    p = {x.language.value: x for x in canonical_profiles()}
    assert p["java"].language_version == "21"
    assert p["kotlin"].language_version == "2.4.20"
    assert p["scala"].language_version == "3.9.0"


def test_boundaries():
    for p in canonical_profiles():
        assert p.arbitrary_source_allowed is False
        assert p.caller_classpath_allowed is False
        assert p.dependency_install_allowed is False
        assert p.network_access_allowed is False


def test_catalog_explicit_binding():
    c = reference_catalog()
    assert c.explicit_profile_binding_required is True
    assert c.autonomous_profile_selection is False
    assert c.allowed_products == ["workspace", "research-lab", "workbench"]
    assert len(c.fingerprint()) == 64


def test_resolve_java():
    r = resolve_profile(JVMLanguageProfileResolutionRequest(resolution_id="resolution:java", product_id="workbench", profile_id=JAVA_PROFILE_ID))
    assert r.language.value == "java"
    assert r.mode == "explicit-profile-binding-validated"


def test_resolve_kotlin():
    r = resolve_profile(JVMLanguageProfileResolutionRequest(resolution_id="resolution:kotlin", product_id="research-lab", profile_id=KOTLIN_PROFILE_ID))
    assert r.language.value == "kotlin"
    assert r.language_version == "2.4.20"


def test_resolve_scala():
    r = resolve_profile(JVMLanguageProfileResolutionRequest(resolution_id="resolution:scala", product_id="workspace", profile_id=SCALA_PROFILE_ID))
    assert r.language.value == "scala"
    assert r.language_version == "3.9.0"


def test_unknown_profile_rejected():
    with pytest.raises(ValueError):
        resolve_profile(JVMLanguageProfileResolutionRequest(resolution_id="resolution:bad", product_id="workspace", profile_id="bad"))


def test_bad_product_rejected():
    with pytest.raises(ValueError):
        resolve_profile(JVMLanguageProfileResolutionRequest(resolution_id="resolution:bad", product_id="unknown", profile_id=JAVA_PROFILE_ID))


def test_contract():
    d = contract_document()
    assert d["release"] == "3.56.1"
    assert d["profile_count"] == 3
    assert d["capabilities"]["java_profile"] is True
    assert d["capabilities"]["kotlin_profile"] is True
    assert d["capabilities"]["scala_profile"] is True
    assert d["boundaries"]["core_autonomously_selects_language_profile"] is False


def test_artifact():
    a = to_scientific_profile_artifact()
    assert a["source_contract"] == CONTRACT_VERSION
    assert a["metadata"]["runtime_id"] == RUNTIME_ID
    assert len(a["content_sha256"]) == 64
