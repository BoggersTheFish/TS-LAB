from __future__ import annotations

import copy

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from .conftest import (
    CONSTITUTION_DIR,
    EXAMPLE_DIR,
    FIXTURE_DIR,
    effect_set_consistency_errors,
    load_yaml,
)

EXPECTED_BYPASS_CLASSIFICATIONS = {
    "authorize_through_confidence": "BLOCKED_BY_SCHEMA",
    "authorize_through_extension": "BLOCKED_BY_SCHEMA",
    "authorize_through_cased_extension": "BLOCKED_BY_SCHEMA",
    "producer_equals_human_approver": "CAUGHT_BY_TEST_VALIDATOR",
    "committed_claim_empty_scope": "BLOCKED_BY_SCHEMA",
    "committed_claim_empty_limitations": "BLOCKED_BY_SCHEMA",
    "committed_claim_supported_by_itself": "CAUGHT_BY_TEST_VALIDATOR",
    "broader_scope_same_classification": "BLOCKED_BY_SCHEMA",
    "broader_scope_local_evidence_overlap": "CAUGHT_BY_TEST_VALIDATOR",
    "broader_scope_historical_novelty": "DOCUMENTED_AS_FUTURE_VERIFIER",
    "commit_without_authorization": "BLOCKED_BY_SCHEMA",
    "authorization_without_human_approval": "BLOCKED_BY_SCHEMA",
    "mandatory_unknown_authorized": "BLOCKED_BY_SCHEMA",
    "failed_result_self_interpretation": "BLOCKED_BY_SCHEMA",
    "negative_evidence_destructive_effect": "BLOCKED_BY_SCHEMA",
    "negative_evidence_historical_reachability": "DOCUMENTED_AS_FUTURE_VERIFIER",
    "nested_extension_authority": "BLOCKED_BY_SCHEMA",
    "unknown_top_level_field": "BLOCKED_BY_SCHEMA",
    "malformed_canonical_hash": "BLOCKED_BY_SCHEMA",
    "passed_replay_without_instructions": "BLOCKED_BY_SCHEMA",
    "duplicate_object_effects": "CAUGHT_BY_TEST_VALIDATOR",
    "receipt_false_verifier_stage": "BLOCKED_BY_SCHEMA",
    "receipt_false_evidence_stage": "BLOCKED_BY_SCHEMA",
    "not_run_execution_claims": "BLOCKED_BY_SCHEMA",
    "unsupported_scientific_evidence": "BLOCKED_BY_SCHEMA",
    "hash_content_equality": "DOCUMENTED_AS_FUTURE_VERIFIER",
    "approval_authenticity": "DOCUMENTED_AS_FUTURE_VERIFIER",
}


def assert_schema_blocked(validate_schema, schema_name, data):
    errors = validate_schema(schema_name, data)
    assert errors, f"adversarial instance unexpectedly validated against {schema_name}"


def validate_with_schema_set(schemas, schema_name, instance):
    registry = Registry()
    for schema in schemas.values():
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    validator = Draft202012Validator(
        schemas[schema_name], registry=registry, format_checker=FormatChecker()
    )
    return list(validator.iter_errors(instance))


def authorized_uncommitted_receipt() -> dict:
    data = load_yaml(EXAMPLE_DIR / "research_receipt.example.yaml")
    data["canonical_state_committed"] = False
    data["post_state_hash"] = None
    data["replay_result"] = {
        "outcome": "NOT_RUN",
        "replayed_at": None,
        "observed_post_state_hash": None,
        "details": "Authorization is tested independently of replay and commitment.",
    }
    return data


def non_authorized_no_change_receipt() -> dict:
    data = authorized_uncommitted_receipt()
    data["decision"] = {
        "decision_id": "decision:fixture.no-change",
        "verdict": "NO_CANONICAL_CHANGE",
        "rationale": "Exercise an earlier receipt stage without authorization.",
    }
    data["human_approval_record"] = None
    data["transition_authorized"] = False
    return data


def test_no_audit_bypass_is_classified_currently_succeeds():
    assert "CURRENTLY_SUCCEEDS" not in EXPECTED_BYPASS_CLASSIFICATIONS.values()
    assert set(EXPECTED_BYPASS_CLASSIFICATIONS.values()) == {
        "BLOCKED_BY_SCHEMA",
        "CAUGHT_BY_TEST_VALIDATOR",
        "DOCUMENTED_AS_FUTURE_VERIFIER",
    }


def test_confidence_cannot_authorize_a_transition(validate_schema):
    data = load_yaml(FIXTURE_DIR / "invalid_confidence_authority.yaml")
    assert_schema_blocked(validate_schema, "transition_proposal.schema.json", data)


@pytest.mark.parametrize(
    "extensions",
    [
        {"org.authorization": True},
        {"org.authorisation": "granted"},
        {"org.authoritative": True},
        {"org.proves": "target"},
        {"Org.safe": {"value": True}},
        {"org.safe": {"approval": True}},
        {"org.safe": {"safe": {"authorisation": True}}},
        {"org.safe": {"safe": [{"deeper": {"proves": True}}]}},
        {"org.safe": {"safe": "SELF_AUTHORIZED"}},
        {"org.safe": {"safe": "canonical commitment granted"}},
        {"org.safe": {"safe": "ESTABLISHED"}},
        {"org.safe": {"safe": "PASS"}},
    ],
)
def test_extension_authority_aliases_are_recursively_rejected(extensions, validate_schema):
    data = load_yaml(EXAMPLE_DIR / "evidence_baseline.example.yaml")
    data["extensions"] = extensions
    assert_schema_blocked(validate_schema, "evidence.schema.json", data)


@pytest.mark.parametrize(
    "alias",
    [
        "authority",
        "authorization",
        "authorisation",
        "authorized",
        "authorised",
        "authoritative",
        "approve",
        "approval",
        "commit",
        "commitment",
        "canonical",
        "decision",
        "epistemic",
        "proof",
        "proves",
        "proven",
        "truth",
        "verifier",
        "verified",
        "transition",
        "status",
        "human_approval",
    ],
)
def test_extension_reserved_aliases_fail_as_namespace_key_nested_key_and_value(
    alias, validate_schema
):
    base = load_yaml(EXAMPLE_DIR / "evidence_baseline.example.yaml")
    variants = [
        {f"org.{alias}": True},
        {"org.safe": {"level-one": {"level_two": {alias: True}}}},
        {"org.safe": {"level-one": [{"level_two": [f"declared {alias}"]}]}},
        {"org.safe": {"level-one": {"level_two": alias.upper()}}},
    ]
    for extensions in variants:
        data = copy.deepcopy(base)
        data["extensions"] = extensions
        assert_schema_blocked(validate_schema, "evidence.schema.json", data)


def test_deep_harmless_lowercase_extension_metadata_remains_valid(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "evidence_baseline.example.yaml")
    nested = {"leaf": ["fixture note", 3, False, None]}
    for depth in range(7):
        nested = {f"level-{depth}": nested}
    data["extensions"] = {"org.fixture": nested}
    assert validate_schema("evidence.schema.json", data) == []


def test_producer_equals_human_approver_is_caught_by_phase0_helper(validate_contract):
    data = load_yaml(FIXTURE_DIR / "invalid_self_approval.yaml")
    schema_errors, contract_errors = validate_contract("transition_proposal.schema.json", data)
    assert schema_errors == []
    assert [error.code for error in contract_errors] == ["GOV-NO-SELF-APPROVAL"]


def test_verifier_cannot_validate_its_own_proposal_in_phase0_helper(validate_contract):
    data = load_yaml(EXAMPLE_DIR / "transition_proposal.example.yaml")
    data["producer"] = {
        "id": data["verifier"]["id"],
        "role": "TRANSITION_VERIFIER",
        "version": data["verifier"]["version"],
    }
    schema_errors, contract_errors = validate_contract("transition_proposal.schema.json", data)
    assert schema_errors == []
    assert [error.code for error in contract_errors] == [
        "GOV-NO-VERIFIER-SELF-APPROVAL"
    ]


def test_committed_claim_cannot_have_empty_scope(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "claim.example.yaml")
    data["scope"]["boundaries"] = []
    assert_schema_blocked(validate_schema, "claim.schema.json", data)


def test_committed_claim_cannot_have_empty_limitations_without_exception(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "claim.example.yaml")
    data["does_not_establish"] = []
    assert_schema_blocked(validate_schema, "claim.schema.json", data)


def test_claim_direct_self_dependency_is_caught_by_phase0_helper(validate_contract):
    data = load_yaml(EXAMPLE_DIR / "claim.example.yaml")
    data["depends_on"] = [data["id"]]
    schema_errors, contract_errors = validate_contract("claim.schema.json", data)
    assert schema_errors == []
    assert [error.code for error in contract_errors] == [
        "DEPENDENCY-DIRECT-SELF-CYCLE"
    ]


def test_broaden_transition_cannot_be_labelled_same_scope(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "transition_proposal.example.yaml")
    data["transition_type"] = "BROADEN_CLAIM_SCOPE"
    data["scope_change_classification"] = "SAME_SCOPE"
    data["new_supporting_evidence"] = ["evidence:fixture.new-support"]
    data["broader_scope_justification"] = "The fixture proposes a broader domain."
    assert_schema_blocked(validate_schema, "transition_proposal.schema.json", data)


def test_claim_transition_cannot_be_not_applicable(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "transition_proposal.example.yaml")
    data["scope_change_classification"] = "NOT_APPLICABLE"
    assert_schema_blocked(validate_schema, "transition_proposal.schema.json", data)


def test_locally_reused_evidence_cannot_be_relabelled_new(validate_contract):
    data = load_yaml(EXAMPLE_DIR / "transition_proposal.example.yaml")
    data["transition_type"] = "BROADEN_CLAIM_SCOPE"
    data["scope_change_classification"] = "BROADER_SCOPE"
    data["new_supporting_evidence"] = [data["evidence_considered"][0]]
    data["broader_scope_justification"] = "Fixture-only broader-domain explanation."
    data["version_transition"] = {
        "prior_object": {
            "object_type": "Claim",
            "id": data["proposed_post_state_effects"][0]["object"]["id"],
            "canonical_hash": "sha256:" + "1" * 64,
        },
        "replacement_object": copy.deepcopy(
            data["proposed_post_state_effects"][0]["object"]
        ),
        "relationship": "BROADER_SCOPE",
    }
    data["proposed_post_state_effects"] = [
        data["proposed_post_state_effects"][0],
        data["proposed_post_state_effects"][3],
    ]
    data["objects_affected"] = [
        effect["object"] for effect in data["proposed_post_state_effects"]
    ]
    schema_errors, contract_errors = validate_contract("transition_proposal.schema.json", data)
    assert schema_errors == []
    assert [error.code for error in contract_errors] == [
        "CLAIM-BROADENING-EVIDENCE-NOT-LOCALLY-DISTINCT"
    ]


def test_commit_cannot_precede_authorization(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "research_receipt.example.yaml")
    data["transition_authorized"] = False
    assert_schema_blocked(validate_schema, "research_receipt.schema.json", data)


@pytest.mark.parametrize("replacement", [None, "REJECT"])
def test_authorization_requires_explicit_human_approve(replacement, validate_schema):
    data = authorized_uncommitted_receipt()
    if replacement is None:
        data["human_approval_record"] = None
    else:
        data["human_approval_record"]["action"] = replacement
    assert_schema_blocked(validate_schema, "research_receipt.schema.json", data)


@pytest.mark.parametrize("outcome", ["UNKNOWN", "UNSUPPORTED", "ERROR", "MISSING", "FAIL"])
def test_authorized_receipt_fails_closed_on_mandatory_verifier_outcome(
    outcome, validate_schema
):
    data = authorized_uncommitted_receipt()
    data["verifier_results"][0]["outcome"] = outcome
    assert_schema_blocked(validate_schema, "research_receipt.schema.json", data)


def test_authorized_receipt_requires_satisfied_gate_summary(validate_schema):
    data = authorized_uncommitted_receipt()
    data["mandatory_gate_summary"]["all_satisfied"] = False
    data["mandatory_gate_summary"]["results"][0]["outcome"] = "UNKNOWN"
    assert_schema_blocked(validate_schema, "research_receipt.schema.json", data)


def test_verifier_stage_true_fails_closed_independently_of_authorization(validate_schema):
    data = non_authorized_no_change_receipt()
    data["verifier_obligation_satisfied"] = True
    data["verifier_results"][0]["outcome"] = "UNKNOWN"
    data["mandatory_gate_summary"]["all_satisfied"] = False
    data["mandatory_gate_summary"]["results"][0]["outcome"] = "UNKNOWN"
    errors = validate_schema("research_receipt.schema.json", data)
    paths = [list(error.absolute_path) for error in errors]
    assert any(path[:1] == ["verifier_results"] for path in paths)
    assert any(path[:1] == ["mandatory_gate_summary"] for path in paths)
    assert not any(path[:1] == ["transition_authorized"] for path in paths)
    assert not any(path[:1] == ["canonical_state_committed"] for path in paths)


def test_evidence_recorded_true_requires_typed_record_independently(validate_schema):
    data = non_authorized_no_change_receipt()
    data["evidence_recorded"] = True
    data["recorded_evidence"] = []
    errors = validate_schema("research_receipt.schema.json", data)
    assert [list(error.absolute_path) for error in errors] == [["recorded_evidence"]]


def test_evidence_recorded_false_forbids_canonical_record_assertions(validate_schema):
    data = non_authorized_no_change_receipt()
    data["evidence_recorded"] = False
    assert data["recorded_evidence"]
    errors = validate_schema("research_receipt.schema.json", data)
    assert [list(error.absolute_path) for error in errors] == [["recorded_evidence"]]


@pytest.mark.parametrize("field", ["replayed_at", "observed_post_state_hash"])
def test_passed_replay_requires_complete_observation(field, validate_schema):
    data = load_yaml(EXAMPLE_DIR / "research_receipt.example.yaml")
    data["replay_result"][field] = None
    assert_schema_blocked(validate_schema, "research_receipt.schema.json", data)


def test_canonical_commit_requires_post_state_hash(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "research_receipt.example.yaml")
    data["post_state_hash"] = None
    assert_schema_blocked(validate_schema, "research_receipt.schema.json", data)


@pytest.mark.parametrize("field", ["tools_used", "workers"])
def test_committed_receipt_requires_tool_and_worker_versions(field, validate_schema):
    data = load_yaml(EXAMPLE_DIR / "research_receipt.example.yaml")
    data[field] = []
    assert_schema_blocked(validate_schema, "research_receipt.schema.json", data)


def test_committed_receipt_requires_replay_artifacts(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "research_receipt.example.yaml")
    data["replay_instructions"]["required_artifacts"] = []
    assert_schema_blocked(validate_schema, "research_receipt.schema.json", data)


def test_bound_tool_record_cannot_be_satisfied_by_unrelated_version(validate_contract):
    data = load_yaml(EXAMPLE_DIR / "result.example.yaml")
    duplicate = copy.deepcopy(data["tools_used"][0])
    duplicate["version"] = "unrelated-version"
    duplicate["implementation_hash"] = "sha256:" + "3" * 64
    data["tools_used"].append(duplicate)
    schema_errors, contract_errors = validate_contract("result.schema.json", data)
    assert schema_errors == []
    assert [error.code for error in contract_errors] == ["TOOL-BINDING-CONFLICT"]


def test_receipt_producer_must_match_directly_bound_worker(validate_contract):
    data = load_yaml(EXAMPLE_DIR / "research_receipt.example.yaml")
    data["workers"][0]["version"] = "unrelated-version"
    schema_errors, contract_errors = validate_contract(
        "research_receipt.schema.json", data
    )
    assert schema_errors == []
    assert [error.code for error in contract_errors] == [
        "RECEIPT-PRODUCER-WORKER-MISMATCH"
    ]


def test_unrelated_worker_record_cannot_satisfy_receipt_producer(validate_contract):
    data = load_yaml(EXAMPLE_DIR / "research_receipt.example.yaml")
    data["workers"][0]["worker_id"] = "worker:unrelated-recorder"
    schema_errors, contract_errors = validate_contract(
        "research_receipt.schema.json", data
    )
    assert schema_errors == []
    assert [error.code for error in contract_errors] == [
        "RECEIPT-PRODUCER-WORKER-UNBOUND"
    ]


def test_duplicate_worker_id_with_conflicting_version_is_rejected(validate_contract):
    data = load_yaml(EXAMPLE_DIR / "research_receipt.example.yaml")
    duplicate = copy.deepcopy(data["workers"][0])
    duplicate["version"] = "conflicting-version"
    duplicate["implementation_hash"] = "sha256:" + "3" * 64
    data["workers"].append(duplicate)
    schema_errors, contract_errors = validate_contract(
        "research_receipt.schema.json", data
    )
    assert schema_errors == []
    assert [error.code for error in contract_errors] == ["WORKER-BINDING-CONFLICT"]


def test_committed_receipt_requires_bound_replay_worker(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "research_receipt.example.yaml")
    data["workers"] = [data["workers"][0]]
    errors = validate_schema("research_receipt.schema.json", data)
    assert any(list(error.absolute_path) == ["workers"] for error in errors)


def test_decision_approve_cannot_contradict_mandatory_verifier(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "decision.example.yaml")
    data["verifier_results"][0]["outcome"] = "UNKNOWN"
    errors = validate_schema("decision.schema.json", data)
    assert any(list(error.absolute_path)[:1] == ["verifier_results"] for error in errors)


def test_decision_approve_cannot_contradict_human_reject(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "decision.example.yaml")
    data["human_approval"]["action"] = "REJECT"
    errors = validate_schema("decision.schema.json", data)
    assert any(list(error.absolute_path)[:1] == ["human_approval"] for error in errors)


def test_decision_approve_cannot_contradict_mandatory_gate_summary(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "decision.example.yaml")
    data["mandatory_gate_summary"]["all_satisfied"] = False
    data["mandatory_gate_summary"]["results"][0]["outcome"] = "FAIL"
    errors = validate_schema("decision.schema.json", data)
    assert any(
        list(error.absolute_path)[:1] == ["mandatory_gate_summary"] for error in errors
    )


def test_decision_transition_type_is_coupled_to_decided_effects(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "decision.example.yaml")
    data["transition_type"] = "COMMIT_CLAIM"
    data["decided_effects"] = [
        effect for effect in data["decided_effects"] if effect["action"] == "CREATE"
    ]
    errors = validate_schema("decision.schema.json", data)
    assert any(list(error.absolute_path) == ["decided_effects", 0] for error in errors)
    assert any(list(error.absolute_path) == ["decided_effects"] for error in errors)


def test_result_cannot_interpret_failed_execution_as_proof(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "result.example.yaml")
    data["execution_outcome"] = "FAILED"
    data["failure_classification"] = "DECLARED_FAILURE"
    data["epistemic_class"] = "ESTABLISHED"
    data["transaction_state"] = "COMMITTED"
    data["proof"] = "The failed run proves the target."
    assert_schema_blocked(validate_schema, "result.schema.json", data)


def test_successful_result_also_cannot_promote_itself(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "result.example.yaml")
    data["transaction_state"] = "COMMITTED"
    assert_schema_blocked(validate_schema, "result.schema.json", data)


@pytest.mark.parametrize("action", ["RETRACT", "SUPERSEDE", "REJECT", "COMMIT"])
def test_evidence_effect_cannot_be_destructive_or_authoritative(action, validate_schema):
    data = load_yaml(EXAMPLE_DIR / "transition_proposal.example.yaml")
    evidence_effect = next(
        effect
        for effect in data["proposed_post_state_effects"]
        if effect["object"]["object_type"] == "Evidence"
    )
    evidence_effect["action"] = action
    assert_schema_blocked(validate_schema, "transition_proposal.schema.json", data)


def test_canonical_reference_couples_object_type_and_id_prefix(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "transition_proposal.example.yaml")
    data["objects_affected"][0]["id"] = "evidence:fixture.wrong-prefix"
    assert_schema_blocked(validate_schema, "transition_proposal.schema.json", data)


def test_duplicate_conflicting_effects_are_caught_by_phase0_helper(validate_contract):
    data = load_yaml(EXAMPLE_DIR / "transition_proposal.example.yaml")
    duplicate = copy.deepcopy(data["proposed_post_state_effects"][0])
    duplicate["action"] = "REJECT"
    duplicate["effect_hash"] = "sha256:" + "3" * 64
    data["proposed_post_state_effects"].append(duplicate)
    schema_errors, contract_errors = validate_contract("transition_proposal.schema.json", data)
    assert schema_errors == []
    assert [error.code for error in contract_errors] == [
        "EFFECT-SET-ACTION-CONFLICT"
    ]


def test_approving_decision_cannot_commit_and_reject_one_claim(validate_contract):
    data = load_yaml(EXAMPLE_DIR / "decision.example.yaml")
    duplicate = copy.deepcopy(data["decided_effects"][0])
    duplicate["action"] = "REJECT"
    duplicate["effect_hash"] = "sha256:" + "3" * 64
    data["decided_effects"].append(duplicate)
    schema_errors, contract_errors = validate_contract("decision.schema.json", data)
    assert schema_errors == []
    assert [error.code for error in contract_errors] == ["EFFECT-SET-ACTION-CONFLICT"]


@pytest.mark.parametrize(
    "schema_name,effect_field",
    [
        ("transition_proposal.schema.json", "proposed_post_state_effects"),
        ("decision.schema.json", "decided_effects"),
    ],
)
def test_same_id_and_action_with_different_version_hash_is_rejected(
    schema_name, effect_field, validate_contract
):
    example = (
        "transition_proposal.example.yaml"
        if schema_name.startswith("transition")
        else "decision.example.yaml"
    )
    data = load_yaml(EXAMPLE_DIR / example)
    duplicate = copy.deepcopy(data[effect_field][-1])
    duplicate["object"]["canonical_hash"] = "sha256:" + "3" * 64
    duplicate["effect_hash"] = "sha256:" + "4" * 64
    data[effect_field].append(duplicate)
    schema_errors, contract_errors = validate_contract(schema_name, data)
    assert schema_errors == []
    assert [error.code for error in contract_errors] == [
        "EFFECT-SET-CANONICAL-HASH-CONFLICT"
    ]


def test_same_stable_id_with_conflicting_object_types_is_rejected_by_shared_helper():
    instance = {
        "decided_effects": [
            {
                "action": "RETAIN",
                "object": {
                    "object_type": "Claim",
                    "id": "claim:fixture.same-id",
                    "canonical_hash": "sha256:" + "1" * 64,
                },
                "effect_description": "First typed target.",
                "effect_hash": "sha256:" + "2" * 64,
            },
            {
                "action": "RETAIN",
                "object": {
                    "object_type": "Evidence",
                    "id": "claim:fixture.same-id",
                    "canonical_hash": "sha256:" + "1" * 64,
                },
                "effect_description": "Conflicting typed target.",
                "effect_hash": "sha256:" + "2" * 64,
            },
        ]
    }
    assert [
        error.code
        for error in effect_set_consistency_errors("decision.schema.json", instance)
    ] == ["EFFECT-SET-OBJECT-TYPE-CONFLICT"]


@pytest.mark.parametrize(
    ("schema_name", "example_name", "field"),
    [
        ("decision.schema.json", "decision.example.yaml", "decided_effects"),
        (
            "transition_proposal.schema.json",
            "transition_proposal.example.yaml",
            "proposed_post_state_effects",
        ),
    ],
)
def test_duplicate_identical_effect_is_rejected_by_shared_schema(
    schema_name, example_name, field, validate_schema
):
    data = load_yaml(EXAMPLE_DIR / example_name)
    data[field].append(copy.deepcopy(data[field][-1]))
    errors = validate_schema(schema_name, data)
    assert len(errors) == 1
    assert list(errors[0].absolute_path) == [field]
    assert "non-unique" in errors[0].message


def test_conflicting_evidence_retain_versions_are_rejected(validate_contract):
    data = load_yaml(EXAMPLE_DIR / "decision.example.yaml")
    retained = copy.deepcopy(data["decided_effects"][-1])
    retained["object"]["canonical_hash"] = "sha256:" + "3" * 64
    retained["effect_hash"] = "sha256:" + "4" * 64
    data["decided_effects"].append(retained)
    schema_errors, contract_errors = validate_contract("decision.schema.json", data)
    assert schema_errors == []
    assert [error.code for error in contract_errors] == [
        "EFFECT-SET-CANONICAL-HASH-CONFLICT"
    ]


def test_same_target_effect_hash_conflict_is_rejected(validate_contract):
    data = load_yaml(EXAMPLE_DIR / "decision.example.yaml")
    duplicate = copy.deepcopy(data["decided_effects"][-1])
    duplicate["effect_description"] = "A second ambiguous description."
    duplicate["effect_hash"] = "sha256:" + "3" * 64
    data["decided_effects"].append(duplicate)
    schema_errors, contract_errors = validate_contract("decision.schema.json", data)
    assert schema_errors == []
    assert [error.code for error in contract_errors] == [
        "EFFECT-SET-EFFECT-HASH-CONFLICT"
    ]


def test_version_change_uses_explicit_prior_and_replacement_roles(validate_contract):
    data = load_yaml(EXAMPLE_DIR / "decision.example.yaml")
    replacement = copy.deepcopy(data["decided_effects"][0]["object"])
    prior = copy.deepcopy(replacement)
    prior["canonical_hash"] = "sha256:" + "3" * 64
    data["transition_type"] = "SUPERSEDE_CLAIM"
    data["decided_effects"] = [data["decided_effects"][0], data["decided_effects"][-1]]
    data["version_transition"] = {
        "prior_object": prior,
        "replacement_object": replacement,
        "relationship": "SUPERSEDES_CLAIM",
    }
    schema_errors, contract_errors = validate_contract("decision.schema.json", data)
    assert schema_errors == []
    assert contract_errors == []

    ambiguous_prior_effect = copy.deepcopy(data["decided_effects"][0])
    ambiguous_prior_effect["action"] = "COMMIT"
    ambiguous_prior_effect["object"] = prior
    ambiguous_prior_effect["effect_hash"] = "sha256:" + "4" * 64
    data["decided_effects"].append(ambiguous_prior_effect)
    schema_errors, contract_errors = validate_contract("decision.schema.json", data)
    assert any(list(error.absolute_path) == ["decided_effects"] for error in schema_errors)
    assert [error.code for error in contract_errors] == [
        "EFFECT-SET-CANONICAL-HASH-CONFLICT"
    ]


def test_branch_merge_cannot_commit_contained_claim(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "transition_proposal.example.yaml")
    branch_ref = {
        "object_type": "Branch",
        "id": "branch:fixture.dec24c-review",
        "canonical_hash": "sha256:" + "2" * 64,
    }
    data["transition_type"] = "MERGE_BRANCH"
    data["scope_change_classification"] = "NOT_APPLICABLE"
    data["branch_lifecycle_change"] = {
        "previous_state": "ACTIVE",
        "next_state": "MERGED",
    }
    data["objects_affected"] = [branch_ref]
    data["proposed_post_state_effects"] = [
        {
            "action": "MERGE",
            "object": branch_ref,
            "effect_description": "Merge only the Branch container.",
            "effect_hash": "sha256:" + "4" * 64,
        }
    ]
    assert validate_schema("transition_proposal.schema.json", data) == []
    data["proposed_post_state_effects"].append(
        {
            "action": "COMMIT",
            "object": {
                "object_type": "Claim",
                "id": "claim:fixture.contained",
                "canonical_hash": "sha256:" + "5" * 64,
            },
            "effect_description": "Illegally commit a contained Claim.",
            "effect_hash": "sha256:" + "6" * 64,
        }
    )
    assert_schema_blocked(validate_schema, "transition_proposal.schema.json", data)


@pytest.mark.parametrize(
    ("transition_type", "action", "previous_state", "next_state"),
    [
        ("CREATE_BRANCH", "CREATE", None, "PROPOSED"),
        ("OPEN_BRANCH", "OPEN", "PROPOSED", "OPEN"),
        ("ACTIVATE_BRANCH", "ACTIVATE", "OPEN", "ACTIVE"),
        ("ACTIVATE_BRANCH", "ACTIVATE", "FROZEN", "ACTIVE"),
        ("FREEZE_BRANCH", "FREEZE", "ACTIVE", "FROZEN"),
        ("MERGE_BRANCH", "MERGE", "ACTIVE", "MERGED"),
        ("MERGE_BRANCH", "MERGE", "FROZEN", "MERGED"),
        ("ABANDON_BRANCH", "ABANDON", "PROPOSED", "ABANDONED"),
        ("ABANDON_BRANCH", "ABANDON", "OPEN", "ABANDONED"),
        ("ABANDON_BRANCH", "ABANDON", "ACTIVE", "ABANDONED"),
        ("ABANDON_BRANCH", "ABANDON", "FROZEN", "ABANDONED"),
        ("CLOSE_BRANCH", "CLOSE", "MERGED", "CLOSED"),
        ("CLOSE_BRANCH", "CLOSE", "ABANDONED", "CLOSED"),
    ],
)
def test_branch_lifecycle_transitions_affect_only_branch(
    transition_type, action, previous_state, next_state, validate_schema
):
    data = load_yaml(EXAMPLE_DIR / "transition_proposal.example.yaml")
    branch_ref = {
        "object_type": "Branch",
        "id": "branch:fixture.lifecycle",
        "canonical_hash": "sha256:" + "7" * 64,
    }
    data["transition_type"] = transition_type
    data["scope_change_classification"] = "NOT_APPLICABLE"
    data["branch_lifecycle_change"] = {
        "previous_state": previous_state,
        "next_state": next_state,
    }
    data["objects_affected"] = [branch_ref]
    data["proposed_post_state_effects"] = [
        {
            "action": action,
            "object": branch_ref,
            "effect_description": "Change only the Branch container lifecycle.",
            "effect_hash": "sha256:" + "8" * 64,
        }
    ]
    assert validate_schema("transition_proposal.schema.json", data) == []


@pytest.mark.parametrize(
    ("transition_type", "action", "previous_state", "next_state"),
    [
        ("CREATE_BRANCH", "CREATE", "PROPOSED", "PROPOSED"),
        ("OPEN_BRANCH", "OPEN", "OPEN", "OPEN"),
        ("ACTIVATE_BRANCH", "ACTIVATE", "PROPOSED", "ACTIVE"),
        ("FREEZE_BRANCH", "FREEZE", "OPEN", "FROZEN"),
        ("MERGE_BRANCH", "MERGE", "PROPOSED", "MERGED"),
        ("ABANDON_BRANCH", "ABANDON", "MERGED", "ABANDONED"),
        ("CLOSE_BRANCH", "CLOSE", "ACTIVE", "CLOSED"),
    ],
)
def test_illegal_declared_branch_lifecycle_jump_is_rejected(
    transition_type, action, previous_state, next_state, validate_schema
):
    data = load_yaml(EXAMPLE_DIR / "transition_proposal.example.yaml")
    branch_ref = {
        "object_type": "Branch",
        "id": "branch:fixture.illegal-jump",
        "canonical_hash": "sha256:" + "7" * 64,
    }
    data.update(
        {
            "transition_type": transition_type,
            "scope_change_classification": "NOT_APPLICABLE",
            "branch_lifecycle_change": {
                "previous_state": previous_state,
                "next_state": next_state,
            },
            "objects_affected": [branch_ref],
            "proposed_post_state_effects": [
                {
                    "action": action,
                    "object": branch_ref,
                    "effect_description": "Attempt an illegal declared lifecycle jump.",
                    "effect_hash": "sha256:" + "8" * 64,
                }
            ],
        }
    )
    errors = validate_schema("transition_proposal.schema.json", data)
    assert any(list(error.absolute_path)[:1] == ["branch_lifecycle_change"] for error in errors)


def test_open_effect_is_branch_and_open_transition_only(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "transition_proposal.example.yaml")
    data["proposed_post_state_effects"][0]["action"] = "OPEN"
    assert_schema_blocked(validate_schema, "transition_proposal.schema.json", data)

    branch_ref = {
        "object_type": "Branch",
        "id": "branch:fixture.open-only",
        "canonical_hash": "sha256:" + "7" * 64,
    }
    data.update(
        {
            "transition_type": "OPEN_BRANCH",
            "scope_change_classification": "NOT_APPLICABLE",
            "branch_lifecycle_change": {
                "previous_state": "PROPOSED",
                "next_state": "OPEN",
            },
            "objects_affected": [branch_ref],
            "proposed_post_state_effects": [
                {
                    "action": "MERGE",
                    "object": branch_ref,
                    "effect_description": "Try to weaken OPEN_BRANCH with another action.",
                    "effect_hash": "sha256:" + "8" * 64,
                }
            ],
        }
    )
    assert_schema_blocked(validate_schema, "transition_proposal.schema.json", data)

    decision = load_yaml(EXAMPLE_DIR / "decision.example.yaml")
    decision["transition_type"] = "OPEN_BRANCH"
    decision["branch_lifecycle_change"] = {
        "previous_state": "PROPOSED",
        "next_state": "OPEN",
    }
    decision["decided_effects"] = [
        {
            "action": "OPEN",
            "object": branch_ref,
            "effect_description": "Open only the Branch container.",
            "effect_hash": "sha256:" + "8" * 64,
        }
    ]
    assert validate_schema("decision.schema.json", decision) == []
    decision["transition_type"] = "MERGE_BRANCH"
    assert_schema_blocked(validate_schema, "decision.schema.json", decision)


@pytest.mark.parametrize(
    ("transition_type", "action"),
    [
        ("ADOPT_ASSUMPTION", "ADOPT"),
        ("SUPERSEDE_ASSUMPTION", "ADOPT"),
        ("RETRACT_ASSUMPTION", "RETRACT"),
    ],
)
def test_assumption_transitions_use_dedicated_effects(transition_type, action, validate_schema):
    data = load_yaml(EXAMPLE_DIR / "transition_proposal.example.yaml")
    assumption_ref = {
        "object_type": "Assumption",
        "id": "assumption:fixture.scoped-premise",
        "canonical_hash": "sha256:" + "9" * 64,
    }
    data["transition_type"] = transition_type
    data["scope_change_classification"] = "NOT_APPLICABLE"
    data["objects_affected"] = [assumption_ref]
    if transition_type == "SUPERSEDE_ASSUMPTION":
        data["version_transition"] = {
            "prior_object": {
                **assumption_ref,
                "canonical_hash": "sha256:" + "8" * 64,
            },
            "replacement_object": assumption_ref,
            "relationship": "SUPERSEDES_ASSUMPTION",
        }
    data["proposed_post_state_effects"] = [
        {
            "action": action,
            "object": assumption_ref,
            "effect_description": "Apply only the dedicated Assumption transition.",
            "effect_hash": "sha256:" + "a" * 64,
        }
    ]
    assert validate_schema("transition_proposal.schema.json", data) == []


def test_adopted_assumption_cannot_acquire_epistemic_authority(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "assumption.example.yaml")
    data["epistemic_class"] = "ESTABLISHED"
    assert_schema_blocked(validate_schema, "assumption.schema.json", data)


def test_unknown_top_level_field_is_blocked(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "claim.example.yaml")
    data["model_authority"] = True
    assert_schema_blocked(validate_schema, "claim.schema.json", data)


def test_malformed_hash_is_blocked(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "claim.example.yaml")
    data["canonical_hash"] = "sha256:not-a-real-hash"
    assert_schema_blocked(validate_schema, "claim.schema.json", data)


def test_replay_cannot_be_marked_passed_without_instructions(validate_schema):
    data = load_yaml(EXAMPLE_DIR / "research_receipt.example.yaml")
    del data["replay_instructions"]
    assert_schema_blocked(validate_schema, "research_receipt.schema.json", data)


@pytest.mark.parametrize(
    ("file_name", "path", "inverted"),
    [
        ("authority.yaml", ("project", "independent"), False),
        ("authority.yaml", ("project", "constitutional_precedent", "runtime_dependency"), True),
        ("authority.yaml", ("phase_boundary", "canonical_research_mutation_path_exists"), True),
        ("authority.yaml", ("actors", "proposer", "authoritative"), True),
        ("authority.yaml", ("future_authorization", "human_approval_required"), False),
        ("authority.yaml", ("event_separation", "execution_completion_is_semantic_proof"), True),
        ("claim_policy.yaml", ("scope_discipline", "silent_broadening_allowed"), True),
        ("claim_policy.yaml", ("committed_claims", "producer_self_approval_allowed"), True),
        ("claim_policy.yaml", ("assumptions", "committed_may_be_established_by_adoption"), True),
        (
            "claim_policy.yaml",
            ("assumptions", "committed_meaning"),
            "SCOPED_PREMISE_ESTABLISHES_TRUTH",
        ),
        ("claim_policy.yaml", ("assumptions", "history", "superseded_assumptions_deleted"), True),
        ("claim_policy.yaml", ("branches", "transaction_state_allowed"), True),
        ("claim_policy.yaml", ("branches", "lifecycle_is_epistemic_authority"), True),
        ("claim_policy.yaml", ("branches", "merge_commits_contained_objects"), True),
        (
            "claim_policy.yaml",
            ("branches", "lifecycle_graph", "OPEN_BRANCH"),
            ["OPEN", "ACTIVE"],
        ),
        ("claim_policy.yaml", ("retention", "contradictory_evidence_removal_allowed"), True),
        ("claim_policy.yaml", ("extensions", "may_affect_authority"), True),
        ("execution_policy.yaml", ("artifacts", "raw_artifacts_immutable"), False),
        (
            "execution_policy.yaml",
            ("environment_capture", "tool_versions_bound_to_tool_ids"),
            False,
        ),
        ("execution_policy.yaml", ("authority", "execution_success_is_verification"), True),
        ("human_governance.yaml", ("canonical_transitions", "automatic_merge_allowed"), True),
        ("human_governance.yaml", ("self_approval", "worker_may_approve_own_output"), True),
        (
            "human_governance.yaml",
            ("self_approval", "verifier_modification_may_approve_itself"),
            True,
        ),
    ],
)
def test_frozen_constitution_rejects_major_inversions(
    file_name, path, inverted, validate_schema
):
    data = load_yaml(CONSTITUTION_DIR / file_name)
    target = data
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = inverted
    assert_schema_blocked(validate_schema, "constitution.schema.json", data)


def test_schema_loss_decision_approval_rule_exposes_unknown_verifier(schemas, validate_schema):
    data = load_yaml(EXAMPLE_DIR / "decision.example.yaml")
    data["verifier_results"][0]["outcome"] = "UNKNOWN"
    assert validate_schema("decision.schema.json", data)

    mutated = copy.deepcopy(schemas)
    rules = mutated["decision.schema.json"]["allOf"]
    mutated["decision.schema.json"]["allOf"] = [
        rule
        for rule in rules
        if rule.get("if", {}).get("properties", {}).get("verdict", {}).get("const")
        != "APPROVE"
    ]
    assert validate_with_schema_set(mutated, "decision.schema.json", data) == []


def test_schema_loss_receipt_verifier_stage_rule_exposes_false_stage(schemas, validate_schema):
    data = non_authorized_no_change_receipt()
    data["verifier_obligation_satisfied"] = True
    data["verifier_results"][0]["outcome"] = "UNKNOWN"
    data["mandatory_gate_summary"]["all_satisfied"] = False
    data["mandatory_gate_summary"]["results"][0]["outcome"] = "UNKNOWN"
    assert validate_schema("research_receipt.schema.json", data)

    mutated = copy.deepcopy(schemas)
    rules = mutated["research_receipt.schema.json"]["allOf"]
    mutated["research_receipt.schema.json"]["allOf"] = [
        rule
        for rule in rules
        if "verifier_obligation_satisfied"
        not in rule.get("if", {}).get("properties", {})
    ]
    assert validate_with_schema_set(mutated, "research_receipt.schema.json", data) == []


def test_schema_loss_receipt_evidence_stage_rule_exposes_false_record(schemas, validate_schema):
    data = non_authorized_no_change_receipt()
    data["evidence_recorded"] = True
    data["recorded_evidence"] = []
    assert validate_schema("research_receipt.schema.json", data)

    mutated = copy.deepcopy(schemas)
    rules = mutated["research_receipt.schema.json"]["allOf"]
    mutated["research_receipt.schema.json"]["allOf"] = [
        rule
        for rule in rules
        if "evidence_recorded" not in rule.get("if", {}).get("properties", {})
    ]
    assert validate_with_schema_set(mutated, "research_receipt.schema.json", data) == []


def test_schema_loss_tool_binding_hash_requirement_exposes_unbound_version(
    schemas, validate_schema
):
    data = load_yaml(EXAMPLE_DIR / "result.example.yaml")
    del data["tools_used"][0]["implementation_hash"]
    assert validate_schema("result.schema.json", data)

    mutated = copy.deepcopy(schemas)
    mutated["common.schema.json"]["$defs"]["toolBinding"]["required"].remove(
        "implementation_hash"
    )
    assert validate_with_schema_set(mutated, "result.schema.json", data) == []


def test_schema_loss_not_run_rule_exposes_execution_claims(schemas, validate_schema):
    data = load_yaml(EXAMPLE_DIR / "result.example.yaml")
    data.update(
        {
            "execution_outcome": "NOT_RUN",
            "engineering_maturity": "SPECIFIED",
            "outcome_reason": "The run was not started.",
            "observation_completeness": "COMPLETE",
            "failure_classification": None,
            "unsupported_capability": None,
            "timeout_record": None,
        }
    )
    assert validate_schema("result.schema.json", data)

    mutated = copy.deepcopy(schemas)
    rules = mutated["result.schema.json"]["allOf"]
    mutated["result.schema.json"]["allOf"] = [
        rule
        for rule in rules
        if rule.get("if", {})
        .get("properties", {})
        .get("execution_outcome", {})
        .get("const")
        != "NOT_RUN"
    ]
    assert validate_with_schema_set(mutated, "result.schema.json", data) == []
