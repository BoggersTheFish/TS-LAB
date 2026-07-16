from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
EXAMPLE_DIR = ROOT / "examples"
CONSTITUTION_DIR = ROOT / "constitution"
FIXTURE_DIR = ROOT / "tests" / "fixtures"


@dataclass(frozen=True)
class ContractError:
    """A Phase 0 test-validator result, never an authoritative runtime decision."""

    code: str
    path: str
    message: str


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def _build_registry(schemas: dict[str, dict[str, Any]]) -> Registry:
    registry = Registry()
    for schema in schemas.values():
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    return registry


@pytest.fixture(scope="session")
def schemas() -> dict[str, dict[str, Any]]:
    return {path.name: load_json(path) for path in sorted(SCHEMA_DIR.glob("*.json"))}


@pytest.fixture(scope="session")
def schema_registry(schemas: dict[str, dict[str, Any]]) -> Registry:
    return _build_registry(schemas)


@pytest.fixture(scope="session")
def validate_schema(schema_registry: Registry, schemas: dict[str, dict[str, Any]]):
    format_checker = FormatChecker()

    def validate(schema_name: str, instance: Any) -> list[ValidationError]:
        validator = Draft202012Validator(
            schemas[schema_name],
            registry=schema_registry,
            format_checker=format_checker,
        )
        return sorted(validator.iter_errors(instance), key=lambda error: list(error.absolute_path))

    return validate


def _approval_records(schema_name: str, instance: dict[str, Any]) -> list[dict[str, Any]]:
    fields = {
        "assumption.schema.json": ["approving_human_governance_record"],
        "claim.schema.json": ["approving_human_governance_record"],
        "decision.schema.json": ["human_approval"],
        "transition_proposal.schema.json": ["human_approval"],
        "research_receipt.schema.json": ["human_approval_record"],
    }
    return [
        instance[field]
        for field in fields.get(schema_name, [])
        if isinstance(instance.get(field), dict)
    ]


def _verifier_ids(schema_name: str, instance: dict[str, Any]) -> set[str]:
    verifier_ids: set[str] = set()
    if schema_name == "transition_proposal.schema.json":
        verifier = instance.get("verifier")
        if isinstance(verifier, dict) and isinstance(verifier.get("id"), str):
            verifier_ids.add(verifier["id"])
    result_fields = {
        "decision.schema.json": ["verifier_results"],
        "research_receipt.schema.json": ["verifier_results"],
        "transition_proposal.schema.json": ["mandatory_gate_results"],
    }
    for field in result_fields.get(schema_name, []):
        for result in instance.get(field, []):
            if isinstance(result, dict):
                verifier_id = result.get("verifier", {}).get("id")
                if isinstance(verifier_id, str):
                    verifier_ids.add(verifier_id)
    return verifier_ids


def effect_set_consistency_errors(
    schema_name: str, instance: dict[str, Any]
) -> list[ContractError]:
    """Check array-wide effect invariants shared by proposals and Decisions.

    JSON Schema validates each effect and rejects exact duplicate objects. It cannot
    compare arbitrary array elements by stable object ID, so this helper simulates
    that local check for Phase 0 tests without becoming runtime authority.
    """
    field = {
        "transition_proposal.schema.json": "proposed_post_state_effects",
        "decision.schema.json": "decided_effects",
    }.get(schema_name)
    if field is None:
        return []
    effects = instance.get(field)
    if not isinstance(effects, list):
        return []
    errors: list[ContractError] = []
    first_by_id: dict[str, dict[str, Any]] = {}
    for index, effect in enumerate(effects):
        if not isinstance(effect, dict):
            continue
        object_ref = effect.get("object", {})
        object_id = object_ref.get("id")
        if not isinstance(object_id, str):
            continue
        first = first_by_id.get(object_id)
        if first is None:
            first_by_id[object_id] = effect
            continue
        first_ref = first.get("object", {})
        comparisons = (
            ("object_type", "EFFECT-SET-OBJECT-TYPE-CONFLICT"),
            ("canonical_hash", "EFFECT-SET-CANONICAL-HASH-CONFLICT"),
        )
        code = next(
            (code for key, code in comparisons if first_ref.get(key) != object_ref.get(key)),
            None,
        )
        if code is None and first.get("action") != effect.get("action"):
            code = "EFFECT-SET-ACTION-CONFLICT"
        if code is None and first.get("effect_hash") != effect.get("effect_hash"):
            code = "EFFECT-SET-EFFECT-HASH-CONFLICT"
        if code is None:
            code = "EFFECT-SET-DUPLICATE-IDENTICAL"
        errors.append(
            ContractError(
                code=code,
                path=f"{field}.{index}",
                message=f"{object_id} occurs more than once in one intended post-state effect set",
            )
        )

    if schema_name == "transition_proposal.schema.json":
        effect_refs = [
            effect.get("object") for effect in effects if isinstance(effect, dict)
        ]
        affected_refs = instance.get("objects_affected", [])
        if (
            isinstance(affected_refs, list)
            and len(first_by_id) == len(effect_refs)
            and affected_refs != effect_refs
        ):
            errors.append(
                ContractError(
                    code="TRANSITION-POST-STATE-TARGET-MISMATCH",
                    path="objects_affected",
                    message=(
                        "objects_affected is the ordered post-state target list and must "
                        "match effect object references exactly; prior versions belong in "
                        "version_transition.prior_object"
                    ),
                )
            )
        version = instance.get("version_transition")
        if isinstance(version, dict):
            prior = version.get("prior_object", {})
            replacement = version.get("replacement_object", {})
            if prior.get("id") != replacement.get("id"):
                errors.append(
                    ContractError(
                    code="VERSION-TRANSITION-STABLE-ID-MISMATCH",
                    path="version_transition",
                    message="prior and replacement roles must use one stable object ID",
                )
            )
            if prior.get("object_type") != replacement.get("object_type"):
                errors.append(
                    ContractError(
                    code="VERSION-TRANSITION-OBJECT-TYPE-MISMATCH",
                    path="version_transition",
                    message="prior and replacement roles must retain the object type",
                )
            )
            if prior.get("canonical_hash") == replacement.get("canonical_hash"):
                errors.append(
                    ContractError(
                    code="VERSION-TRANSITION-HASH-NOT-CHANGED",
                    path="version_transition",
                    message="a declared replacement must name a distinct canonical version",
                )
            )
            if replacement not in effect_refs:
                errors.append(
                    ContractError(
                    code="VERSION-TRANSITION-REPLACEMENT-NOT-EFFECT-TARGET",
                    path="version_transition.replacement_object",
                    message="the explicit replacement must be the post-state effect target",
                )
            )
            else:
                replacement_effect = next(
                    effect
                    for effect in effects
                    if isinstance(effect, dict) and effect.get("object") == replacement
                )
                expected_action = (
                    "ADOPT" if replacement.get("object_type") == "Assumption" else "COMMIT"
                )
                if replacement_effect.get("action") != expected_action:
                    errors.append(
                        ContractError(
                            code="VERSION-TRANSITION-REPLACEMENT-ACTION-MISMATCH",
                            path="version_transition.replacement_object",
                            message=(
                                "the replacement post-state effect action must be "
                                f"{expected_action}"
                            ),
                        )
                    )
    elif schema_name == "decision.schema.json":
        version = instance.get("version_transition")
        effect_refs = [
            effect.get("object") for effect in effects if isinstance(effect, dict)
        ]
        if isinstance(version, dict):
            prior = version.get("prior_object", {})
            replacement = version.get("replacement_object", {})
            if prior.get("id") != replacement.get("id"):
                errors.append(
                    ContractError(
                    code="VERSION-TRANSITION-STABLE-ID-MISMATCH",
                    path="version_transition",
                    message="prior and replacement roles must use one stable object ID",
                )
            )
            if prior.get("object_type") != replacement.get("object_type"):
                errors.append(
                    ContractError(
                    code="VERSION-TRANSITION-OBJECT-TYPE-MISMATCH",
                    path="version_transition",
                    message="prior and replacement roles must retain the object type",
                )
            )
            if prior.get("canonical_hash") == replacement.get("canonical_hash"):
                errors.append(
                    ContractError(
                    code="VERSION-TRANSITION-HASH-NOT-CHANGED",
                    path="version_transition",
                    message="a declared replacement must name a distinct canonical version",
                )
            )
            if replacement not in effect_refs:
                errors.append(
                    ContractError(
                    code="VERSION-TRANSITION-REPLACEMENT-NOT-EFFECT-TARGET",
                    path="version_transition.replacement_object",
                    message="the explicit replacement must be the post-state effect target",
                )
            )
            else:
                replacement_effect = next(
                    effect
                    for effect in effects
                    if isinstance(effect, dict) and effect.get("object") == replacement
                )
                expected_action = (
                    "ADOPT" if replacement.get("object_type") == "Assumption" else "COMMIT"
                )
                if replacement_effect.get("action") != expected_action:
                    errors.append(
                        ContractError(
                            code="VERSION-TRANSITION-REPLACEMENT-ACTION-MISMATCH",
                            path="version_transition.replacement_object",
                            message=(
                                "the replacement post-state effect action must be "
                                f"{expected_action}"
                            ),
                        )
                    )
    return errors


def _binding_errors(schema_name: str, instance: dict[str, Any]) -> list[ContractError]:
    errors: list[ContractError] = []
    if schema_name in {
        "result.schema.json",
        "evidence.schema.json",
        "research_receipt.schema.json",
    }:
        seen_tools: dict[str, dict[str, Any]] = {}
        for index, binding in enumerate(instance.get("tools_used", [])):
            if not isinstance(binding, dict) or not isinstance(binding.get("tool_id"), str):
                continue
            tool_id = binding["tool_id"]
            if tool_id in seen_tools:
                code = (
                    "TOOL-BINDING-CONFLICT"
                    if binding != seen_tools[tool_id]
                    else "TOOL-BINDING-DUPLICATE"
                )
                errors.append(
                    ContractError(code, f"tools_used.{index}", f"{tool_id} is bound more than once")
                )
            else:
                seen_tools[tool_id] = binding
    if schema_name == "research_receipt.schema.json":
        seen_workers: dict[str, dict[str, Any]] = {}
        for index, binding in enumerate(instance.get("workers", [])):
            if not isinstance(binding, dict) or not isinstance(binding.get("worker_id"), str):
                continue
            worker_id = binding["worker_id"]
            if worker_id in seen_workers:
                code = (
                    "WORKER-BINDING-CONFLICT"
                    if binding != seen_workers[worker_id]
                    else "WORKER-BINDING-DUPLICATE"
                )
                errors.append(
                    ContractError(code, f"workers.{index}", f"{worker_id} is bound more than once")
                )
            else:
                seen_workers[worker_id] = binding
        producer = instance.get("producer", {})
        producer_id = producer.get("id")
        producer_binding = seen_workers.get(producer_id) if producer_id else None
        if producer_binding is None:
            errors.append(
                ContractError(
                    "RECEIPT-PRODUCER-WORKER-UNBOUND",
                    "producer.id",
                    "the receipt producer must have a directly bound worker record",
                )
            )
        else:
            if any(
                producer.get(source) != producer_binding.get(target)
                for source, target in (
                    ("role", "role"),
                    ("version", "version"),
                    ("implementation_hash", "implementation_hash"),
                )
            ):
                errors.append(
                    ContractError(
                    "RECEIPT-PRODUCER-WORKER-MISMATCH",
                    "producer",
                    "the producer identity and directly bound worker version must agree",
                )
            )
            responsibilities = producer_binding.get("responsibilities", [])
            if "RECEIPT_RECORDING" not in responsibilities:
                errors.append(
                    ContractError(
                        "RECEIPT-PRODUCER-MISSING-RESPONSIBILITY",
                        "producer.id",
                        "the worker bound to the receipt producer must include RECEIPT_RECORDING responsibility",
                    )
                )
    return errors


def constitutional_errors(schema_name: str, instance: Any) -> list[ContractError]:
    """Simulate local cross-field checks that JSON Schema cannot express.

    These checks support Phase 0 contract tests. They are explicitly not a canonical
    store, transition verifier, approval mechanism, or runtime authority boundary.
    """
    if not isinstance(instance, dict):
        return []
    producer_id = instance.get("producer", {}).get("id")
    errors: list[ContractError] = []
    for approval in _approval_records(schema_name, instance):
        approver_id = approval.get("approver", {}).get("id")
        if producer_id and producer_id == approver_id:
            errors.append(
                ContractError(
                    code="GOV-NO-SELF-APPROVAL",
                    path="human_approval.approver.id",
                    message="the producer may not approve its own object or transition",
                )
            )
    if producer_id and producer_id in _verifier_ids(schema_name, instance):
        errors.append(
            ContractError(
                code="GOV-NO-VERIFIER-SELF-APPROVAL",
                path="producer.id",
                message="the producer may not be its own transition verifier",
            )
        )
    if schema_name == "claim.schema.json" and not instance.get("does_not_establish"):
        policy_record = instance.get("limitation_exception_policy_approval", {})
        human_record = instance.get("approving_human_governance_record", {})
        policy_id = policy_record.get("governance_record_id")
        human_id = human_record.get("governance_record_id")
        if policy_id and human_id and policy_id != human_id:
            errors.append(
                ContractError(
                    code="CLAIM-LIMITATION-GOVERNANCE-MISMATCH",
                    path="limitation_exception_policy_approval.governance_record_id",
                    message=(
                        "the policy exception and approving human must name one "
                        "governance record"
                    ),
                )
            )
    if schema_name in {"claim.schema.json", "assumption.schema.json"}:
        if instance.get("id") in instance.get("depends_on", []):
            errors.append(
                ContractError(
                    code="DEPENDENCY-DIRECT-SELF-CYCLE",
                    path="depends_on",
                    message="an object cannot directly depend on its own stable ID",
                )
            )
    errors.extend(effect_set_consistency_errors(schema_name, instance))
    errors.extend(_binding_errors(schema_name, instance))
    if schema_name == "transition_proposal.schema.json":
        considered = set(instance.get("evidence_considered", []))
        labelled_new = set(instance.get("new_supporting_evidence", []))
        if considered & labelled_new:
            errors.append(
                ContractError(
                    code="CLAIM-BROADENING-EVIDENCE-NOT-LOCALLY-DISTINCT",
                    path="new_supporting_evidence",
                    message="an Evidence ID cannot be both previously considered and labelled new",
                )
            )
    return errors


@pytest.fixture(scope="session")
def validate_contract(validate_schema):
    def validate(
        schema_name: str, instance: Any
    ) -> tuple[list[ValidationError], list[ContractError]]:
        return validate_schema(schema_name, instance), constitutional_errors(schema_name, instance)

    return validate
}