from app.server import JVM_LANGUAGE_PROFILES, language_profiles_descriptor


def test_language_profile_count():
    assert len(JVM_LANGUAGE_PROFILES) == 3


def test_language_profile_order():
    assert [x["language"] for x in JVM_LANGUAGE_PROFILES] == ["java", "kotlin", "scala"]


def test_language_profile_versions():
    p = {x["language"]: x for x in JVM_LANGUAGE_PROFILES}
    assert p["java"]["language_version"] == "21"
    assert p["kotlin"]["language_version"] == "2.4.20"
    assert p["scala"]["language_version"] == "3.9.0"


def test_profile_boundaries():
    d = language_profiles_descriptor()
    assert d["runtime_id"] == "sc-runtime-jvm"
    assert d["provider_version"] == "1.0.0"
    assert d["explicit_profile_binding_required"] is True
    assert d["autonomous_profile_selection"] is False
    assert d["boundaries"]["arbitrary_source"] is False
    assert d["boundaries"]["caller_classpath"] is False
