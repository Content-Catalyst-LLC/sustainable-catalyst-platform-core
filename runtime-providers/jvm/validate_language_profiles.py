#!/usr/bin/env python3
from app.server import JVM_LANGUAGE_PROFILES, PROVIDER_VERSION, language_profiles_descriptor


def main():
    d = language_profiles_descriptor()
    assert PROVIDER_VERSION == "1.0.0"
    assert [p["language"] for p in JVM_LANGUAGE_PROFILES] == ["java", "kotlin", "scala"]
    assert d["explicit_profile_binding_required"] is True
    assert d["autonomous_profile_selection"] is False
    print("PASS - Sustainable Catalyst JVM Language Profiles v1.0.0 contract validation")
    print("PROVIDER_VERSION=1.0.0")
    print("PROFILES=java-21,kotlin-2.4.20,scala-3.9.0")


if __name__ == "__main__":
    main()
