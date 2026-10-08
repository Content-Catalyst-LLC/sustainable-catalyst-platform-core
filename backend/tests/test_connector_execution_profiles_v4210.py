from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.routers import connector_execution_profiles as api
from app.services.connector_execution_profiles import (
    ProfileMode,
    all_profiles,
    get_profile,
    profile_contract_document,
    profile_requested_by,
    reference_connector_profile_contract,
    resolve_profile_parameters,
    scheduled_profiles,
    validate_profile_against_connector,
    validate_profile_contract_coverage,
)


REQUIREMENTS = {
    "met-no.locationforecast": {"required_parameters": ["lat", "lon"]},
    "world-bank.indicators": {"required_parameters": ["indicator"]},
    "fred.series-observations": {"required_parameters": ["series_id"]},
    "un.sdg-metadata": {"required_parameters": ["series"]},
    "un.population-data": {"required_parameters": ["indicators", "locations", "start_year", "end_year"]},
    "un.comtrade": {"required_parameters": ["reporter_code", "period"]},
    "nasa.cmr-collections": {"required_parameters": ["keyword"]},
    "noaa.ncei-data": {"required_parameters": ["dataset", "start_date", "end_date"]},
    "ecmwf.open-data-index": {"required_parameters": ["date", "run", "stream", "type", "step"]},
    "usgs.water-instantaneous": {"required_one_of": ["sites", "state_cd", "b_box"]},
    "imf.sdmx": {"required_parameters": ["agency", "dataset", "key"]},
    "oecd.sdmx": {"required_parameters": ["agency", "dataset", "key"]},
    "eurostat.statistics": {"required_parameters": ["dataset"]},
    "ecb.sdmx": {"required_parameters": ["flow_ref", "key"]},
    "bis.sdmx": {"required_parameters": ["flow_ref", "key"]},
    "bea.statistics": {"required_parameters": ["dataset_name"]},
    "bls.timeseries": {"required_parameters": ["series_ids"]},
    "census.data": {"required_parameters": ["year", "dataset", "get", "for"]},
    "sec.companyfacts": {"required_parameters": ["cik"]},
    "eia.v2-data": {"required_parameters": ["route", "data_fields"]},
    "faostat.data": {"required_parameters": ["domain_code"]},
    "ilostat.sdmx": {"required_parameters": ["flow_ref", "key"]},
}


def fake_connector(connector_id: str):
    return SimpleNamespace(id=connector_id, configuration_json=REQUIREMENTS[connector_id])


def test_release_contract_and_coverage():
    bundle = reference_connector_profile_contract()
    assert bundle.release == "4.21.0"
    assert bundle.contract == "sc.core.parameterized-connector-execution-profile.v1"
    assert bundle.predecessor_release == "4.20.3"
    assert len(bundle.profiles) == 22
    assert {p.connector_id for p in bundle.profiles} == set(REQUIREMENTS)
    assert bundle.database_migration == "none"


def test_one_canonical_profile_per_connector():
    profiles = all_profiles()
    assert len({p.profile_id for p in profiles}) == 22
    assert len({p.connector_id for p in profiles}) == 22


def test_profile_contracts_cover_connector_requirements():
    for profile in all_profiles():
        assert validate_profile_contract_coverage(
            profile,
            fake_connector(profile.connector_id),
        )["valid"]


def test_scheduler_safe_default_contract():
    doc = profile_contract_document()
    assert doc["scheduler"]["disabled_by_default"] is True
    assert doc["scheduler"]["allowlist_supported"] is True
    assert doc["boundaries"]["template_profile_auto_executes"] is False
    assert doc["database_migration"] == "none"


def test_nine_scheduled_reference_profiles():
    profiles = scheduled_profiles()
    assert len(profiles) == 9
    assert all(profile.mode == ProfileMode.scheduled for profile in profiles)
    assert all(not profile.required_parameters for profile in profiles)
    assert all(not profile.required_one_of for profile in profiles)


def test_template_profiles_never_scheduler_eligible():
    assert all(
        not profile.scheduler_eligible
        for profile in all_profiles()
        if profile.mode == ProfileMode.template
    )


def test_dynamic_parameter_resolution():
    now = datetime(2026, 10, 8, 13, 15, tzinfo=timezone.utc)

    world_bank = get_profile("profile:world-bank:us-gdp-per-capita")
    resolved = resolve_profile_parameters(world_bank, now=now)
    assert resolved["date"] == "2021:2026"

    census = get_profile("profile:census:state-demographic-baseline")
    resolved = resolve_profile_parameters(census, now=now)
    assert resolved["year"] == "2024"

    ecb = get_profile("profile:ecb:usd-eur-reference-rate")
    resolved = resolve_profile_parameters(ecb, now=now)
    assert resolved["endPeriod"] == "2026-10-08"


def test_ecmwf_resolution_uses_lagged_cycle():
    profile = get_profile("profile:ecmwf:latest-operational-index")
    resolved = resolve_profile_parameters(
        profile,
        now=datetime(2026, 10, 8, 13, 0, tzinfo=timezone.utc),
    )
    assert resolved["date"] == "20261008"
    assert resolved["run"] == "00"


def test_scheduled_profiles_resolve_to_connector_valid_parameters():
    now = datetime(2026, 10, 8, 13, 15, tzinfo=timezone.utc)
    for profile in scheduled_profiles():
        params = resolve_profile_parameters(profile, now=now)
        assert validate_profile_against_connector(
            profile,
            fake_connector(profile.connector_id),
            parameters=params,
        )["valid"]


def test_template_bindings_are_enforced():
    profile = get_profile("profile:met-no:point-forecast")
    with pytest.raises(ValueError):
        resolve_profile_parameters(profile)

    params = resolve_profile_parameters(
        profile,
        overrides={"lat": 38.6270, "lon": -90.1994},
    )
    assert validate_profile_against_connector(
        profile,
        fake_connector(profile.connector_id),
        parameters=params,
    )["valid"]


def test_usgs_one_of_binding_is_enforced():
    profile = get_profile("profile:usgs-water:bounded-selection")
    with pytest.raises(ValueError):
        resolve_profile_parameters(profile)

    params = resolve_profile_parameters(profile, overrides={"state_cd": "MO"})
    assert validate_profile_against_connector(
        profile,
        fake_connector(profile.connector_id),
        parameters=params,
    )["valid"]


def test_credentials_cannot_enter_profile_parameters():
    profile = get_profile("profile:world-bank:us-gdp-per-capita")
    with pytest.raises(ValueError):
        resolve_profile_parameters(profile, overrides={"api_key": "nope"})


def test_requested_by_is_profile_specific():
    assert profile_requested_by("profile:world-bank:us-gdp-per-capita") == (
        "connector-profile:profile:world-bank:us-gdp-per-capita"
    )


def test_contract_document_counts():
    doc = profile_contract_document()
    assert doc["reference"]["profile_count"] == 22
    assert doc["reference"]["connector_count"] == 22
    assert doc["reference"]["scheduler_eligible_count"] == 9
    assert doc["reference"]["template_count"] == 13


def test_profile_fingerprints_are_deterministic():
    bundle = reference_connector_profile_contract()
    assert bundle.fingerprint() == reference_connector_profile_contract().fingerprint()
    assert {p.profile_id: p.fingerprint() for p in bundle.profiles} == {
        p.profile_id: p.fingerprint()
        for p in reference_connector_profile_contract().profiles
    }


def test_api_static_surfaces():
    assert api.contract()["release"] == "4.21.0"
    assert api.public_contract()["release"] == "4.21.0"
    assert api.profiles()["count"] == 22
    assert api.public_profiles()["count"] == 22
    assert api.profile("profile:world-bank:us-gdp-per-capita")["ok"] is True


def test_main_mounts_v4210_routes():
    from app.main import create_app

    app = create_app()
    paths = {route.path for route in app.routes}
    assert "/v1/connector-profiles/contract" in paths
    assert "/public/v1/connector-profiles/contract" in paths
    assert "/v1/connector-profiles/readiness" in paths
    assert "/v1/connector-profiles/profiles/{profile_id:path}/queue" in paths
