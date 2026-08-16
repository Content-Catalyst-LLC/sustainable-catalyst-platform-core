from datetime import datetime, timezone

NOW = datetime(2026, 8, 14, tzinfo=timezone.utc)


def candidate(**overrides):
    data = {
        "record_family": "economic-statistic", "record_id": "r1", "concept": "population",
        "source_id": "world-bank", "publisher": "World Bank", "evidence_class": "harmonized-benchmark",
        "semantic_role": "structural-baseline", "geographic_scope": "PSE", "reference_period": "2025",
        "value_number": 5400000, "unit": "people",
    }
    data.update(overrides)
    return data


def post_reconcile(client, headers, candidates, concept="population", persist=True):
    r = client.post("/v1/country-evidence/reconcile", headers=headers, json={
        "country_code": "PSE", "concept": concept, "candidates": candidates, "persist": persist,
    })
    assert r.status_code == 200, r.text
    return r.json()


def test_release_readiness(client):
    assert client.get("/health").json()["version"] == "2.25.0"
    body = client.get("/v1/country-evidence/readiness").json()
    assert body["release"] == "2.25.0"
    assert body["migration_0015_applied"] is True
    assert body["exact_concept_required"] is True
    assert body["automatic_averaging"] is False
    assert body["subnational_scope_can_replace_national"] is False
    assert body["knowledge_context_truth_precedence"] == "excluded"


def test_primary_official_beats_harmonized_benchmark(client, write_headers):
    pcbs = candidate(record_id="pcbs", source_id="pcbs", publisher="Palestinian Central Bureau of Statistics", evidence_class="official-statistic", value_number=5550000)
    wb = candidate(record_id="wb")
    body = post_reconcile(client, write_headers, [wb, pcbs])
    assert body["selected"]["record_id"] == "pcbs"
    assert body["selected"]["authority_role"] == "primary-official"
    assert body["automatic_averaging"] is False
    assert body["decision_state"] == "material-discrepancy"


def test_missing_official_source_is_explicit_fallback(client, write_headers):
    body = post_reconcile(client, write_headers, [candidate(record_id="wb")], persist=False)
    assert body["selected"]["record_id"] == "wb"
    assert body["preferred_official_candidate_present"] is False
    assert body["rationale"]["fallback_reason"] == "preferred-official-source-not-in-candidate-set"


def test_gaza_scope_never_substitutes_for_palestine_national(client, write_headers):
    national = candidate(record_id="national", source_id="pcbs", publisher="PCBS", evidence_class="official-statistic", geographic_scope="PSE")
    gaza = candidate(record_family="humanitarian-condition", record_id="gaza", source_id="ocha-hdx-hapi", publisher="OCHA", authority_role="operational-authority", semantic_role="structural-baseline", geographic_scope="PSE-GZA", value_number=3000000)
    body = post_reconcile(client, write_headers, [gaza, national], persist=False)
    assert body["selected"]["record_id"] == "national"
    assert body["incompatible_candidate_count"] == 1
    assert body["decision_state"] == "scope-or-semantics-differ"
    assert body["rationale"]["subnational_scope_never_substitutes_for_national_scope"] is True


def test_structural_and_operational_evidence_do_not_blend(client, write_headers):
    structural = candidate(record_id="access", concept="electricity", value_number=100, unit="percent")
    operational = candidate(record_family="humanitarian-condition", record_id="outage", concept="electricity", source_id="ocha-hdx-hapi", publisher="OCHA", semantic_role="operational-condition", evidence_class="operational-reporting", status_value="service-unavailable", value_number=None, unit=None)
    body = post_reconcile(client, write_headers, [structural, operational], concept="electricity", persist=False)
    assert body["do_not_blend"] is True
    assert body["incompatible_candidate_count"] == 1
    assert body["rationale"]["structural_baselines_never_substitute_for_operational_conditions"] is True


def test_different_reference_periods_are_not_discrepancies(client, write_headers):
    a = candidate(record_id="2024", source_id="pcbs", publisher="PCBS", evidence_class="official-statistic", reference_period="2024", value_number=5300000)
    b = candidate(record_id="2025", source_id="pcbs", publisher="PCBS", evidence_class="official-statistic", reference_period="2025", value_number=5400000)
    body = post_reconcile(client, write_headers, [a, b], persist=False)
    assert body["decision_state"] == "different-reference-period"
    assert body["discrepancies"] == []
    assert body["rationale"]["different_reference_periods_are_not_conflicts"] is True


def test_exact_concept_required(client, write_headers):
    body = post_reconcile(client, write_headers, [candidate(concept="gdp")], concept="population", persist=False)
    assert body["decision_state"] == "no-comparable-candidates"
    assert body["selected"] is None


def test_reconciliation_audit_is_idempotent(client, write_headers):
    items = [candidate(record_id="wb")]
    a = post_reconcile(client, write_headers, items)
    b = post_reconcile(client, write_headers, items)
    assert a["audit"]["id"] == b["audit"]["id"]
    rows = client.get("/v1/country-evidence/reconciliations?country_code=PSE").json()
    assert rows["total"] == 1


def test_country_federation_keeps_lanes_separate(client, write_headers):
    client.post('/v1/humanitarian/conditions', headers=write_headers, json={
        'country_code':'PSE','service_domain':'electricity','condition_kind':'interruption',
        'semantic_role':'operational-condition','status_value':'service-unavailable',
        'observed_at':NOW.isoformat(),'publisher':'OCHA','source_id':'ocha-hdx-hapi','public':True,
    })
    client.post('/v1/humanitarian/conditions', headers=write_headers, json={
        'country_code':'PSE','service_domain':'electricity','condition_kind':'availability',
        'semantic_role':'structural-baseline','value_number':100,'unit':'percent',
        'observed_at':NOW.isoformat(),'publisher':'World Bank','evidence_class':'harmonized-benchmark','public':True,
    })
    body = client.get('/v1/country-evidence/country/PSE/federation').json()
    assert body['records'] == 2
    assert body['lanes']['operational'] == 1
    assert body['lanes']['harmonized_benchmark'] == 1
    assert body['automatic_blending'] is False
    assert body['structural_and_operational_evidence_kept_separate'] is True


def test_facility_evidence_is_counted_without_flattening(client, write_headers):
    f = client.post('/v1/facilities', headers=write_headers, json={'name':'Example Hospital','facility_type':'hospital','country_code':'PSE'}).json()
    client.post(f"/v1/facilities/{f['id']}/observations", headers=write_headers, json={
        'observation_kind':'operational-status','status_value':'partially-operational','observed_at':NOW.isoformat(),'publisher':'WHO'
    })
    body = client.get('/v1/country-evidence/country/PSE/federation').json()
    assert body['facilities'] == 1
    assert body['facility_observations'] == 1


def test_zero_records_remains_unknown_not_normal(client):
    body = client.get('/v1/country-evidence/country/SDN/federation').json()
    assert body['records'] == 0
    assert body['zero_records_implication'] == 'unknown-not-normal'
