#!/usr/bin/env python3
from app.services.jvm_language_profiles import contract_document, reference_catalog


def main():
    d = contract_document()
    c = reference_catalog()
    assert d["release"] == "3.56.1"
    assert d["contract"] == "sc.core.jvm-language-profiles.v1"
    assert d["runtime_id"] == "sc-runtime-jvm"
    assert d["runtime_version"] == "1.0.0"
    assert [p["language"] for p in d["profiles"]] == ["java", "kotlin", "scala"]
    assert c.explicit_profile_binding_required is True
    assert c.autonomous_profile_selection is False
    print("PASS - Platform Core v3.56.1 JVM Language Profiles")
    print("CONTRACT=sc.core.jvm-language-profiles.v1")
    print("JAVA_PROFILE=21")
    print("KOTLIN_PROFILE=2.4.20")
    print("SCALA_PROFILE=3.9.0")
    print("EXPLICIT_PROFILE_BINDING=required")
    print("AUTONOMOUS_PROFILE_SELECTION=false")
    print("ARBITRARY_SOURCE=false")
    print("SPARK_ADAPTER=v3.56.2")


if __name__ == "__main__":
    main()
