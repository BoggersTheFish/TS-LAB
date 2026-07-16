from __future__ import annotations

import copy
import re
from pathlib import Path

import pytest

from .conftest import EXAMPLE_DIR, FIXTURE_DIR, load_yaml

EXAMPLE_SCHEMAS = {
    "definition.example.yaml": "definition.schema.json",
    "assumption.example.yaml": "assumption.schema.json",
    "evidence_baseline.example.yaml": "evidence.schema.json",
    "evidence.example.yaml": "evidence.schema.json",
    "claim.example.yaml": "claim.schema.json",
    "obligation.example.yaml": "obligation.schema.json",
    "experiment.example.yaml": "experiment.schema.json",
    "result.example.yaml": "result.schema.json",
    "challenge.example.yaml": "challenge.schema.json",
    "decision.example.yaml": "decision.schema.json",
    "branch.example.yaml": "branch.schema.json",
    "transition_proposal.example.yaml": "transition_proposal.schema.json",
    "research_receipt.example.yaml": "research_receipt.schema.json",
}

INVALID_SCHEMAS = {
    "invalid_confidence_authority.yaml": "transition_proposal.schema.json",
    "invalid_missing_provenance.yaml": "evidence.schema.json",
    "invalid_self_approval.yaml": "transition_proposal.schema.json",
    "invalid_scope_broadening.yaml": "transition_proposal.schema.json",
    "invalid_unreplayable_receipt.yaml": "research_receipt.schema.json",
}


def messages(errors) -> str:
    return "\n".join(error.message for error in errors)


@pytest.mark.parametrize(("example_name", "schema_name"), EXAMPLE_SCHEMAS.items())
def test_every_example_validates(example_name, schema_name, validate_contract):
    schema_errors, contract_errors = validate_contract(
        schema_name, load_yaml(EXAMPLE_DIR / example_name)
    )
    assert schema_errors == [], messages(schema_errors)
    assert contract_errors == []


def test_every_object_schema_has_a_direct_valid_example():
    exercised = set(EXAMPLE_SCHEMAS.values())
    expected = {
        "definition.schema.json",
        "assumption.schema.json",
        "evidence.schema.json",
        "claim.schema.json",
        "obligation.schema.json",
        "experiment.schema.json",
        "result.schema.json",
        "challenge.schema.json",
        "decision.schema.json",
        "branch.schema.json",
        "transition_proposal.schema.json",
        "research_receipt.schema.json",
    }
    assert exercised == expected


def test_invalid_confidence_fails_at_authority_basis(validate_contract):
    data = load_yaml(FIXTURE_DIR / "invalid_confidence_authority.yaml")
    schema_errors, contract_errors = validate_contract("transition_proposal.schema.json", data)
    assert [list(error.absolute_path) for error in schema_errors] == [["authority_basis"]]
    assert "VERIFIER_AND_HUMAN_APPROVAL" in schema_errors[0].message
    assert contract_errors == []


def test_invalid_missing_provenance_fails_only_for_provenance(validate_contract):
    data = load_yaml(FIXTURE_DIR / "invalid_missing_provenance.yaml")
    schema_errors, contract_errors = validate_contract("evidence.schema.json", data)
    assert len(schema_errors) == 1
    assert schema_errors[0].message == "'provenance' is a required property"
    assert contract_errors == []


def test_invalid_self_approval_fails_identity_separation_only(validate_contract):
    data = load_yaml(FIXTURE_DIR / "invalid_self_approval.yaml")
    schema_errors, contract_errors = validate_contract("transition_proposal.schema.json", data)
    assert schema_errors == [], messages(schema_errors)
    assert [error.code for error in contract_errors] == ["GOV-NO-SELF-APPROVAL"]


def test_invalid_scope_broadening_fails_broadening_controls(validate_contract):
    data = load_yaml(FIXTURE_DIR / "invalid_scope_broadening.yaml")
    schema_errors, contract_errors = validate_contract("transition_proposal.schema.json", data)
    rendered = messages(schema_errors)
    assert "'new_supporting_evidence' is a required property" in rendered
    assert "'broader_scope_justification' is a required property" in rendered
    assert any(list(error.absolute_path) == ["human_approval"] for error in schema_errors)
    assert any(list(error.absolute_path) == ["challenges_considered"] for error in schema_errors)
    assert any(
        list(error.absolute_path) == ["proposed_post_state_effects"]
        for error in schema_errors
    )
    assert contract_errors == []


def test_invalid_unreplayable_receipt_fails_only_missing_replay_contract(validate_contract):
    data = load_yaml(FIXTURE_DIR / "invalid_unreplayable_receipt.yaml")
    schema_errors, contract_errors = validate_contract("research_receipt.schema.json", data)
    rendered = messages(schema_errors)
    assert "'parent_canonical_state_hash' is a required property" in rendered
    assert "'replay_instructions' is a required property" in rendered
    assert "'deterministic_receipt_hash' is a required property" in rendered
    assert len(schema_errors) == 3
    assert contract_errors == []


def test_every_declared_invalid_fixture_is_covered():
    assert {path.name for path in FIXTURE_DIR.glob("*.yaml")} == set(INVALID_SCHEMAS)


def test_unknown_top_level_field_is_rejected(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "evidence.example.yaml")
    data["unexpected_authority_hint"] = True
    errors = validate_schema("evidence.schema.json", data)
    assert any("Additional properties are not allowed" in error.message for error in errors)


@pytest.mark.parametrize(
    "value",
    ["", " ", "\t", "\n", " \t\n ", "\u00a0", "\u2003", "\u2028", " \u00a0\t"],
)
def test_claim_statement_must_be_nonblank(value, validate_schema):
    data = load_yaml(EXAMPLE_DIR / "claim.example.yaml")
    data["statement"] = value
    assert validate_schema("claim.schema.json", data)


@pytest.mark.parametrize(
    ("schema_name", "example_name", "path"),
    [
        ("claim.schema.json", "claim.example.yaml", ("scope", "domain")),
        ("claim.schema.json", "claim.example.yaml", ("scope", "boundaries", 0)),
        ("claim.schema.json", "claim.example.yaml", ("does_not_establish", 0)),
        ("decision.schema.json", "decision.example.yaml", ("rationale",)),
        ("obligation.schema.json", "obligation.example.yaml", ("precise_question",)),
        ("obligation.schema.json", "obligation.example.yaml", ("success_gates", 0, "criterion")),
        ("obligation.schema.json", "obligation.example.yaml", ("kill_gates", 0, "pass_condition")),
        ("challenge.schema.json", "challenge.example.yaml", ("statement",)),
        ("evidence.schema.json", "evidence.example.yaml", ("provenance", "method")),
    ],
)
def test_semantic_content_fields_reject_whitespace(
    schema_name, example_name, path, validate_schema
):
    data = load_yaml(EXAMPLE_DIR / example_name)
    target = data
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = " \t\n "
    assert validate_schema(schema_name, data)


def test_committed_claim_limitation_exception_requires_approving_human(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "claim.example.yaml")
    data["does_not_establish"] = []
    data["no_scope_exclusions_reason"] = "A fixture exception requiring explicit governance."
    data["limitation_exception_policy_approval"] = {
        "policy_id": "claim_policy",
        "rule_id": "CLAIM-LIMITATIONS-REQUIRED",
        "approved": True,
        "governance_record_id": "governance:fixture.exception",
    }
    data["approving_human_governance_record"] = copy.deepcopy(
        load_yaml(EXAMPLE_DIR / "decision.example.yaml")["human_approval"]
    )
    data["approving_human_governance_record"]["action"] = "REJECT"
    assert validate_schema("claim.schema.json", data)


def test_limitation_exception_governance_identity_is_a_test_validator_check(validate_contract):
    data = load_yaml(EXAMPLE_DIR / "claim.example.yaml")
    data["does_not_establish"] = []
    data["no_scope_exclusions_reason"] = "Explicit Phase 0 exception fixture."
    data["limitation_exception_policy_approval"] = {
        "policy_id": "claim_policy",
        "rule_id": "CLAIM-LIMITATIONS-REQUIRED",
        "approved": True,
        "governance_record_id": "governance:fixture.policy-record",
    }
    data["approving_human_governance_record"] = copy.deepcopy(
        load_yaml(EXAMPLE_DIR / "decision.example.yaml")["human_approval"]
    )
    schema_errors, contract_errors = validate_contract("claim.schema.json", data)
    assert schema_errors == []
    assert [error.code for error in contract_errors] == [
        "CLAIM-LIMITATION-GOVERNANCE-MISMATCH"
    ]


def test_assumption_commitment_requires_adoption_lineage_and_approval(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "assumption.example.yaml")
    data["transaction_state"] = "COMMITTED"
    errors = validate_schema("assumption.schema.json", data)
    rendered = messages(errors)
    assert "'parent_transition' is a required property" in rendered
    assert "'mandatory_transition_gates' is a required property" in rendered
    assert "'approving_human_governance_record' is a required property" in rendered
    assert any(list(error.absolute_path) == ["used_by"] for error in errors)
    assert any(list(error.absolute_path) == ["supporting_decisions"] for error in errors)
    assert any(list(error.absolute_path) == ["supporting_receipts"] for error in errors)


def test_committed_assumption_is_valid_only_as_scoped_adoption(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "assumption.example.yaml")
    data.update(
        {
            "transaction_state": "COMMITTED",
            "used_by": ["claim:fixture.depends-on-premise"],
            "supporting_decisions": ["decision:fixture.adopt-assumption"],
            "supporting_receipts": ["receipt:fixture.adopt-assumption"],
            "parent_transition": "transition:fixture.adopt-assumption",
            "mandatory_transition_gates": copy.deepcopy(
                load_yaml(EXAMPLE_DIR / "claim.example.yaml")["mandatory_transition_gates"]
            ),
            "approving_human_governance_record": copy.deepcopy(
                load_yaml(EXAMPLE_DIR / "decision.example.yaml")["human_approval"]
            ),
        }
    )
    assert validate_schema("assumption.schema.json", data) == []
    assert "epistemic_class" not in data


def test_branch_uses_lifecycle_not_transaction_or_epistemic_state(schemas, validate_schema):
    properties = schemas["branch.schema.json"]["properties"]
    assert "branch_lifecycle" in properties
    assert "transaction_state" not in properties
    assert "epistemic_class" not in properties
    data = load_yaml(EXAMPLE_DIR / "branch.example.yaml")
    data["transaction_state"] = "COMMITTED"
    assert validate_schema("branch.schema.json", data)


def test_nonproposed_branch_lifecycle_requires_decision_and_receipt_lineage(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "branch.example.yaml")
    data["branch_lifecycle"] = "ACTIVE"
    errors = validate_schema("branch.schema.json", data)
    assert any(list(error.absolute_path) == ["supporting_decisions"] for error in errors)
    assert any(list(error.absolute_path) == ["supporting_receipts"] for error in errors)
    assert "'lifecycle_transition' is a required property" in messages(errors)


def test_result_is_observation_only(schemas, validate_schema):
    properties = schemas["result.schema.json"]["properties"]
    forbidden = {
        "epistemic_class",
        "transaction_state",
        "approval",
        "approves_claims",
        "interpretation",
        "proof",
    }
    assert forbidden.isdisjoint(properties)
    for field, value in (
        ("epistemic_class", "ESTABLISHED"),
        ("transaction_state", "COMMITTED"),
        ("approves_claims", ["claim:dec24c.full-emergence"]),
        ("interpretation", "The target is true."),
    ):
        data = load_yaml(EXAMPLE_DIR / "result.example.yaml")
        data[field] = value
        assert validate_schema("result.schema.json", data)


def _failed_result() -> dict:
    data = load_yaml(EXAMPLE_DIR / "result.example.yaml")
    data["execution_outcome"] = "FAILED"
    data["outcome_reason"] = (
        "The execution stopped after retaining partial diagnostic observations."
    )
    data["failure_classification"] = "DECLARED_EXECUTION_FAILURE"
    data["observation_completeness"] = "PARTIAL"
    data["partial_observation_reason"] = "The declared execution did not complete."
    data["execution_observations"].append(
        "Execution failed after producing the retained artifact."
    )
    return data


def test_failed_result_can_produce_retained_evidence_without_promotion(validate_schema):
    data = _failed_result()
    assert data["evidence_produced"]
    assert validate_schema("result.schema.json", data) == []
    assert "epistemic_class" not in data
    assert "transaction_state" not in data


def test_failed_result_requires_failure_classification(validate_schema):
    data = _failed_result()
    data["failure_classification"] = None
    assert validate_schema("result.schema.json", data)


def test_completed_result_forbids_failure_classification(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "result.example.yaml")
    data["failure_classification"] = "NOT_A_FAILURE"
    assert validate_schema("result.schema.json", data)


def test_completed_execution_requires_environment_and_capture(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "result.example.yaml")
    data["environment"] = None
    errors = validate_schema("result.schema.json", data)
    assert any(list(error.absolute_path) == ["environment"] for error in errors)
    data = load_yaml(EXAMPLE_DIR / "result.example.yaml")
    data["execution_capture"] = None
    errors = validate_schema("result.schema.json", data)
    assert any(list(error.absolute_path) == ["execution_capture"] for error in errors)


def _not_run_result() -> dict:
    data = load_yaml(EXAMPLE_DIR / "result.example.yaml")
    data.update(
        {
            "execution_outcome": "NOT_RUN",
            "engineering_maturity": "SPECIFIED",
            "outcome_reason": (
                "Execution was not started because the declared fixture "
                "precondition was absent."
            ),
            "evidence_produced": [],
            "gate_observations": [],
            "execution_observations": [],
            "administrative_observations": [
                "The missing precondition was recorded without running the experiment."
            ],
            "comparisons": [],
            "observation_completeness": "NONE",
            "partial_observation_reason": None,
            "environment": None,
            "deterministic_seed": None,
            "nondeterminism_declaration": None,
            "tools_used": [],
            "execution_capture": None,
            "timeout_record": None,
            "unsupported_capability": None,
            "failure_classification": None,
        }
    )
    return data


def _unsupported_result() -> dict:
    data = _not_run_result()
    data.update(
        {
            "execution_outcome": "UNSUPPORTED",
            "outcome_reason": "The required fixture capability is unavailable.",
            "unsupported_capability": "exact-nullity fixture capability",
            "failure_classification": "UNSUPPORTED_CAPABILITY",
            "evidence_produced": [
                {
                    "evidence": {
                        "object_type": "Evidence",
                        "id": "evidence:fixture.missing-capability",
                        "canonical_hash": "sha256:" + "3" * 64,
                    },
                    "evidence_role": "CAPABILITY_DIAGNOSTIC",
                    "description": "Administrative record of the missing capability.",
                }
            ],
        }
    )
    return data


def test_not_run_result_can_record_only_administrative_nonexecution_facts(validate_schema):
    assert validate_schema("result.schema.json", _not_run_result()) == []


def test_unsupported_result_can_emit_only_typed_capability_diagnostic(validate_schema):
    assert validate_schema("result.schema.json", _unsupported_result()) == []


@pytest.mark.parametrize(
    "mutation,expected_path",
    [
        ("comparison", ["comparisons"]),
        ("pass_gate", ["gate_observations"]),
        ("evidence", ["evidence_produced"]),
        ("execution_observation", ["execution_observations"]),
    ],
)
def test_not_run_cannot_claim_execution_derived_facts(
    mutation, expected_path, validate_schema
):
    source = load_yaml(EXAMPLE_DIR / "result.example.yaml")
    data = _not_run_result()
    if mutation == "comparison":
        data["comparisons"] = copy.deepcopy(source["comparisons"])
    elif mutation == "pass_gate":
        gate = copy.deepcopy(source["gate_observations"][0])
        gate["outcome"] = "PASS"
        data["gate_observations"] = [gate]
    elif mutation == "evidence":
        data["evidence_produced"] = copy.deepcopy(source["evidence_produced"])
    else:
        data["execution_observations"] = ["An execution-derived observation."]
    errors = validate_schema("result.schema.json", data)
    assert any(list(error.absolute_path) == expected_path for error in errors)


@pytest.mark.parametrize("mutation", ["comparison", "pass_gate", "scientific_evidence"])
def test_unsupported_cannot_claim_scientific_execution_facts(mutation, validate_schema):
    source = load_yaml(EXAMPLE_DIR / "result.example.yaml")
    data = _unsupported_result()
    if mutation == "comparison":
        data["comparisons"] = copy.deepcopy(source["comparisons"])
        expected = ["comparisons"]
    elif mutation == "pass_gate":
        gate = copy.deepcopy(source["gate_observations"][0])
        gate["outcome"] = "PASS"
        data["gate_observations"] = [gate]
        expected = ["gate_observations"]
    else:
        data["evidence_produced"][0]["evidence_role"] = "SCIENTIFIC_EXECUTION"
        expected = ["evidence_produced", 0, "evidence_role"]
    errors = validate_schema("result.schema.json", data)
    assert any(list(error.absolute_path) == expected for error in errors)


def test_timed_out_result_requires_timeout_record_and_partial_markers(validate_schema):
    data = _failed_result()
    data["execution_outcome"] = "TIMED_OUT"
    data["failure_classification"] = "TIMEOUT"
    data["timeout_record"] = {
        "configured_timeout_seconds": 600,
        "elapsed_seconds": 600,
        "timed_out_at": "2026-01-01T00:12:00Z",
        "termination_reason": "The declared wall-time limit was reached.",
    }
    for gate in data["gate_observations"]:
        gate["observation_status"] = "PARTIAL"
    for record in data["evidence_produced"]:
        record["evidence_role"] = "PARTIAL_EXECUTION"
    assert validate_schema("result.schema.json", data) == []
    data["timeout_record"] = None
    errors = validate_schema("result.schema.json", data)
    assert any(list(error.absolute_path) == ["timeout_record"] for error in errors)


def test_cancelled_result_uses_failure_and_partial_contract(validate_schema):
    data = _failed_result()
    data["execution_outcome"] = "CANCELLED"
    data["failure_classification"] = "OPERATOR_CANCELLATION"
    assert validate_schema("result.schema.json", data) == []


def test_execution_capture_not_applicable_requires_nonblank_reason(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "result.example.yaml")
    data["execution_capture"]["stdout"] = {
        "capture_status": "NOT_APPLICABLE",
        "artifact": None,
        "reason": " ",
    }
    errors = validate_schema("result.schema.json", data)
    assert any(
        list(error.absolute_path) == ["execution_capture", "stdout", "reason"]
        for error in errors
    )


@pytest.mark.parametrize(
    ("schema_name", "example_name"),
    [
        ("experiment.schema.json", "experiment.example.yaml"),
        ("result.schema.json", "result.example.yaml"),
        ("evidence.schema.json", "evidence.example.yaml"),
    ],
)
def test_null_seed_requires_nondeterminism_declaration(schema_name, example_name, validate_schema):
    data = load_yaml(EXAMPLE_DIR / example_name)
    data["deterministic_seed"] = None
    data["nondeterminism_declaration"] = None
    assert validate_schema(schema_name, data)


def test_tool_binding_is_direct_and_legacy_parallel_versions_are_rejected(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "result.example.yaml")
    data["tool_versions"] = [{"name": "unrelated-tool", "version": "1"}]
    assert validate_schema("result.schema.json", data)
    del data["tool_versions"]
    del data["tools_used"][0]["implementation_hash"]
    errors = validate_schema("result.schema.json", data)
    assert any(list(error.absolute_path) == ["tools_used", 0] for error in errors)


def test_external_documentary_evidence_does_not_require_execution_fields(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "evidence_baseline.example.yaml")
    assert "environment" not in data
    assert "tools_used" not in data
    assert validate_schema("evidence.schema.json", data) == []


def test_capability_diagnostic_evidence_is_structurally_distinct_from_scientific_execution(
    validate_schema,
):
    data = load_yaml(EXAMPLE_DIR / "evidence_baseline.example.yaml")
    data["evidence_classification"] = "CAPABILITY_DIAGNOSTIC"
    data["evidence_kind"] = "MISSING_CAPABILITY_RECORD"
    assert validate_schema("evidence.schema.json", data) == []

    data["evidence_classification"] = "SCIENTIFIC_EXECUTION"
    errors = validate_schema("evidence.schema.json", data)
    rendered = messages(errors)
    assert "'environment' is a required property" in rendered
    assert "'execution_capture' is a required property" in rendered


@pytest.mark.parametrize("field", ["comparisons", "successful_gate_results"])
def test_diagnostic_evidence_cannot_smuggle_scientific_result_fields(
    field, validate_schema
):
    data = load_yaml(EXAMPLE_DIR / "evidence_baseline.example.yaml")
    data["evidence_classification"] = "CAPABILITY_DIAGNOSTIC"
    data[field] = [{"outcome": "PASS"}]
    errors = validate_schema("evidence.schema.json", data)
    assert any("Additional properties are not allowed" in error.message for error in errors)


@pytest.mark.parametrize(
    "timestamp",
    [
        "",
        "not-a-date",
        "2026-02-30T00:00:00Z",
        "2026-01-01T00:00:00",
        "2026-01-01T00:00:00+00:00",
        "2026-01-01T00:00:00z",
    ],
)
def test_invalid_or_noncanonical_timestamps_are_rejected(timestamp, validate_schema):
    data = load_yaml(EXAMPLE_DIR / "evidence.example.yaml")
    data["created_at"] = timestamp
    assert validate_schema("evidence.schema.json", data)


@pytest.mark.parametrize(
    "uri",
    ["", "relative/path", "http://[invalid", "1http:invalid", "not a uri"],
)
def test_malformed_or_nonabsolute_source_uris_are_rejected(uri, validate_schema):
    data = load_yaml(EXAMPLE_DIR / "evidence_baseline.example.yaml")
    data["source_uri"] = uri
    assert validate_schema("evidence.schema.json", data)


@pytest.mark.parametrize(
    "uri",
    [
        "https://example.com/evidence",
        "file:///tmp/fixture-evidence",
        "mailto:user@example.com",
        "urn:example:ts-lab:object",
    ],
)
def test_all_valid_absolute_uri_forms_are_accepted(uri, validate_schema):
    data = load_yaml(EXAMPLE_DIR / "evidence_baseline.example.yaml")
    data["source_uri"] = uri
    assert validate_schema("evidence.schema.json", data) == []


def _no_change_receipt() -> dict:
    data = load_yaml(EXAMPLE_DIR / "research_receipt.example.yaml")
    data["decision"] = {
        "decision_id": "decision:fixture.no-change",
        "verdict": "NO_CANONICAL_CHANGE",
        "rationale": "Record the outcome without a canonical change.",
    }
    data["post_state_hash"] = None
    data["transition_authorized"] = False
    data["canonical_state_committed"] = False
    data["replay_result"] = {
        "outcome": "NOT_RUN",
        "replayed_at": None,
        "observed_post_state_hash": None,
        "details": "No canonical transition was authorized.",
    }
    return data


@pytest.mark.parametrize(
    "updates",
    [
        {
            "execution_completed": True,
            "evidence_recorded": True,
            "verifier_obligation_satisfied": False,
        },
        {
            "execution_completed": False,
            "evidence_recorded": True,
            "verifier_obligation_satisfied": False,
        },
        {
            "execution_completed": True,
            "evidence_recorded": False,
            "verifier_obligation_satisfied": True,
        },
    ],
)
def test_no_change_receipts_keep_execution_evidence_and_verification_independent(
    updates, validate_schema
):
    data = _no_change_receipt()
    data.update(updates)
    if not data["evidence_recorded"]:
        data["recorded_evidence"] = []
    assert validate_schema("research_receipt.schema.json", data) == []


def test_authorized_transition_can_await_replay_and_commit(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "research_receipt.example.yaml")
    data["canonical_state_committed"] = False
    data["post_state_hash"] = None
    data["replay_result"] = {
        "outcome": "NOT_RUN",
        "replayed_at": None,
        "observed_post_state_hash": None,
        "details": "Authorization is recorded before replay and canonical commitment.",
    }
    assert validate_schema("research_receipt.schema.json", data) == []


def test_typed_hashes_have_contract_shape():
    pattern = re.compile(r"^sha256:[0-9a-f]{64}$")
    for example in EXAMPLE_SCHEMAS:
        text = (EXAMPLE_DIR / example).read_text(encoding="utf-8")
        for token in re.findall(r"sha256:[0-9a-f]+", text):
            assert pattern.fullmatch(token), f"invalid hash token in {example}: {token}"


def test_all_expected_example_files_are_present():
    assert {path.name for path in Path(EXAMPLE_DIR).glob("*.yaml")} == set(EXAMPLE_SCHEMAS)
