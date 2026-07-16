# MVP Acceptance

## Phase 0 Exit Gate

Phase 0 is accepted only when:

- TS-LAB is an independent project and no external repository was modified;
- all required constitution, schema, specification, example, and test files exist;
- every schema is valid Draft 2020-12 and all local references resolve offline;
- every example validates against its intended schema;
- every invalid fixture fails only for its declared constitutional reason;
- constitutions parse as YAML and match the single normative frozen-constitution
  schema exactly; inverted constitutional values fail;
- confidence, identity, execution, reviewers, investigators, extensions, and
  external interfaces cannot authorize Claims or transitions;
- committed Claims require provenance, limitations, support, transition lineage,
  and satisfied mandatory gates;
- broader scope requires human approval, new Evidence, Challenge review, and
  justification;
- approving Decisions and authorized Receipts fail closed on every mandatory
  verifier outcome and require explicit human `APPROVE`;
- canonical commitment requires coherent authorization, replay, post-state,
  artifact, tool, and worker records;
- transition type, Claim scope classification, typed object ID, object type, and
  legal effect are locally coupled;
- each TransitionProposal and Decision effect set has one post-state effect per
  stable ID, with explicit prior/replacement roles for version changes;
- each Receipt stage is locally truthful even when later stages are false, and
  tool/worker versions are directly bound to the named actors;
- Result has no epistemic or transaction authority and may retain Evidence from
  failed execution; `NOT_RUN` cannot claim execution facts and `UNSUPPORTED`
  emits only administrative or capability diagnostics;
- committed Assumption means only scoped premise adoption with Decision/Receipt
  lineage, limitations, dependencies, revision condition, and human approval;
- Branch has a separate lifecycle and merge cannot commit contained objects;
- the complete Branch lifecycle graph, including `OPEN_BRANCH`, is structurally
  coupled to declared previous/next states and container-only effects;
- extensions reject reserved authority aliases recursively, semantic strings are
  nonblank, and timestamps and URIs receive active format validation;
- receipts separate execution, Evidence, verification, authorization, and commit;
- negative Evidence, failures, and rejected interpretations remain addressable;
- the DEC24-C fixture demonstrates improvement without false promotion;
- all tests, lint checks, and package metadata checks pass;
- test-validator simulations and future authoritative transition-verifier duties
  are labelled accurately and never conflated;
- no agents, model calls, scheduling, execution, state store, mutation boundary,
  TSKernel integration, or other Phase 1 runtime exists.

Any schema or constitution change after acceptance reopens this review gate.

Phase 0 exit still requires another independent read-only adversarial audit. A
passing local suite is necessary evidence, not self-approval.

## Later First End-to-End Validation

The first future end-to-end case should instantiate the DEC24-C pattern through
an isolated, explicitly approved test harness: snapshot a known state, select one
bounded Obligation, record real source artifacts without inventing measurements,
run a deterministic allowlisted evaluation, preserve a failed mandatory gate as
Evidence, sustain hostile review, propose only a negative diagnostic, obtain
human approval, create a receipt, replay it, and verify that the target emergence
Claim was not committed.

That case is not part of Phase 0. Before implementation it requires a separate
Phase 1 design review covering the mutation boundary, verifier implementation,
artifact storage, sandbox, canonicalization algorithm, human approval security,
and rollback behavior.
