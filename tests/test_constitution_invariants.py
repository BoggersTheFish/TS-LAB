from __future__ import annotations

import ast
import json
import shutil
import subprocess
import tomllib
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from .conftest import CONSTITUTION_DIR, ROOT, load_yaml

CONSTITUTION_FILES = {
    "authority.yaml",
    "claim_policy.yaml",
    "execution_policy.yaml",
    "human_governance.yaml",
}

OBJECT_SCHEMAS = {
    "evidence.schema.json",
    "definition.schema.json",
    "assumption.schema.json",
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

IGNORED_PARTS = {
    ".git",
    ".venv",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "ts_lab.egg-info",
}


def authored_files():
    for path in ROOT.rglob("*"):
        if path.is_file() and not IGNORED_PARTS.intersection(path.parts):
            yield path


def walk(value):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def test_all_schemas_are_valid_draft_2020_12(schemas):
    for name, schema in schemas.items():
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema", name
        Draft202012Validator.check_schema(schema)


def test_all_local_schema_references_resolve_offline(schemas, schema_registry):
    for schema in schemas.values():
        resolver = schema_registry.resolver(base_uri=schema["$id"])
        for node in walk(schema):
            if isinstance(node, dict) and "$ref" in node:
                resolver.lookup(node["$ref"])


def test_format_checker_has_real_datetime_and_uri_validators():
    checker = FormatChecker()
    assert "date-time" in checker.checkers
    assert "uri" in checker.checkers


def test_object_schemas_reject_unknown_top_level_fields(schemas):
    for name in OBJECT_SCHEMAS:
        assert schemas[name]["additionalProperties"] is False, name


def test_all_constitutions_parse_and_validate_normatively(validate_schema):
    assert {path.name for path in CONSTITUTION_DIR.glob("*.yaml")} == CONSTITUTION_FILES
    for path in sorted(CONSTITUTION_DIR.glob("*.yaml")):
        policy = load_yaml(path)
        assert isinstance(policy, dict)
        errors = validate_schema("constitution.schema.json", policy)
        assert errors == [], "\n".join(error.message for error in errors)


def test_constitution_schema_is_frozen_not_a_generic_boolean_shape(schemas):
    schema = schemas["constitution.schema.json"]
    assert "Frozen TS-LAB Phase 0 Constitution" == schema["title"]
    for definition in schema["$defs"].values():
        assert "const" in definition
        assert definition["type"] == "object"


def test_authority_policy_is_fail_closed_and_non_authoritative():
    policy = load_yaml(CONSTITUTION_DIR / "authority.yaml")
    assert policy["project"]["independent"] is True
    assert policy["project"]["constitutional_precedent"] == {
        "project": "BoggersTheAI",
        "access": "READ_ONLY_REFERENCE",
        "runtime_dependency": False,
    }
    assert policy["phase_boundary"] == {
        "phase": 0,
        "canonical_research_mutation_path_exists": False,
        "tskernel_integration_exists": False,
    }
    assert all(actor["authoritative"] is False for actor in policy["actors"].values())
    assert set(policy["authority_weights"].values()) == {0}
    assert set(policy["fail_closed"].values()) == {"REJECT"}
    assert all(value is False for value in policy["event_separation"].values())


def test_claim_policy_agrees_with_commitment_and_scope_schemas(schemas):
    policy = load_yaml(CONSTITUTION_DIR / "claim_policy.yaml")
    assert policy["scope_discipline"]["silent_broadening_allowed"] is False
    assert policy["committed_claims"]["producer_self_approval_allowed"] is False
    assert policy["retention"]["negative_diagnostics_permanently_addressable"] is True
    assert policy["retention"]["contradictory_evidence_removal_allowed"] is False
    claim = schemas["claim.schema.json"]
    transition = schemas["transition_proposal.schema.json"]
    assert "does_not_establish" in claim["required"]
    assert "provenance" in claim["required"]
    assert "BROADEN_CLAIM_SCOPE" in schemas["common.schema.json"]["$defs"]["transitionType"][
        "enum"
    ]
    assert any("BROADER_SCOPE" in str(rule) for rule in transition["allOf"])


def test_execution_policy_agrees_with_non_authoritative_result_schema(schemas):
    policy = load_yaml(CONSTITUTION_DIR / "execution_policy.yaml")
    result = schemas["result.schema.json"]
    assert policy["authority"] == {
        "result_self_interpretation_allowed": False,
        "result_self_approval_allowed": False,
        "execution_success_is_verification": False,
        "execution_failure_precludes_knowledge": False,
    }
    assert "execution_outcome" in result["properties"]
    assert "failure_classification" in result["properties"]
    assert "environment" in result["properties"]
    assert "tools_used" in result["properties"]
    assert "execution_capture" in result["properties"]
    assert "epistemic_class" not in result["properties"]
    assert "transaction_state" not in result["properties"]


def test_human_governance_agrees_with_transition_decision_and_receipt_schemas(schemas):
    policy = load_yaml(CONSTITUTION_DIR / "human_governance.yaml")
    assert policy["canonical_transitions"]["human_approval_required"] is True
    assert policy["canonical_transitions"]["automatic_merge_allowed"] is False
    assert policy["automation"]["background_daemon_allowed"] is False
    assert all(value is False for value in policy["self_approval"].values())
    assert schemas["transition_proposal.schema.json"]["properties"][
        "human_approval_required"
    ] == {"const": True}
    assert "mandatory_gate_summary" in schemas["decision.schema.json"]["required"]
    assert "transition_authorized" in schemas["research_receipt.schema.json"]["required"]


def test_status_enums_are_central_and_axis_fields_cannot_duplicate_subsets_or_supersets(schemas):
    common = schemas["common.schema.json"]["$defs"]
    axis_refs = {
        "epistemic_class": "common.schema.json#/$defs/epistemicClass",
        "transaction_state": "common.schema.json#/$defs/transactionState",
        "engineering_maturity": "common.schema.json#/$defs/engineeringMaturity",
        "branch_lifecycle": "common.schema.json#/$defs/branchLifecycle",
    }
    assert common["epistemicClass"]["enum"] == [
        "ESTABLISHED",
        "REPRODUCTION",
        "SUBSTRATE_DERIVED",
        "CONDITIONAL_CONSTRUCTION",
        "NEGATIVE_DIAGNOSTIC",
        "HYPOTHESIS",
        "ANSATZ",
        "FAILED",
        "KILL_CONDITION",
    ]
    for name, schema in schemas.items():
        if name == "common.schema.json":
            continue
        for field, expected_ref in axis_refs.items():
            if field in schema.get("properties", {}):
                assert schema["properties"][field] == {"$ref": expected_ref}, (
                    name,
                    field,
                    "inline subset/superset duplication or drift",
                )


def test_transition_and_effect_enums_are_central_and_reused(schemas):
    properties = schemas["transition_proposal.schema.json"]["properties"]
    assert properties["transition_type"] == {"$ref": "common.schema.json#/$defs/transitionType"}
    assert schemas["decision.schema.json"]["properties"]["transition_type"] == {
        "$ref": "common.schema.json#/$defs/transitionType"
    }
    assert properties["proposed_post_state_effects"] == {
        "$ref": "common.schema.json#/$defs/transitionEffectSet"
    }
    assert schemas["decision.schema.json"]["properties"]["decided_effects"] == {
        "$ref": "common.schema.json#/$defs/transitionEffectSet"
    }
    effect_set = schemas["common.schema.json"]["$defs"]["transitionEffectSet"]
    assert effect_set["items"] == {"$ref": "#/$defs/transitionEffect"}


def test_evidence_has_no_direct_truth_interpretation_or_approval_field(schemas):
    properties = schemas["evidence.schema.json"]["properties"]
    forbidden = {
        "claim_true",
        "proves",
        "supports",
        "contradicts",
        "approves",
        "decision",
        "epistemic_class",
        "transaction_state",
    }
    assert forbidden.isdisjoint(properties)


def test_assumption_and_branch_have_distinct_semantics(schemas):
    assumption = schemas["assumption.schema.json"]["properties"]
    branch = schemas["branch.schema.json"]["properties"]
    assert "transaction_state" in assumption
    assert "does_not_establish" in assumption
    assert "applicability" in assumption
    assert "branch_lifecycle" in branch
    assert "transaction_state" not in branch
    assert branch["merge_does_not_commit_contents"] == {"const": True}
    policy = load_yaml(CONSTITUTION_DIR / "claim_policy.yaml")
    assert policy["assumptions"]["committed_meaning"] == (
        "SCOPED_PREMISE_ADOPTION_NOT_TRUTH"
    )
    assert policy["assumptions"]["history"][
        "downstream_historical_dependencies_retained"
    ] is True
    assert policy["branches"]["transaction_state_allowed"] is False
    assert policy["branches"]["merge_commits_contained_objects"] is False
    assert policy["branches"]["lifecycle_states"] == schemas["common.schema.json"][
        "$defs"
    ]["branchLifecycle"]["enum"]
    transition_types = set(schemas["common.schema.json"]["$defs"]["transitionType"]["enum"])
    assert set(policy["branches"]["lifecycle_graph"]) <= transition_types


def test_schema_ids_are_unique_and_match_offline_file_names(schemas):
    ids = [schema["$id"] for schema in schemas.values()]
    assert len(ids) == len(set(ids))
    for name, schema in schemas.items():
        assert schema["$id"].endswith(f"/{name}")


def test_extension_patterns_compile_as_ecmascript_without_inline_flags(schemas):
    common = schemas["common.schema.json"]["$defs"]
    patterns = []
    extension_contract = {
        "reserved": common["reservedExtensionKey"],
        "value": common["extensionValue"],
    }
    for node in walk(extension_contract):
        if isinstance(node, dict) and isinstance(node.get("pattern"), str):
            patterns.append(node["pattern"])
    assert patterns
    assert all("(?i)" not in pattern for pattern in patterns)
    node = shutil.which("node")
    assert node is not None, "local validation requires the available ECMAScript compiler"
    script = "const patterns=JSON.parse(process.argv[1]); for (const p of patterns) new RegExp(p);"
    completed = subprocess.run(
        [node, "-e", script, json.dumps(patterns)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_obligations_are_bounded_testable_stoppable_and_commitment_traced(schemas):
    obligation = schemas["obligation.schema.json"]
    required = set(obligation["required"])
    assert {
        "precise_question",
        "finite_scope",
        "success_gates",
        "kill_gates",
        "resource_budget",
        "required_outputs",
        "dependency_requirements",
        "stop_conditions",
        "supporting_decisions",
        "supporting_receipts",
    } <= required
    assert any("commitmentLineageRequirements" in str(rule) for rule in obligation["allOf"])


def test_no_authored_python_file_imports_boggerstheai():
    for path in authored_files():
        if path.suffix != ".py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(
                    not alias.name.lower().startswith("boggerstheai") for alias in node.names
                )
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.lower().startswith("boggerstheai")


def phase1_boundary_violations(root: Path) -> list[str]:
    files = {
        path.relative_to(root)
        for path in root.rglob("*")
        if path.is_file() and not IGNORED_PARTS.intersection(path.parts)
    }
    forbidden_roots = {
        "agents",
        "workers",
        "runtime",
        "scheduler",
        "orchestration",
        "models",
        "experiments",
        "database",
        "state",
        "store",
        "kernel",
        "interface",
        "src",
        "bin",
    }
    violations = [
        f"runtime-directory:{path}"
        for path in files
        if forbidden_roots.intersection(path.parts)
    ]
    executable_suffixes = {
        ".sh",
        ".bash",
        ".js",
        ".mjs",
        ".cjs",
        ".ts",
        ".tsx",
        ".jsx",
        ".ipynb",
        ".go",
        ".rs",
    }
    violations.extend(
        f"executable-source:{path}" for path in files if path.suffix in executable_suffixes
    )
    violations.extend(
        f"non-test-python:{path}"
        for path in files
        if path.suffix == ".py" and path.parts[0] != "tests"
    )
    violations.extend(
        f"root-yaml-entrypoint:{path}"
        for path in files
        if len(path.parts) == 1 and path.suffix in {".yaml", ".yml"}
    )
    violations.extend(
        f"executable-permission:{path}"
        for path in files
        if (root / path).stat().st_mode & 0o111
    )
    forbidden_entrypoints = {
        Path("Dockerfile"),
        Path("docker-compose.yml"),
        Path("compose.yaml"),
        Path("Makefile"),
        Path("Procfile"),
    }
    violations.extend(
        f"entrypoint:{path}" for path in sorted(files & forbidden_entrypoints)
    )
    return sorted(violations)


def test_complete_project_tree_contains_no_phase1_runtime_or_entrypoint():
    assert phase1_boundary_violations(ROOT) == []


def test_phase1_boundary_scan_detects_hidden_multilanguage_and_test_runtime(tmp_path):
    cases = {
        "runtime/loop.py": "pass\n",
        "tests/runtime/adapter.py": "pass\n",
        "hidden/worker.ts": "export {};\n",
        "hidden/runner.sh": "#!/bin/sh\n",
        "hidden/analysis.ipynb": "{}\n",
        "service.yaml": "command: run\n",
    }
    for relative, content in cases.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    executable = tmp_path / "README.md"
    executable.write_text("fixture", encoding="utf-8")
    executable.chmod(0o755)
    violations = phase1_boundary_violations(tmp_path)
    assert any(item.startswith("runtime-directory:") for item in violations)
    assert any(item.startswith("executable-source:") for item in violations)
    assert any(item.startswith("root-yaml-entrypoint:") for item in violations)
    assert any(item.startswith("executable-permission:") for item in violations)


def test_project_has_no_runtime_dependencies_or_package_entrypoints():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["dependencies"] == []
    assert project["tool"]["setuptools"]["packages"] == []
    assert "scripts" not in project["project"]
    assert "entry-points" not in project["project"]


def test_no_generated_build_or_secret_artifacts_are_project_files():
    forbidden_names = {
        ".env",
        "dist",
        "build",
        "node_modules",
        ".coverage",
        "coverage.xml",
    }
    paths = {part for path in authored_files() for part in path.relative_to(ROOT).parts}
    assert forbidden_names.isdisjoint(paths)
    generated = [
        path for path in authored_files() if path.suffix in {".whl", ".pyc", ".p12", ".pem"}
    ]
    assert not generated


def test_required_phase0_files_exist():
    required = {
        "README.md",
        "pyproject.toml",
        ".gitignore",
        "specs/AUTHORITY_PRECEDENT.md",
        "specs/OBJECT_MODEL.md",
        "specs/STATE_MACHINE.md",
        "specs/RESEARCH_CYCLE.md",
        "specs/THREAT_MODEL.md",
        "specs/MVP_ACCEPTANCE.md",
        "specs/DEC24C_REFERENCE_CASE.md",
        "tests/test_adversarial_bypasses.py",
        "tests/test_fixture_graph.py",
    }
    required.update(f"constitution/{name}" for name in CONSTITUTION_FILES)
    required.update(f"schemas/{name}" for name in OBJECT_SCHEMAS)
    required.update({"schemas/common.schema.json", "schemas/constitution.schema.json"})
    for relative in required:
        assert (ROOT / relative).is_file(), relative


def test_future_transition_verifier_contract_is_decision_complete():
    state_machine = (ROOT / "specs" / "STATE_MACHINE.md").read_text(encoding="utf-8")
    state_machine_flat = " ".join(state_machine.split())
    required_contract_terms = {
        "every referenced object exists",
        "approved canonical serialization",
        "true current state",
        "reproduce the actual proposed post-state hash",
        "Evidence object is unchanged, immutable, and reachable",
        "dependency graph is acyclic",
        "genuinely new support",
        "actual contents were reviewed",
        "identity separation",
        "human identity and approval are authentic",
        "approved registry",
        "ruleset bytes match",
        "verifier's own code",
        "semantic before/after comparison",
        "actual canonical type matches",
        "state mutation describe exactly the same effects",
    }
    for term in required_contract_terms:
        assert term in state_machine_flat


def test_docs_distinguish_schema_helpers_and_future_authority():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    cycle = (ROOT / "specs" / "RESEARCH_CYCLE.md").read_text(encoding="utf-8")
    assert "JSON Schema enforces local shape and consistency" in readme
    assert "not runtime enforcement and have no authority" in readme
    assert "future authoritative transition verifier" in readme
    assert "test simulation, not transition authority" in (
        ROOT / "specs" / "STATE_MACHINE.md"
    ).read_text(encoding="utf-8")
    cycle_flat = " ".join(cycle.split())
    assert "Neither can" in cycle_flat and "authorize a transition" in cycle_flat


def test_authority_precedent_records_exact_read_only_sources():
    text = (ROOT / "specs" / "AUTHORITY_PRECEDENT.md").read_text(encoding="utf-8")
    assert "73fd3e8ee9053e77a56367126ca64713004c5a59" in text
    assert "No nearby local checkout was available" in text
    for source in (
        "README.md",
        "ARCHITECTURE.md",
        "COGNITIVE_PHYSICS_ROADMAP.md",
        "core/kernel/ir.py",
        "core/kernel/receipts.py",
        "tests/test_canonical_kernel.py",
        "interface/autonomous_loop.py",
        "interface/self_improvement.py",
    ):
        assert source in text
