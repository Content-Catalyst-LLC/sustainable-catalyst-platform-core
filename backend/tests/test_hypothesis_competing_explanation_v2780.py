from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def client(tmp_path):
    return TestClient(create_app(Settings(database_url="sqlite:///" + str(tmp_path / "h.db"))))


def project(c, visibility="public"):
    response = c.post(
        "/v1/research/projects",
        json={"data": {"title": "Competing Explanation Study", "project_key": "competing-explanation-study", "visibility": visibility}},
    )
    assert response.status_code == 200, response.text
    return response.json()["project"]["id"]


def test_readiness(tmp_path):
    c = client(tmp_path)
    data = c.get("/v1/research/hypotheses/readiness").json()
    assert data["release"] == "2.78.0"
    assert data["contract"] == "sc.research.hypothesis-competing-explanation.v1"
    assert data["migration_0082_applied"] is True
    assert data["descriptive_comparison_matrix_by_core"] is True
    assert data["rank_hypotheses_by_core"] is False
    assert data["select_best_hypothesis_by_core"] is False
    c.close()


def test_competing_explanation_roundtrip(tmp_path):
    c = client(tmp_path)
    pid = project(c)
    hs = c.post(
        f"/v1/research/hypotheses/projects/{pid}/sets",
        json={"data": {"hypothesis_set_key": "set-1", "title": "Competing explanations", "research_question_ref": "question:q1"}},
    )
    assert hs.status_code == 200, hs.text
    set_id = hs.json()["id"]

    h1 = c.post(
        f"/v1/research/hypotheses/sets/{set_id}/hypotheses",
        json={"data": {"hypothesis_key": "h1", "title": "Explanation A", "proposition": "Mechanism A explains the recorded finding.", "claim_refs": ["claim:a"], "finding_refs": ["finding:1"]}},
    )
    assert h1.status_code == 200, h1.text
    h1id = h1.json()["id"]
    h2 = c.post(
        f"/v1/research/hypotheses/sets/{set_id}/hypotheses",
        json={"data": {"hypothesis_key": "h2", "title": "Explanation B", "proposition": "Mechanism B explains the recorded finding.", "hypothesis_type": "alternative", "finding_refs": ["finding:1"]}},
    )
    assert h2.status_code == 200, h2.text
    h2id = h2.json()["id"]

    rel = c.post(
        f"/v1/research/hypotheses/sets/{set_id}/relations",
        json={"data": {"relation_key": "h1-h2", "source_hypothesis_id": h1id, "target_hypothesis_id": h2id, "relationship": "alternative_to"}},
    )
    assert rel.status_code == 200, rel.text

    a1 = c.post(
        f"/v1/research/hypotheses/{h1id}/evidence-assessments",
        json={"data": {"assessment_key": "a1", "evidence_ref": "evidence:1", "relation": "supports", "declared_strength": "moderate", "assessment_basis": "Researcher-declared assessment."}},
    )
    assert a1.status_code == 200, a1.text
    a2 = c.post(
        f"/v1/research/hypotheses/{h2id}/evidence-assessments",
        json={"data": {"assessment_key": "a2", "evidence_ref": "evidence:1", "relation": "contradicts", "assessment_basis": "Researcher-declared assessment."}},
    )
    assert a2.status_code == 200, a2.text

    p1 = c.post(
        f"/v1/research/hypotheses/{h1id}/predictions",
        json={"data": {"prediction_key": "p1", "statement": "If H1 is applicable, observation O1 is expected.", "expected_observation": "O1", "disconfirming_observation": "O2", "status": "observed", "evidence_refs": ["evidence:2"]}},
    )
    assert p1.status_code == 200, p1.text
    p2 = c.post(
        f"/v1/research/hypotheses/{h2id}/predictions",
        json={"data": {"prediction_key": "p2", "statement": "If H2 is applicable, observation O2 is expected.", "expected_observation": "O2", "status": "not_observed", "evidence_refs": ["evidence:2"]}},
    )
    assert p2.status_code == 200, p2.text

    ass = c.post(
        f"/v1/research/hypotheses/{h1id}/assumptions",
        json={"data": {"assumption_key": "assumption-1", "assumption_text": "Measurement M is comparable across the study window.", "testability": "externally_testable"}},
    )
    assert ass.status_code == 200, ass.text

    gap = c.post(
        f"/v1/research/hypotheses/sets/{set_id}/discrimination-gaps",
        json={"data": {"gap_key": "gap-1", "title": "Distinguishing measurement", "question": "Which measurement would discriminate H1 from H2?", "hypothesis_ids": [h1id, h2id], "evidence_needed": ["independent measurement of O1 and O2"]}},
    )
    assert gap.status_code == 200, gap.text

    revision = c.post(
        f"/v1/research/hypotheses/{h1id}/revisions",
        json={"data": {"status": "qualified", "limitations": ["Applies only to the registered study window."], "change_summary": "Qualified scope."}},
    )
    assert revision.status_code == 200, revision.text
    assert revision.json()["revision"] == 1
    assert len(revision.json()["state_hash"]) == 64

    comparison = c.get(f"/v1/research/hypotheses/sets/{set_id}/comparison")
    assert comparison.status_code == 200, comparison.text
    matrix = comparison.json()
    assert len(matrix["rows"]) == 2
    assert matrix["comparison_is_descriptive_only"] is True
    assert matrix["scores_computed"] is False
    assert matrix["ranking_computed"] is False
    assert matrix["winner_selected"] is False
    by_key = {row["hypothesis_key"]: row for row in matrix["rows"]}
    assert by_key["h1"]["evidence_relation_counts"]["supports"] == 1
    assert by_key["h2"]["evidence_relation_counts"]["contradicts"] == 1
    assert by_key["h1"]["prediction_status_counts"]["observed"] == 1
    assert by_key["h2"]["prediction_status_counts"]["not_observed"] == 1

    s1 = c.post(f"/v1/research/hypotheses/sets/{set_id}/snapshots", json={"data": {}}).json()
    s2 = c.post(f"/v1/research/hypotheses/sets/{set_id}/snapshots", json={"data": {}}).json()
    assert s2["previous_snapshot_hash"] == s1["content_hash"]

    bundle = c.get(f"/v1/research/hypotheses/sets/{set_id}/bundle")
    assert bundle.status_code == 200, bundle.text
    data = bundle.json()
    assert len(data["hypotheses"]) == 2
    assert len(data["hypothesis_revisions"]) == 1
    assert len(data["evidence_assessments"]) == 2
    assert len(data["predictions"]) == 2
    assert len(data["assumptions"]) == 1
    assert len(data["hypothesis_relations"]) == 1
    assert len(data["discrimination_gaps"]) == 1
    assert len(data["snapshots"]) == 2
    assert data["rank_hypotheses_by_core"] is False
    c.close()


def test_boundaries(tmp_path):
    c = client(tmp_path)
    pid = project(c)
    hs = c.post(
        f"/v1/research/hypotheses/projects/{pid}/sets",
        json={"data": {"hypothesis_set_key": "set-boundary", "title": "Boundary test"}},
    )
    assert hs.status_code == 200
    set_id = hs.json()["id"]
    bad = c.post(
        f"/v1/research/hypotheses/sets/{set_id}/hypotheses",
        json={"data": {"hypothesis_key": "bad", "title": "Bad", "proposition": "Bad", "rank_hypotheses_by_core": True}},
    )
    assert bad.status_code == 422
    c.close()
