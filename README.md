# TS-LAB

TS-LAB is a standalone specification and validation project for verifier-governed
research records. It freezes the constitutional boundary, object model, state
machine, schemas, and acceptance tests that later TS-LAB phases must obey.

TS-LAB is not a generic multi-agent chat system. Conversation, model output,
confidence, reviewer agreement, and execution volume are proposal or evidence
sources at most. None has research authority. Phase 0 contains no agents, model
provider, experiment runner, scheduler, database, or canonical state mutation.

## Three Planes

The future architecture separates three planes:

- **Evidence plane:** immutable raw, derived, reproduced, or external artifacts,
  with exact provenance and environment capture. Evidence can be considered by a
  verifier but cannot declare a Claim true or mutate canonical state.
- **Research plane:** Definitions, Assumptions, Claims, Challenges, Decisions,
  bounded Obligations, Branches, TransitionProposals, and ResearchReceipts. This
  plane expresses what is proposed, reviewed, authorized, rejected, or retained.
- **Execution plane:** future isolated, budgeted execution that captures seeds,
  environment, tools, stdout, stderr, timeouts, and failures. Execution completion
  is distinct from Evidence recording and semantic verification.

Only a future dedicated transition verifier, together with the required human
approval, may authorize a research-state change. TS-LAB v0.1 requires human
approval for every canonical transition and permits no automatic merge. Phase 0
does not implement that authorization or mutation path.

## Research Objects

The canonical object types are Evidence, Definition, Assumption, Claim,
Obligation, Experiment, Result, Challenge, Decision, Branch,
TransitionProposal, and ResearchReceipt. Every object has a typed stable ID,
schema version, timestamp, producer, provenance, deterministic canonical hash,
dependency links where applicable, and restricted namespaced extensions.

`COMMITTED` has type-specific meaning. For a Claim it means canonically adopted
through the Claim transition path. For an Assumption it means only “canonically
adopted as an explicit premise within a stated scope and Branch or programme”; it
never means verified or established as true. Assumptions use
`ADOPT_ASSUMPTION`, `SUPERSEDE_ASSUMPTION`, and `RETRACT_ASSUMPTION`.

A Branch does not have `transaction_state`. It has the independent container
lifecycle `PROPOSED`, `OPEN`, `ACTIVE`, `FROZEN`, `MERGED`, `ABANDONED`, or
`CLOSED`. Creating, opening, activating, freezing, merging, abandoning, or closing a
Branch changes only the Branch container. It never commits a contained Claim,
Assumption, Result, or interpretation.

An Obligation is the atomic unit of future work. It must ask one finite question,
name its dependencies, define allowed and forbidden methods, provide inspectable
success and kill gates, state a resource budget and concrete outputs, and include
at least one stopping condition.

## Independent Status Axes

Claims use the three independent vocabularies from
`schemas/common.schema.json`:

- `epistemic_class`: ESTABLISHED, REPRODUCTION, SUBSTRATE_DERIVED,
  CONDITIONAL_CONSTRUCTION, NEGATIVE_DIAGNOSTIC, HYPOTHESIS, ANSATZ, FAILED, or
  KILL_CONDITION.
- `transaction_state`: CANDIDATE, UNDER_REVIEW, COMMITTED, QUARANTINED,
  REJECTED, SUPERSEDED, or RETRACTED.
- `engineering_maturity`: SPECIFIED, IMPLEMENTED, TESTED, REPRODUCED, or
  RELEASED.

Engineering maturity does not imply epistemic strength. Successful execution
does not imply semantic truth. A committed negative diagnostic is a successful
research outcome. A hypothesis may be implemented and tested while remaining
uncommitted. Result is deliberately not an epistemic or transactional object: it
records typed execution and administrative observations, execution outcome,
gate observations, comparisons, directly bound tool versions, capture records,
and produced-Evidence roles. `NOT_RUN` records no execution-derived facts;
`UNSUPPORTED` can emit only administrative or capability-diagnostic Evidence.
Interpretation occurs only through Claim, Challenge, Decision,
TransitionProposal, and ResearchReceipt. Rejection and failure remain
permanently addressable. No generic `status` field substitutes for these axes.

## Validation and Authority Layers

Phase 0 keeps three enforcement layers explicit:

- JSON Schema enforces local shape and consistency, including typed IDs, legal
  transition/effect combinations, nonblank semantic strings, UTC timestamps,
  URI and hash syntax, extension restrictions, and fail-closed receipt and
  Decision combinations. Absolute URI fields accept any valid URI scheme,
  including `https:`, `file:`, `mailto:`, and `urn:`; they do not require `://`.
- Python helpers in `tests/` simulate a small set of cross-field checks for test
  coverage, such as producer/approver inequality, one-effect-per-stable-ID
  consistency shared by TransitionProposal and Decision, directly bound actor
  uniqueness, direct self-dependency rejection, limitation-exception record
  agreement, and local new-Evidence overlap. They
  are not runtime enforcement and have no authority.
- A future authoritative transition verifier must check history and external
  truth: reference existence, content hashes, parent state, replay reproduction,
  Evidence immutability and reachability, dependency cycles, historical novelty,
  actual Challenge review, identity authenticity, verifier approval lineage,
  semantic scope change, and consistency with the real mutation. Phase 0 does
  not implement that verifier.

## Constitutional Precedent

BoggersTheAI was consulted read-only as constitutional precedent. TS-LAB adopts
its verifier-first separation of proposal, evidence, verification,
authorization, commitment, receipt hashing, and replay. It does not copy or
import BoggersTheAI runtime code. Compatibility with TSKernel or other external
systems must be explicit and versioned in a later phase. See
`specs/AUTHORITY_PRECEDENT.md`.

The four machine-readable policies are:

- `constitution/authority.yaml`
- `constitution/claim_policy.yaml`
- `constitution/execution_policy.yaml`
- `constitution/human_governance.yaml`

## Phase 0 Boundary

Phase 0 implements JSON Schema Draft 2020-12 contracts, policy YAML,
specifications, examples, invalid fixtures, and tests. Hash fields specify future
deterministic canonical serialization but Phase 0 does not calculate hashes or
execute replay instructions.

`schemas/constitution.schema.json` is the single normative schema for the four
frozen Phase 0 policies. It validates their exact values and is not a generic,
weaker policy-shape alternative. Canonical timestamps use RFC 3339 UTC with an
uppercase trailing `Z`; maintained `jsonschema` format dependencies validate
date-time and absolute URI syntax.

Deferred: autonomous research, agent orchestration, model calls, execution,
background scheduling, live Claim graphs, canonical storage and mutation,
BoggersTheAI writes, TSKernel integration, and all Phase 1 runtime behavior.

## Development

Python is validation tooling only. Create a local environment and install the
development extra:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
```

Run schema and constitutional validation:

```bash
.venv/bin/python -m pytest
.venv/bin/ruff check tests
.venv/bin/python -m pip check
```

`tests/test_schema_examples.py` validates every example and intentional failure.
`tests/test_adversarial_bypasses.py` executes the repaired bypass matrix.
`tests/test_fixture_graph.py` traverses the DEC24-C reference chain.
`tests/test_constitution_invariants.py` validates the frozen policies, schema
metaschemas and references, enum reuse, and repository boundary.

## Review Gate

Phase 1 must not start until a human review confirms that all Phase 0 tests pass,
every schema and constitution change is reviewed, the DEC24-C case preserves
partial improvement without false promotion, and no authority bypass exists in
extensions, confidence, execution, schedulers, external interfaces, or model
identity. Approval of Phase 0 is not approval to begin autonomous operation.
