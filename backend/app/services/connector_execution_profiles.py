from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from functools import lru_cache
import re
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256

CORE_RELEASE = "4.21.0"
CONTRACT_VERSION = "sc.core.parameterized-connector-execution-profile.v1"
PREDECESSOR_RELEASE = "4.20.3"
REQUESTED_BY_PREFIX = "connector-profile:"

SENSITIVE_PARAMETER_PARTS = (
    "api_key",
    "apikey",
    "token",
    "secret",
    "password",
    "authorization",
    "credential",
    "registrationkey",
    "user_id",
    "userid",
)


class ProfileMode(str, Enum):
    scheduled = "scheduled"
    template = "template"


class ConnectorExecutionProfile(BaseModel):
    profile_id: str = Field(min_length=3, max_length=180)
    connector_id: str = Field(min_length=3, max_length=180)
    display_name: str = Field(min_length=3, max_length=240)
    description: str = Field(min_length=10)
    domain: str = Field(min_length=2, max_length=100)
    mode: ProfileMode
    parameters: dict[str, Any] = Field(default_factory=dict)
    required_parameters: list[str] = Field(default_factory=list)
    required_one_of: list[str] = Field(default_factory=list)
    refresh_policy: str = Field(min_length=2, max_length=100)
    scheduler_eligible: bool = False
    priority: int = Field(default=100, ge=0, le=1000)
    max_attempts: int = Field(default=3, ge=1, le=20)
    scope: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    parameters_contain_credentials: Literal[False] = False
    profile_scope_is_not_global_coverage: Literal[True] = True
    execution_does_not_establish_truth: Literal[True] = True
    automatic_evidence_promotion: Literal[False] = False

    @model_validator(mode="after")
    def validate_profile(self):
        if self.mode == ProfileMode.template and self.scheduler_eligible:
            raise ValueError("Template profiles cannot be scheduler eligible.")
        if self.mode == ProfileMode.scheduled and (self.required_parameters or self.required_one_of):
            raise ValueError("Scheduled profiles must resolve all required parameters without caller bindings.")
        if len(self.required_parameters) != len(set(self.required_parameters)):
            raise ValueError("required_parameters must be unique.")
        if len(self.required_one_of) != len(set(self.required_one_of)):
            raise ValueError("required_one_of must be unique.")
        if len(self.tags) != len(set(self.tags)):
            raise ValueError("tags must be unique.")
        _assert_no_sensitive_parameters(self.parameters)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ConnectorProfileContract(BaseModel):
    release: Literal["4.21.0"] = "4.21.0"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    predecessor_release: Literal["4.20.3"] = "4.20.3"
    profiles: list[ConnectorExecutionProfile] = Field(min_length=1)
    database_migration: Literal["none"] = "none"
    scheduler_disabled_by_default: Literal[True] = True
    secrets_in_profiles: Literal[False] = False
    profiles_establish_truth: Literal[False] = False
    profiles_automatically_promote_evidence: Literal[False] = False

    @model_validator(mode="after")
    def validate_bundle(self):
        profile_ids = [p.profile_id for p in self.profiles]
        if len(profile_ids) != len(set(profile_ids)):
            raise ValueError("profile ids must be unique")
        connector_ids = [p.connector_id for p in self.profiles]
        if len(connector_ids) != len(set(connector_ids)):
            raise ValueError("v4.21.0 reference registry requires one canonical profile per connector")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def _assert_no_sensitive_parameters(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(part in normalized for part in SENSITIVE_PARAMETER_PARTS):
                raise ValueError(f"Credential-like execution parameter is forbidden: {key}")
            _assert_no_sensitive_parameters(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_sensitive_parameters(item)


def profile_requested_by(profile_id: str) -> str:
    return f"{REQUESTED_BY_PREFIX}{profile_id}"


def _latest_ecmwf_cycle(now: datetime) -> tuple[str, str]:
    aware = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
    candidate = aware.astimezone(timezone.utc) - timedelta(hours=8)
    run_hour = (candidate.hour // 6) * 6
    return candidate.strftime("%Y%m%d"), f"{run_hour:02d}"


_TOKEN = re.compile(r"\{\{([a-z0-9_-]+)\}\}")


def _token_value(token: str, now: datetime) -> str:
    aware = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
    aware = aware.astimezone(timezone.utc)

    if token == "today":
        return aware.date().isoformat()
    if token == "current_year":
        return str(aware.year)

    match = re.fullmatch(r"year_minus_(\d+)", token)
    if match:
        return str(aware.year - int(match.group(1)))

    match = re.fullmatch(r"date_minus_(\d+)d", token)
    if match:
        return (aware.date() - timedelta(days=int(match.group(1)))).isoformat()

    if token in {"ecmwf_date", "ecmwf_run"}:
        date, run = _latest_ecmwf_cycle(aware)
        return date if token == "ecmwf_date" else run

    raise ValueError(f"Unknown profile parameter token: {token}")


def _resolve(value: Any, now: datetime) -> Any:
    if isinstance(value, dict):
        return {key: _resolve(item, now) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve(item, now) for item in value]
    if not isinstance(value, str):
        return value

    matches = list(_TOKEN.finditer(value))
    if not matches:
        return value

    if len(matches) == 1 and matches[0].span() == (0, len(value)):
        return _token_value(matches[0].group(1), now)

    result = value
    for match in matches:
        result = result.replace(match.group(0), _token_value(match.group(1), now))
    return result


def resolve_profile_parameters(
    profile: ConnectorExecutionProfile,
    *,
    now: datetime | None = None,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    parameters = _resolve(dict(profile.parameters), now)
    parameters.update(dict(overrides or {}))
    _assert_no_sensitive_parameters(parameters)

    missing = [
        name
        for name in profile.required_parameters
        if parameters.get(name) is None
        or (isinstance(parameters.get(name), str) and not str(parameters.get(name)).strip())
    ]
    if missing:
        raise ValueError("Profile requires caller parameters: " + ", ".join(sorted(missing)))

    if profile.required_one_of and not any(
        parameters.get(name) is not None
        and (not isinstance(parameters.get(name), str) or str(parameters.get(name)).strip())
        for name in profile.required_one_of
    ):
        raise ValueError("Profile requires one of: " + ", ".join(profile.required_one_of))

    return parameters


def validate_profile_against_connector(
    profile: ConnectorExecutionProfile,
    connector,
    *,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if connector.id != profile.connector_id:
        raise ValueError("Profile connector identity mismatch.")

    params = dict(parameters or profile.parameters)
    config = dict(connector.configuration_json or {})
    required = list(config.get("required_parameters") or [])
    required_one = list(config.get("required_one_of") or [])

    missing = [
        key
        for key in required
        if params.get(key) is None
        or (isinstance(params.get(key), str) and not str(params.get(key)).strip())
    ]
    if missing:
        raise ValueError(
            f"Profile {profile.profile_id} missing required connector parameters: "
            + ", ".join(missing)
        )

    if required_one and not any(
        params.get(key) is not None
        and (not isinstance(params.get(key), str) or str(params.get(key)).strip())
        for key in required_one
    ):
        raise ValueError(
            f"Profile {profile.profile_id} must provide one of: " + ", ".join(required_one)
        )

    return {
        "profile_id": profile.profile_id,
        "connector_id": profile.connector_id,
        "required_parameters": required,
        "required_one_of": required_one,
        "valid": True,
    }


def validate_profile_contract_coverage(profile: ConnectorExecutionProfile, connector) -> dict[str, Any]:
    config = dict(connector.configuration_json or {})
    required = set(config.get("required_parameters") or [])
    required_one = set(config.get("required_one_of") or [])
    declared = set(profile.parameters) | set(profile.required_parameters)

    missing = sorted(required - declared)
    if missing:
        raise ValueError(
            f"Profile {profile.profile_id} does not declare connector requirements: "
            + ", ".join(missing)
        )

    if required_one:
        declared_one = set(profile.parameters) | set(profile.required_one_of)
        if not (required_one & declared_one):
            raise ValueError(
                f"Profile {profile.profile_id} does not cover connector one-of requirements: "
                + ", ".join(sorted(required_one))
            )

    return {"profile_id": profile.profile_id, "valid": True}


def _p(
    profile_id: str,
    connector_id: str,
    name: str,
    description: str,
    domain: str,
    mode: ProfileMode,
    parameters: dict[str, Any],
    refresh_policy: str,
    *,
    required_parameters: list[str] | None = None,
    required_one_of: list[str] | None = None,
    scheduler_eligible: bool = False,
    priority: int = 100,
    scope: dict[str, Any] | None = None,
    tags: list[str] | None = None,
) -> ConnectorExecutionProfile:
    return ConnectorExecutionProfile(
        profile_id=profile_id,
        connector_id=connector_id,
        display_name=name,
        description=description,
        domain=domain,
        mode=mode,
        parameters=parameters,
        required_parameters=list(required_parameters or []),
        required_one_of=list(required_one_of or []),
        refresh_policy=refresh_policy,
        scheduler_eligible=scheduler_eligible,
        priority=priority,
        scope=dict(scope or {}),
        tags=list(tags or []),
        provenance={
            "release": CORE_RELEASE,
            "authority": "platform-core-governed-profile-registry",
            "connector_contract_bound": True,
            "credentials_from_deployment_settings_only": True,
        },
    )


@lru_cache(maxsize=1)
def reference_connector_profile_contract() -> ConnectorProfileContract:
    profiles = [
        _p(
            "profile:met-no:point-forecast",
            "met-no.locationforecast",
            "MET Norway Point Forecast",
            "Reusable point-weather profile requiring caller latitude and longitude bindings.",
            "weather",
            ProfileMode.template,
            {},
            "PT1H",
            required_parameters=["lat", "lon"],
            scope={"geography": "caller-selected point"},
            tags=["weather", "forecast", "geospatial"],
        ),
        _p(
            "profile:world-bank:us-gdp-per-capita",
            "world-bank.indicators",
            "World Bank US GDP per Capita",
            "Recent United States GDP-per-capita observations from the World Bank Indicators API.",
            "economics",
            ProfileMode.scheduled,
            {
                "indicator": "NY.GDP.PCAP.CD",
                "country": "USA",
                "date": "{{year_minus_5}}:{{current_year}}",
                "per_page": 100,
            },
            "P1D",
            scheduler_eligible=True,
            priority=120,
            scope={"country": "USA", "indicator": "NY.GDP.PCAP.CD"},
            tags=["economics", "development", "gdp"],
        ),
        _p(
            "profile:fred:us-gdp",
            "fred.series-observations",
            "FRED United States GDP",
            "Recent United States GDP observations using deployment-managed FRED credentials.",
            "economics",
            ProfileMode.scheduled,
            {
                "series_id": "GDP",
                "observation_start": "{{year_minus_5}}-01-01",
                "limit": 200,
                "sort_order": "desc",
            },
            "P1D",
            scheduler_eligible=True,
            priority=130,
            scope={"country": "USA", "series": "GDP"},
            tags=["economics", "gdp", "fred"],
        ),
        _p(
            "profile:un-sdg:metadata-series",
            "un.sdg-metadata",
            "UN SDG Metadata Series",
            "Methodology profile requiring an official SDG series identifier selected by the caller.",
            "sustainability",
            ProfileMode.template,
            {},
            "P7D",
            required_parameters=["series"],
            scope={"series": "caller-selected official SDG series"},
            tags=["sdg", "methodology", "sustainability"],
        ),
        _p(
            "profile:un-population:indicator-window",
            "un.population-data",
            "UN Population Indicator Window",
            "Demographic profile requiring official indicator and location identifiers plus a bounded year window.",
            "demographics",
            ProfileMode.template,
            {},
            "P30D",
            required_parameters=["indicators", "locations", "start_year", "end_year"],
            scope={"geography": "caller-selected locations", "time": "caller-selected year window"},
            tags=["population", "demographics", "un"],
        ),
        _p(
            "profile:un-comtrade:us-total-trade",
            "un.comtrade",
            "UN Comtrade US Total Trade",
            "Bounded prior-year United States aggregate import and export profile using the public preview API.",
            "economics",
            ProfileMode.scheduled,
            {
                "reporter_code": "842",
                "period": "{{year_minus_1}}",
                "commodity_code": "TOTAL",
                "partner_code": "0",
                "flow_code": "X,M",
                "max_records": 100,
            },
            "P1D",
            scheduler_eligible=True,
            priority=180,
            scope={"reporter": "United States", "partner": "World", "commodity": "TOTAL"},
            tags=["trade", "imports", "exports"],
        ),
        _p(
            "profile:nasa-cmr:climate-collections",
            "nasa.cmr-collections",
            "NASA CMR Climate Collections",
            "Bounded discovery of NASA Earth-science collections matching the climate keyword.",
            "earth_science",
            ProfileMode.scheduled,
            {"keyword": "climate", "page_size": 50},
            "P1D",
            scheduler_eligible=True,
            priority=140,
            scope={"keyword": "climate", "page_size": 50},
            tags=["nasa", "earth-science", "climate"],
        ),
        _p(
            "profile:noaa-ncei:dataset-window",
            "noaa.ncei-data",
            "NOAA NCEI Dataset Window",
            "Climate-observation profile requiring a selected dataset and explicit bounded date window.",
            "earth_science",
            ProfileMode.template,
            {},
            "P1D",
            required_parameters=["dataset", "start_date", "end_date"],
            scope={"dataset": "caller-selected", "time": "caller-selected bounded window"},
            tags=["noaa", "climate", "observations"],
        ),
        _p(
            "profile:ecmwf:latest-operational-index",
            "ecmwf.open-data-index",
            "ECMWF Latest Operational Forecast Index",
            "Safely lagged ECMWF IFS operational zero-hour forecast-index profile.",
            "atmospheric_science",
            ProfileMode.scheduled,
            {
                "date": "{{ecmwf_date}}",
                "run": "{{ecmwf_run}}",
                "stream": "oper",
                "type": "fc",
                "step": 0,
                "model": "ifs",
                "resolution": "0p25",
            },
            "PT6H",
            scheduler_eligible=True,
            priority=60,
            scope={"model": "ifs", "stream": "oper", "step_hours": 0},
            tags=["ecmwf", "forecast", "atmosphere"],
        ),
        _p(
            "profile:usgs-water:bounded-selection",
            "usgs.water-instantaneous",
            "USGS Water Bounded Selection",
            "Hydrology profile requiring a caller-provided site list, state code, or bounding box.",
            "hydrology",
            ProfileMode.template,
            {"period": "P1D"},
            "PT15M",
            required_one_of=["sites", "state_cd", "b_box"],
            scope={"geography": "caller-selected bounded hydrologic geography"},
            tags=["usgs", "hydrology", "streamflow"],
        ),
        _p(
            "profile:imf:sdmx-series",
            "imf.sdmx",
            "IMF SDMX Series",
            "IMF profile requiring the configured free portal endpoint and caller-selected agency, dataset, and key.",
            "economics",
            ProfileMode.template,
            {},
            "P1D",
            required_parameters=["agency", "dataset", "key"],
            scope={"dataset": "caller-selected IMF SDMX flow"},
            tags=["imf", "macroeconomics", "sdmx"],
        ),
        _p(
            "profile:oecd:sdmx-series",
            "oecd.sdmx",
            "OECD SDMX Series",
            "OECD profile requiring caller-selected agency, dataset, and SDMX key.",
            "economics",
            ProfileMode.template,
            {},
            "P1D",
            required_parameters=["agency", "dataset", "key"],
            scope={"dataset": "caller-selected OECD Data Explorer flow"},
            tags=["oecd", "economics", "sdmx"],
        ),
        _p(
            "profile:eurostat:eu-population",
            "eurostat.statistics",
            "Eurostat EU Population",
            "Recent total-population observations for the EU27 aggregate from Eurostat.",
            "economics",
            ProfileMode.scheduled,
            {
                "dataset": "demo_pjan",
                "geo": "EU27_2020",
                "sex": "T",
                "age": "TOTAL",
                "sinceTimePeriod": "{{year_minus_3}}",
            },
            "PT12H",
            scheduler_eligible=True,
            priority=150,
            scope={"geo": "EU27_2020", "dataset": "demo_pjan"},
            tags=["eurostat", "population", "eu"],
        ),
        _p(
            "profile:ecb:usd-eur-reference-rate",
            "ecb.sdmx",
            "ECB USD/EUR Reference Rate",
            "Recent daily USD-per-EUR reference exchange-rate observations from the ECB Data Portal.",
            "finance",
            ProfileMode.scheduled,
            {
                "flow_ref": "EXR",
                "key": "D.USD.EUR.SP00.A",
                "startPeriod": "{{date_minus_45d}}",
                "endPeriod": "{{today}}",
            },
            "P1D",
            scheduler_eligible=True,
            priority=100,
            scope={"currency_pair": "USD/EUR", "frequency": "daily"},
            tags=["ecb", "finance", "exchange-rate"],
        ),
        _p(
            "profile:bis:sdmx-series",
            "bis.sdmx",
            "BIS SDMX Series",
            "BIS profile requiring a caller-selected flow reference and SDMX key.",
            "finance",
            ProfileMode.template,
            {},
            "P1D",
            required_parameters=["flow_ref", "key"],
            scope={"dataset": "caller-selected BIS dataflow"},
            tags=["bis", "finance", "sdmx"],
        ),
        _p(
            "profile:bea:nipa-table",
            "bea.statistics",
            "BEA NIPA Table",
            "BEA National Income and Product Accounts profile requiring an API key and explicit table/year selection.",
            "economics",
            ProfileMode.template,
            {"dataset_name": "NIPA", "Frequency": "A"},
            "P1D",
            required_parameters=["TableName", "Year"],
            scope={"dataset": "NIPA", "table": "caller-selected"},
            tags=["bea", "gdp", "national-accounts"],
        ),
        _p(
            "profile:bls:cpi-unemployment",
            "bls.timeseries",
            "BLS CPI and Unemployment",
            "Recent CPI-U and civilian unemployment-rate observations from the BLS public API.",
            "labour",
            ProfileMode.scheduled,
            {
                "series_ids": ["CUUR0000SA0", "LNS14000000"],
                "startyear": "{{year_minus_2}}",
                "endyear": "{{current_year}}",
                "catalog": True,
            },
            "P1D",
            scheduler_eligible=True,
            priority=110,
            scope={"country": "USA", "series": ["CUUR0000SA0", "LNS14000000"]},
            tags=["bls", "inflation", "unemployment"],
        ),
        _p(
            "profile:census:state-demographic-baseline",
            "census.data",
            "Census State Demographic Baseline",
            "Prior-year-safe ACS state population and median-household-income baseline profile.",
            "demographics",
            ProfileMode.scheduled,
            {
                "year": "{{year_minus_2}}",
                "dataset": "acs/acs1/profile",
                "get": "NAME,DP05_0001E,DP03_0062E",
                "for": "state:*",
            },
            "P30D",
            scheduler_eligible=True,
            priority=220,
            scope={"geography": "US states", "dataset": "ACS 1-year profile"},
            tags=["census", "population", "income"],
        ),
        _p(
            "profile:sec:company-facts",
            "sec.companyfacts",
            "SEC Company Facts",
            "Company-finance profile requiring a caller-selected SEC Central Index Key.",
            "company_finance",
            ProfileMode.template,
            {"taxonomy": "us-gaap", "limit_per_fact": 5},
            "P1D",
            required_parameters=["cik"],
            scope={"company": "caller-selected SEC registrant"},
            tags=["sec", "xbrl", "company-finance"],
        ),
        _p(
            "profile:eia:route-series",
            "eia.v2-data",
            "EIA Energy Route",
            "Energy profile requiring a configured free EIA key and caller-selected route and data fields.",
            "energy",
            ProfileMode.template,
            {},
            "P1D",
            required_parameters=["route", "data_fields"],
            scope={"dataset": "caller-selected EIA v2 route"},
            tags=["eia", "energy", "official-statistics"],
        ),
        _p(
            "profile:faostat:domain-series",
            "faostat.data",
            "FAOSTAT Domain Series",
            "Food-and-agriculture profile requiring a caller-selected FAOSTAT domain code and optional bounded filters.",
            "agriculture",
            ProfileMode.template,
            {},
            "P30D",
            required_parameters=["domain_code"],
            scope={"dataset": "caller-selected FAOSTAT domain"},
            tags=["fao", "agriculture", "food"],
        ),
        _p(
            "profile:ilostat:sdmx-series",
            "ilostat.sdmx",
            "ILOSTAT SDMX Series",
            "Labour-statistics profile requiring a caller-selected ILOSTAT flow reference and SDMX key.",
            "labour",
            ProfileMode.template,
            {},
            "P30D",
            required_parameters=["flow_ref", "key"],
            scope={"dataset": "caller-selected ILOSTAT dataflow"},
            tags=["ilo", "labour", "sdmx"],
        ),
    ]
    return ConnectorProfileContract(profiles=profiles)


def all_profiles() -> list[ConnectorExecutionProfile]:
    return list(reference_connector_profile_contract().profiles)


def get_profile(profile_id: str) -> ConnectorExecutionProfile | None:
    return next((profile for profile in all_profiles() if profile.profile_id == profile_id), None)


def scheduled_profiles() -> list[ConnectorExecutionProfile]:
    return [
        profile
        for profile in all_profiles()
        if profile.scheduler_eligible and profile.mode == ProfileMode.scheduled
    ]


def profile_contract_document() -> dict[str, Any]:
    bundle = reference_connector_profile_contract()
    scheduled = scheduled_profiles()
    templates = [profile for profile in bundle.profiles if profile.mode == ProfileMode.template]
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "predecessor_release": PREDECESSOR_RELEASE,
        "identity": {
            "product": "Sustainable Catalyst Platform Core",
            "build": "Parameterized Connector Execution Profiles",
            "major_api": "v4",
        },
        "reference": {
            "profile_count": len(bundle.profiles),
            "connector_count": len({profile.connector_id for profile in bundle.profiles}),
            "scheduler_eligible_count": len(scheduled),
            "template_count": len(templates),
            "domains": sorted({profile.domain for profile in bundle.profiles}),
            "bundle_fingerprint_sha256": bundle.fingerprint(),
        },
        "scheduler": {
            "disabled_by_default": True,
            "allowlist_supported": True,
            "profile_activity_isolated_by_requested_by": True,
            "zero_parameter_scheduler_preserved": True,
            "duplicate_active_profile_work_suppressed": True,
            "profile_refresh_policy_enforced": True,
        },
        "parameter_resolution": {
            "dynamic_tokens": [
                "{{today}}",
                "{{current_year}}",
                "{{year_minus_N}}",
                "{{date_minus_Nd}}",
                "{{ecmwf_date}}",
                "{{ecmwf_run}}",
            ],
            "credentials_resolved_from_deployment_settings_only": True,
            "credentials_persisted_in_profile_parameters": False,
        },
        "boundaries": {
            "profile_is_provider_request_contract_not_truth_claim": True,
            "execution_success_establishes_truth": False,
            "execution_success_auto_promotes_evidence": False,
            "template_profile_auto_executes": False,
            "profile_scope_implies_global_coverage": False,
            "manual_search_connectors_automated_by_this_release": False,
        },
        "database_migration": "none",
    }
