from __future__ import annotations

from .conftest import EXAMPLE_DIR, load_yaml


def fixture(name: str):
    return load_yaml(EXAMPLE_DIR / name)


def test_dec24c_reference_chain_preserves_improvement_and_failed_gates():
    experiment = fixture("experiment.example.yaml")
    result = fixture("result.example.yaml")
    baseline = fixture("evidence_baseline.example.yaml")
    evidence = fixture("evidence.example.yaml")

    assert result["experiment"] == experiment["id"]
    assert experiment["execution_outcome"] == "COMPLETED"
    assert result["execution_outcome"] == "COMPLETED"
    assert result["comparisons"] == [
        {
            "metric": "Declared target metric",
            "baseline_evidence": baseline["id"],
            "relation": "IMPROVED",
            "description": result["comparisons"][0]["description"],
        }
    ]
    assert set(result["comparisons"][0]) == {
        "metric",
        "baseline_evidence",
        "relation",
        "description",
    }
    outcomes = {item["gate_id"]: item["outcome"] for item in result["gate_observations"]}
    assert outcomes == {
        "gate:exact-gauge-nullity": "FAIL",
        "gate:leakage-required-threshold": "FAIL",
    }
    assert result["evidence_produced"] == [
        {
            "evidence": {
                "object_type": "Evidence",
                "id": evidence["id"],
                "canonical_hash": evidence["canonical_hash"],
            },
            "evidence_role": "NEGATIVE_DIAGNOSTIC",
            "description": result["evidence_produced"][0]["description"],
        }
    ]
    assert evidence["evidence_classification"] == "NEGATIVE_DIAGNOSTIC"
    assert "epistemic_class" not in result
    assert "transaction_state" not in result
    assert "interpretation" not in result


def test_dec24c_failed_gates_become_retained_scoped_negative_knowledge():
    result = fixture("result.example.yaml")
    evidence = fixture("evidence.example.yaml")
    challenge = fixture("challenge.example.yaml")
    claim = fixture("claim.example.yaml")
    obligation = fixture("obligation.example.yaml")
    transition = fixture("transition_proposal.example.yaml")

    target = "claim:dec24c.full-emergence"
    assert evidence["id"] in {
        item["evidence"]["id"] for item in result["evidence_produced"]
    }
    assert challenge["disposition"] == "SUSTAINED"
    assert target in challenge["target_claims"]
    assert evidence["id"] in challenge["evidence_considered"]
    assert claim["epistemic_class"] == "NEGATIVE_DIAGNOSTIC"
    assert claim["transaction_state"] == "COMMITTED"
    assert evidence["id"] in claim["supported_by"]
    assert "full emergence Claim" in claim["does_not_establish"][-1]
    assert obligation["id"] in claim["open_obligations"]
    assert obligation["blocked_claims"] == [target]

    effects = {
        (effect["action"], effect["object"]["id"])
        for effect in transition["proposed_post_state_effects"]
    }
    assert ("COMMIT", claim["id"]) in effects
    assert ("REJECT", target) in effects
    assert ("RETAIN", evidence["id"]) in effects
    assert ("CREATE", obligation["id"]) in effects
    assert ("COMMIT", target) not in effects


def test_dec24c_decision_and_receipt_authorize_only_the_scoped_transition():
    decision = fixture("decision.example.yaml")
    transition = fixture("transition_proposal.example.yaml")
    receipt = fixture("research_receipt.example.yaml")
    claim = fixture("claim.example.yaml")

    assert decision["transition_proposal"] == transition["id"]
    assert decision["transition_type"] == transition["transition_type"]
    assert decision["version_transition"] == transition["version_transition"]
    assert decision["branch_lifecycle_change"] == transition["branch_lifecycle_change"]
    assert decision["verdict"] == "APPROVE"
    assert decision["human_approval"]["action"] == "APPROVE"
    assert all(
        result["outcome"] == "PASS"
        for result in decision["verifier_results"]
        if result["mandatory"]
    )
    assert receipt["decision"]["decision_id"] == decision["id"]
    assert receipt["proposed_transition_hash"] == transition["deterministic_proposal_hash"]
    assert claim["supporting_decisions"] == [decision["id"]]
    assert claim["supporting_receipts"] == [receipt["id"]]
    assert receipt["human_approval_record"]["action"] == "APPROVE"
    assert receipt["replay_result"]["outcome"] == "PASSED"
    assert receipt["replay_result"]["replayed_at"] is not None
    assert receipt["replay_result"]["observed_post_state_hash"] == receipt["post_state_hash"]
    assert [
        item["evidence"]["id"] for item in receipt["recorded_evidence"]
    ] == ["evidence:dec24c.fixture.leakage-observation"]

    five_events = [
        "execution_completed",
        "evidence_recorded",
        "verifier_obligation_satisfied",
        "transition_authorized",
        "canonical_state_committed",
    ]
    assert all(receipt[event] is True for event in five_events)
    assert len(five_events) == len(set(five_events))


def test_dec24c_fixture_uses_no_fabricated_measurement_fields():
    result = fixture("result.example.yaml")
    evidence = fixture("evidence.example.yaml")
    baseline = fixture("evidence_baseline.example.yaml")

    forbidden_measurement_keys = {
        "value",
        "measured_value",
        "baseline_value",
        "delta",
        "magnitude",
        "threshold_value",
        "leakage_value",
    }
    for comparison in result["comparisons"]:
        assert forbidden_measurement_keys.isdisjoint(comparison)
    assert evidence["extensions"]["org.ts-lab.fixture"]["empirical_value_present"] is False
    assert baseline["extensions"]["org.ts-lab.fixture"]["empirical_value_present"] is False


def test_assumption_and_branch_examples_do_not_launder_epistemic_commitment():
    assumption = fixture("assumption.example.yaml")
    branch = fixture("branch.example.yaml")

    assert assumption["transaction_state"] == "CANDIDATE"
    assert "epistemic_class" not in assumption
    assert assumption["does_not_establish"]
    assert branch["branch_lifecycle"] == "PROPOSED"
    assert "transaction_state" not in branch
    assert branch["merge_does_not_commit_contents"] is True


def test_dec24c_declares_exactly_two_test_only_external_nodes():
    transition = fixture("transition_proposal.example.yaml")
    metadata = transition["extensions"]["fixture.external_references"]
    assert metadata["fixture_only"] is True
    assert metadata["nodes"] == [
        {
            "id": "claim:dec24c.full-emergence",
            "role": "pre_existing_external_node",
        },
        {
            "id": "obligation:dec24c.fixture.reference-evaluation",
            "role": "pre_existing_external_node",
        },
    ]

    external_ids = {node["id"] for node in metadata["nodes"]}
    result = fixture("result.example.yaml")
    receipt = fixture("research_receipt.example.yaml")
    assert external_ids.isdisjoint(
        item["evidence"]["id"] for item in result["evidence_produced"]
    )
    assert external_ids.isdisjoint(
        item["evidence"]["id"] for item in receipt["recorded_evidence"]
    )
    assert external_ids.isdisjoint(fixture("claim.example.yaml")["supported_by"])


def test_dec24c_object_reference_graph_is_closed_except_declared_fixture_nodes():
    names = [
        "definition.example.yaml",
        "assumption.example.yaml",
        "evidence_baseline.example.yaml",
        "evidence.example.yaml",
        "claim.example.yaml",
        "obligation.example.yaml",
        "experiment.example.yaml",
        "result.example.yaml",
        "challenge.example.yaml",
        "decision.example.yaml",
        "branch.example.yaml",
        "transition_proposal.example.yaml",
        "research_receipt.example.yaml",
    ]
    documents = [fixture(name) for name in names]
    materialized = {document["id"] for document in documents}
    external = {
        node["id"]
        for node in fixture("transition_proposal.example.yaml")["extensions"][
            "fixture.external_references"
        ]["nodes"]
    }
    prefixes = tuple(
        f"{prefix}:"
        for prefix in (
            "definition",
            "assumption",
            "evidence",
            "claim",
            "obligation",
            "experiment",
            "result",
            "challenge",
            "decision",
            "branch",
            "transition",
            "receipt",
        )
    )

    def references(value):
        if isinstance(value, str) and value.startswith(prefixes):
            yield value
        elif isinstance(value, dict):
            for key, child in value.items():
                if key == "extensions":
                    continue
                yield from references(child)
        elif isinstance(value, list):
            for child in value:
                yield from references(child)

    unresolved = set().union(*(set(references(document)) for document in documents))
    assert unresolved - materialized == external
