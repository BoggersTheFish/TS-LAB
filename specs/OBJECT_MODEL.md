# Research Object Model

## Common Envelope

Every canonical object has a typed stable ID, schema version `0.1.0`, UTC
creation timestamp, producer identity and version, explicit provenance,
deterministic canonical hash, dependency links where applicable, and a
namespaced `extensions` object. Unknown top-level fields are rejected.

Canonical hashes use the contract form `sha256:<64 lowercase hex>`. The future
hashing implementation must serialize JSON deterministically, omit the hash
field being calculated, and publish its canonicalization version. Phase 0
specifies but does not calculate hashes.

Extensions are non-authoritative. Namespace keys and every nested structured key
must be lowercase and pass the centrally defined reserved-vocabulary filter.
Approval/approve variants, authorization/authorisation variants, authority,
verifier state, proof/proves, truth, Decision, Transition, commitment, canonical
state, human approval, receipt authority, and epistemic or transaction status
are rejected in keys and lowercase-only string values at every depth. The
lowercase-only value rule provides portable case handling without non-ECMAScript
inline regular-expression flags. Consumers must ignore all
extensions when evaluating authority even when an unanticipated synonym passes
the lexical filter.

## Object Types

| Object | Purpose | Key authority boundary |
|---|---|---|
| Evidence | Immutable artifact or observation | Cannot declare a Claim true or mutate state |
| Definition | Scoped meaning of a term | Meaning changes require a new addressable object |
| Assumption | Explicit, scoped premise | Adoption is scoped and never establishes truth |
| Claim | Research assertion with three status axes | Commitment requires transition gates and Decision/Receipt support |
| Obligation | One bounded unit of future work | Must be finite, testable, stoppable, and budgeted |
| Experiment | Declared execution contract | Cannot interpret or approve itself |
| Result | Execution outcome, observations, comparisons, and gate observations | Has no epistemic class or transaction state and cannot interpret or approve itself |
| Challenge | Hostile review of Claim, method, scope, or evidence | Reviewer output remains non-authoritative |
| Decision | Verifier-backed and human-governed disposition | Producer and approver must be distinct |
| Branch | Isolated research container description | Separate lifecycle; merge never commits contents |
| TransitionProposal | Exact proposed state effects | Proposal is non-authoritative until separately authorized |
| ResearchReceipt | Hash-linked audit record and replay contract | Five progress booleans remain independent |

## Status Axes

`epistemic_class`, `transaction_state`, and `engineering_maturity` are defined
once in `common.schema.json`. They answer different questions: what kind of
knowledge a Claim asserts, where a committable object is in its authority
transaction, and how mature an engineering artifact is.

No inference is permitted between axes. In particular:

- RELEASED does not mean ESTABLISHED.
- COMPLETED execution does not mean COMMITTED Claim.
- NEGATIVE_DIAGNOSTIC plus COMMITTED is a valid successful outcome.
- HYPOTHESIS plus TESTED may remain CANDIDATE.
- REPRODUCED engineering maturity on a Result does not interpret its observations.
- FAILED, REJECTED, RETRACTED, and contradictory Evidence remain addressable.

## Relationships

Links are typed IDs or strict object references containing object type, ID, and
canonical hash. Evidence does not carry `supports`, `proves`, or `approves`
fields. Claim-side links, Challenges, Decisions, and TransitionProposals state
how Evidence was considered. Circular dependencies and missing dependencies are
constitutional failures even where single-document JSON Schema cannot inspect a
whole repository graph.

## Claim Commitment

A COMMITTED Claim requires nonempty scope, provenance, at least one supporting
Decision or ResearchReceipt, a traceable parent transition, and passing
mandatory transition gates. It must list what it does not establish. The only
exception requires a reason, explicit claim-policy approval, and a human
governance record. Producer self-approval is prohibited.

## Assumption Adoption

An Assumption may use `COMMITTED`, but that state means only canonically adopted
as an explicit premise inside its declared scope and applicable Branch or
programme. It does not mean `ESTABLISHED`, verified, or true. Assumption objects
do not carry `epistemic_class`.

A committed Assumption requires nonblank scope, named applicability, nonempty
`does_not_establish`, downstream Claim dependencies, a falsification, revision,
or discharge condition, `ADOPT_ASSUMPTION` lineage, passing mandatory gate
records, a supporting Decision, a supporting ResearchReceipt, and explicit
human `APPROVE`. `SUPERSEDE_ASSUMPTION` creates an explicitly linked replacement
version, while `RETRACT_ASSUMPTION` changes applicability without deleting the
prior record. Adopted, superseded, and retracted Assumptions remain permanently
addressable, and downstream Claims retain historical dependency links. JSON
Schema enforces the local record shape; the
future transition verifier must prove that the linked Decision, Receipt, and
transition all describe this same Assumption adoption.

## Branch Lifecycle

Branch uses `branch_lifecycle`, not `transaction_state`:
`PROPOSED`, `OPEN`, `ACTIVE`, `FROZEN`, `MERGED`, `ABANDONED`, and `CLOSED`.
Lifecycle transitions are `CREATE_BRANCH`, `OPEN_BRANCH`, `ACTIVATE_BRANCH`, `FREEZE_BRANCH`,
`MERGE_BRANCH`, `ABANDON_BRANCH`, and `CLOSE_BRANCH`. They can affect only a
Branch reference. A non-proposed lifecycle record requires its lifecycle
TransitionProposal plus supporting Decision and ResearchReceipt; terminal
records also require a closure Decision. Activating or merging a Branch never commits, establishes,
adopts, approves, or interprets contained objects. Each contained Claim,
Assumption, or other committable object requires its own valid transition.

## Receipt Events

ResearchReceipt separately records `execution_completed`, `evidence_recorded`,
`verifier_obligation_satisfied`, `transition_authorized`, and
`canonical_state_committed`. `evidence_recorded: true` requires a typed,
nonempty `recorded_evidence` collection. `verifier_obligation_satisfied: true`
requires explicitly passing mandatory verifier results and a satisfied summary
even when authorization is false. Tool and worker IDs bind directly to their
version and implementation hash rather than being satisfied by unrelated
parallel records. These fields allow failed execution with useful
Evidence, rejected transitions after Evidence collection, verified proposals
awaiting humans, authorized transitions awaiting commit, and replayable receipts
that make no canonical change.

Local schema consistency is intentionally narrower than authoritative truth. A
schema can require a passing replay record and two well-formed hashes, but cannot
prove the hashes are equal to canonical serialized content, that replay actually
reproduced the state, that an identity is authentic, or that linked objects
exist. Those are future transition-verifier checks.
