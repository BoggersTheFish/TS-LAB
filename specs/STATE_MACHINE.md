# Research State Machine

This document specifies future legal transitions. Phase 0 provides schemas,
fixtures, documentation, and non-authoritative test simulations only. It has no
state store, verifier runtime, approval service, replay executor, or mutation
operation.

## Invariants

1. A proposal, investigator, runner, reviewer, generator, renderer, model,
   scheduler, or external interface is never authoritative.
2. Execution completion, Evidence recording, verifier satisfaction,
   authorization, replay, and canonical commitment are distinct events.
3. Every proposal names its parent canonical state hash and exact typed effects.
4. Every mandatory verifier result fails closed: only explicit `PASS` passes.
   `FAIL`, `UNKNOWN`, `UNSUPPORTED`, `ERROR`, and `MISSING` cannot authorize.
5. All TS-LAB v0.1 canonical transitions require an approved transition verifier
   and an authentic, distinct human `APPROVE` record.
6. Claim-changing transitions use `SAME_SCOPE`, `NARROWER_SCOPE`, or
   `BROADER_SCOPE`; non-Claim transitions use `NOT_APPLICABLE`.
7. Negative Evidence, contradictory Evidence, failed or rejected Claims,
   rejected proposals, and negative diagnostics remain permanently addressable.
8. A canonical commit must be Decision-backed, receipt-backed, hash-linked, and
   replay-valid.
9. Extensions, confidence, identity, prose, eloquence, token volume, provider,
   and execution volume never affect authority.
10. Verifier-rule changes and verifier implementations cannot approve their own
    modification.
11. Assumption adoption is premise adoption, not scientific establishment.
12. Branch lifecycle changes govern only the Branch container and never commit
    or interpret its contents.

## Normative Transition and Effect Matrix

The schema enforces the following local matrix. `Claim COMMIT` means a new Claim
version is the proposed canonical interpretation; it does not bypass Decision,
human, Receipt, or replay requirements.

| Transition type | Scope classification | Required local effect(s) |
|---|---|---|
| `PROPOSE_CLAIM` | `SAME_SCOPE` | `CREATE` a Claim |
| `COMMIT_CLAIM` | `SAME_SCOPE` | `COMMIT` a Claim |
| `STRENGTHEN_EVIDENCE` | `SAME_SCOPE` | `COMMIT` one replacement Claim effect, declare prior/replacement roles, and `CREATE` or `RETAIN` Evidence |
| `NARROW_CLAIM_SCOPE` | `NARROWER_SCOPE` | `COMMIT` one narrower replacement Claim effect and declare its predecessor through `version_transition.prior_object` |
| `BROADEN_CLAIM_SCOPE` | `BROADER_SCOPE` | `COMMIT` one broader replacement Claim effect, declare prior/replacement roles, and `CREATE` or `RETAIN` supporting Evidence; also requires nonempty new-Evidence IDs, Challenge review, justification, and human `APPROVE` |
| `QUARANTINE_INTERPRETATION` | `SAME_SCOPE` | `QUARANTINE` a Claim |
| `REJECT_CLAIM` | `SAME_SCOPE` | `REJECT` a Claim without deleting it |
| `SUPERSEDE_CLAIM` | `SAME_SCOPE` | `COMMIT` one replacement Claim and declare the superseded Claim in the explicit prior role |
| `RETRACT_CLAIM` | `SAME_SCOPE` | `RETRACT` a Claim while retaining addressability |
| `COMMIT_NEGATIVE_DIAGNOSTIC` | `SAME_SCOPE` | `COMMIT` a scoped negative Claim; may additionally reject its target, retain Evidence, and create a bounded Obligation |
| `CREATE_OBLIGATION` | `NOT_APPLICABLE` | `CREATE` an Obligation |
| `CLOSE_OBLIGATION_SATISFIED` | `NOT_APPLICABLE` | `CLOSE_SATISFIED` on an Obligation |
| `CLOSE_OBLIGATION_KILLED` | `NOT_APPLICABLE` | `CLOSE_KILLED` on an Obligation while retaining partial and negative Evidence |
| `ADOPT_ASSUMPTION` | `NOT_APPLICABLE` | `ADOPT` an Assumption with explicit human `APPROVE` |
| `SUPERSEDE_ASSUMPTION` | `NOT_APPLICABLE` | `ADOPT` one replacement Assumption and declare the superseded Assumption in the explicit prior role |
| `RETRACT_ASSUMPTION` | `NOT_APPLICABLE` | `RETRACT` an Assumption without erasing it |
| `CREATE_BRANCH` | `NOT_APPLICABLE` | `CREATE` only a Branch container |
| `OPEN_BRANCH` | `NOT_APPLICABLE` | `OPEN` only a Branch container |
| `ACTIVATE_BRANCH` | `NOT_APPLICABLE` | `ACTIVATE` only a Branch container |
| `FREEZE_BRANCH` | `NOT_APPLICABLE` | `FREEZE` only a Branch container |
| `MERGE_BRANCH` | `NOT_APPLICABLE` | `MERGE` only a Branch container |
| `ABANDON_BRANCH` | `NOT_APPLICABLE` | `ABANDON` only a Branch container |
| `CLOSE_BRANCH` | `NOT_APPLICABLE` | `CLOSE` only a Branch container |
| `NO_CANONICAL_CHANGE` | `NOT_APPLICABLE` | `NO_CHANGE` and/or nondestructive `RETAIN` effects |

Effect legality is also coupled to the target type. Evidence accepts only
`CREATE` or `RETAIN`; it cannot be committed, approved, rejected, retracted,
superseded, or destructively removed. Assumption adoption effects apply only to
Assumptions. Branch lifecycle effects apply only to Branches. Typed object
references couple each `object_type` to its ID prefix.

One effect set represents intended post-state targets and permits exactly one
effect per stable object ID. `objects_affected` is the ordered post-state target
list and must match effect object references, including their replacement
hashes. A version-changing transition declares its predecessor and replacement
in `version_transition.prior_object` and `replacement_object`; it never encodes
them as two ambiguous effects with the same stable ID. The shared Phase 0 helper
applies the same array-wide rule to TransitionProposal and Decision, rejecting
conflicting types, hashes, actions, effect hashes, and duplicate effects. That
helper is test simulation, not transition authority. The future verifier must
compare both explicit roles and every effect against actual canonical history.

## Assumption Adoption Contract

`COMMITTED` remains legal for Assumption, narrowly meaning “canonically adopted
as an explicit premise within a stated scope and Branch or programme.” A
committed Assumption must remain typed as Assumption and has no
`epistemic_class`. Its local record requires scope, applicability,
`does_not_establish`, downstream Claim dependencies, a revision, kill,
falsification, or discharge condition, a supporting Decision, a supporting
ResearchReceipt, passing transition gates, an `ADOPT_ASSUMPTION` lineage, and
human `APPROVE`.

The future verifier must cross-check those linked records against the actual
transition. Merely inserting IDs with the right lexical prefixes does not adopt
an Assumption. Adoption, supersession, and retraction never erase an Assumption:
supersession creates a new addressable version, retraction changes canonical
applicability rather than historical existence, and downstream Claim dependency
links continue to name the historical premise.

## Branch Lifecycle Contract

Branch has `branch_lifecycle`: `PROPOSED`, `OPEN`, `ACTIVE`, `FROZEN`, `MERGED`,
`ABANDONED`, or `CLOSED`. It does not have scientific `transaction_state` or
`epistemic_class`. Non-proposed lifecycle records carry transition lineage, and
supporting Decision and ResearchReceipt; terminal lifecycle records also carry a
closure Decision.

Branch transition schemas permit effects only on Branch objects. Merging or
activating a Branch cannot carry a Claim `COMMIT`, Assumption `ADOPT`, Result
interpretation, or any implicit content promotion. Every contained object still
requires its own valid transition.

The declared lifecycle graph is:

| Transition | Declared previous state | Declared next state |
|---|---|---|
| `CREATE_BRANCH` | absent (`null`) | `PROPOSED` |
| `OPEN_BRANCH` | `PROPOSED` | `OPEN` |
| `ACTIVATE_BRANCH` | `OPEN` or `FROZEN` | `ACTIVE` |
| `FREEZE_BRANCH` | `ACTIVE` | `FROZEN` |
| `MERGE_BRANCH` | `ACTIVE` or `FROZEN` | `MERGED` |
| `ABANDON_BRANCH` | `PROPOSED`, `OPEN`, `ACTIVE`, or `FROZEN` | `ABANDONED` |
| `CLOSE_BRANCH` | `MERGED` or `ABANDONED` | `CLOSED` |

`branch_lifecycle_change` is the primary structural declaration. Its single
Branch effect must agree. `OPEN` is legal only for a Branch in `OPEN_BRANCH`.
Schema checks the declared pair; the future verifier checks that the declared
previous state is the true historical lifecycle.

## Receipt and Decision Consistency

An approving Decision locally requires at least one mandatory verifier result,
every mandatory result explicitly `PASS`, a satisfied mandatory-gate summary,
and human action `APPROVE`. Human `REJECT` cannot coexist with verdict
`APPROVE`.

An authorized Receipt locally requires the same passing verifier conditions, an
approving Decision summary, a complete human `APPROVE` record, verifier
obligation satisfaction, and structurally complete replay instructions. A
canonical commit additionally requires authorization, non-null post-state hash,
nonempty directly bound tool and worker versions, a replay worker, nonempty replay artifacts, and a `PASSED`
replay with non-null UTC timestamp and observed post-state hash. A noncommitted
Receipt must have null `post_state_hash`.

Earlier stage booleans are truthful independently of later stages.
`evidence_recorded: true` requires a typed, nonempty record naming what Evidence
was recorded and when; `false` requires that collection to be empty.
`verifier_obligation_satisfied: true` requires at least one mandatory result,
only explicit mandatory `PASS`, and a satisfied mandatory-gate summary even when
authorization and commitment are false.

## Result Outcome and Capture Contract

`COMPLETED` permits execution observations, comparisons, gate observations, and
produced Evidence but requires environment and capture records. `FAILED` and
`CANCELLED` require a failure classification and `PARTIAL` or `NONE`
completeness; retained Evidence is limited to partial execution or negative
diagnostics. `TIMED_OUT` additionally requires a structured timeout record and
marks gate records partial or not evaluated. `NOT_RUN` records a nonblank reason
and administrative observations but no execution observations, comparisons,
gates, tools, environment, capture, or produced Evidence. `UNSUPPORTED` names
the unavailable capability and may produce only explicitly typed administrative
or capability-diagnostic Evidence, never scientific comparisons or passing
gates.

Tool IDs bind directly to version and implementation hash. Worker IDs in a
Receipt bind directly to role, version, implementation hash, and
responsibilities. Stream and raw-artifact captures use `CAPTURED`,
`NOT_PRODUCED`, or `NOT_APPLICABLE`; the latter two require a nonblank reason.
Schema checks this structure. The future verifier checks actor identity,
artifact existence, contents, immutability, hashes, and whether a claimed
not-applicable capture is honest for the execution method.

JSON Schema does not prove hash equality, content authenticity, approval
authenticity, or real replay reproduction. Those checks remain below.

## Future Authoritative Transition Verifier Contract

The future verifier receives one immutable verification package containing:

- the proposed TransitionProposal and its canonical serialized bytes;
- the true current canonical state hash and parent Receipt;
- all affected before/after objects and canonical serialized bytes;
- all referenced Evidence, Claims, Assumptions, Challenges, Decisions,
  Obligations, Branches, Results, and provenance sources;
- the proposed Decision and human approval record with authentication material;
- replay instructions, artifacts, environment, tool and worker versions;
- the approved verifier registry, ruleset bytes and hash, version history, and
  approval lineage;
- the complete dependency graph and Evidence retention index relevant to the
  proposed delta; and
- historical Evidence and Challenge indexes needed for novelty and review checks.

It must fail closed before authorization if any of these checks is false,
unknown, unsupported, missing, inconsistent, or errors:

1. every referenced object exists and its actual canonical type matches both
   `object_type` and typed ID;
2. every declared hash matches the approved canonical serialization of its
   actual content;
3. `parent_canonical_state_hash` equals the one true current state and the
   Receipt parent chain is intact;
4. replay instructions execute in the declared environment and reproduce the
   actual proposed post-state hash;
5. every canonically referenced Evidence object is unchanged, immutable, and
   reachable after the proposed delta, including negative and contradictory
   Evidence;
6. the resulting dependency graph is acyclic wherever the constitution forbids
   cycles and contains no missing dependency;
7. Evidence labelled new for `BROADER_SCOPE` was not already available or used
   in the relevant prior support history and is genuinely new support;
8. required Challenges existed before authorization and their actual contents
   were reviewed by the Decision, not merely named;
9. producers, experiment runners, investigators, reviewers, generators,
   verifiers, and human approvers satisfy all required identity separation
   across every affected record;
10. the human identity and approval are authentic, unrevoked, scoped to this
    exact transition, and action `APPROVE`;
11. the verifier is a member of the approved registry, the ruleset bytes match
    `ruleset_hash`, and the version has valid human approval lineage;
12. neither the verifier nor its producer approved the verifier's own code,
    ruleset, registry entry, or modification;
13. the declared scope classification matches a semantic before/after comparison
    of the real Claim versions, including domain, boundaries, and exclusions;
14. Assumption adoption records all refer to the same scoped Assumption and
    Branch/programme, Decision, Receipt, human approval, and downstream links;
15. Branch lifecycle effects alter only the container and produce no implicit
    mutation of contained objects, and the declared prior lifecycle is the true
    historical state;
16. explicit prior and replacement object roles name the true historical and
    proposed versions, the post-state target list matches the real effect delta,
    and tool/worker bindings identify the actual implementations used;
17. a Result's produced-Evidence role matches the referenced Evidence object's
    classification; `UNSUPPORTED` diagnostics contain no scientific comparison,
    passing gate, or target-hypothesis assertion, and capture-status reasons are
    honest for the declared execution method;
18. superseded or retracted Assumptions remain addressable and all downstream
    historical dependency references remain reachable; and
19. TransitionProposal, Decision, ResearchReceipt, replayed delta, and actual
    state mutation describe exactly the same effects and final state.

Only that future verifier plus the required human approval may authorize. Phase
0 tests can demonstrate examples of these comparisons but cannot make them
authoritative.

## Illegal Transitions

- confidence-only, model-identity, provider-identity, eloquence, or token-volume
  promotion;
- Experiment or Result self-interpretation or self-approval;
- investigator, runner, reviewer, generator, proposer, or verifier self-approval;
- Evidence directly mutating canonical state or becoming unreachable;
- missing provenance or stale parent canonical state;
- silent scope broadening or relabelling old Evidence as new;
- verifier-rule changes approving themselves;
- treating a non-pass outcome as pass;
- extension metadata providing alternate approval, truth, verifier state,
  transaction state, or commitment;
- Branch activation or merge committing contained objects; and
- any scheduler, autonomous loop, QueryProcessor, external interface, or
  self-improvement routine authorizing state change.

Illegal proposals may still receive a `REJECT` or `NO_CANONICAL_CHANGE` Receipt
so the attempt remains auditable. They never produce an authorized canonical
delta.
