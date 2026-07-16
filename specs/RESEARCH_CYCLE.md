# Future Research Cycle

This cycle is a Phase 1-or-later specification. Phase 0 does not implement any
step, worker, scheduler, model call, experiment, verifier runtime, approval
workflow, receipt executor, or canonical mutation.

1. **Snapshot:** identify an immutable canonical state hash and relevant object
   hashes.
2. **Reconcile:** surface dependency gaps, contradictions, stale sources, open
   Challenges, and prior negative Evidence without deleting any of them.
3. **Select one Obligation:** choose exactly one bounded, ready, budgeted question.
4. **Create isolated Branch:** use a separately approved `CREATE_BRANCH`
   lifecycle transition to bind the parent state and inputs while denying
   canonical writes. Later Branch lifecycle transitions affect only the
   container.
5. **Generate competing attacks:** create non-authoritative proposals and hostile
   challenges, including attempts to falsify assumptions and scope.
6. **Execute:** run only allowlisted, sandboxed, budgeted methods while capturing
   environment, seeds, directly bound tool/worker versions, stdout, stderr,
   timeouts, failures, and raw artifacts. `NOT_PRODUCED` or `NOT_APPLICABLE`
   capture statuses require an explicit reason. A `NOT_RUN` record has no
   execution-derived scientific Evidence; `UNSUPPORTED` can retain only typed
   administrative or capability diagnostics.
7. **Hostile review:** review provenance, method, scope, circularity, target
   insertion, fitting, reproducibility, and contradictory Evidence.
8. **Verify:** a dedicated versioned verifier evaluates every mandatory gate and
   fails closed on failed, unknown, unsupported, errored, or missing results. It
   also consumes the immutable object, graph, history, registry, approval, and
   replay package defined in `STATE_MACHINE.md` and performs every historical
   and cross-record check listed there.
9. **Propose Transition:** state the parent hash, exact post-state affected
   objects, explicit prior/replacement roles for a version change, scope change,
   evidence, challenges, one effect per stable ID, and the replay contract.
10. **Obtain human approval:** a distinct human governor approves, narrows, or
    rejects. There is no automatic merge.
11. **Receipt and replay:** record all distinct events, hash the receipt, replay
    the exact effects, and commit only if all authorization and replay conditions
    pass. A Branch merge at this step changes only its lifecycle; each contained
    Claim or Assumption still needs its own transition.

At any step the valid outcome may be no canonical change, a committed negative
diagnostic, a killed Obligation, quarantine, rejection, or a narrower proposal.

## Phase 0 Versus Future Enforcement

JSON Schema checks local record shape and contradiction. Phase 0 Python helpers
simulate a few relations between fields in one submitted document. Neither can
query a canonical history, authenticate a person, execute replay, or authorize a
transition. The future verifier contract in `STATE_MACHINE.md` is the sole
authoritative procedural specification; it remains unimplemented in Phase 0.
