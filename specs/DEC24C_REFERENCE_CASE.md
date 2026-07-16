# DEC24-C Reference Case

This is a schema fixture, not a new physics derivation and not a report of new
measurements. Exact source artifacts and measurements were not available. The
examples therefore record only a qualitative comparison relation and abstract
gate observations; they deliberately contain no numerical metric, leakage, or
threshold value.

## Reference Scenario

`experiment.example.yaml` declares an execution contract comparing a target
metric with an abstract earlier-run Evidence fixture. `result.example.yaml`
records that execution completed and that the comparison relation was
`IMPROVED`. It separately records `FAIL` for exact gauge nullity and `FAIL` for
the required leakage gate. The Result is observation-only: it has no
`epistemic_class`, `transaction_state`, approval, proof, or commitment field.

The fixture's improvement label therefore cannot authorize the full-emergence
Claim. `evidence.example.yaml` retains the observation artifact.
`challenge.example.yaml` sustains the objection to promotion. A narrowly scoped
Claim records only the failed-gate knowledge as a committed
`NEGATIVE_DIAGNOSTIC`, and lists what it does not establish. The target emergence
interpretation is explicitly rejected by the proposed effects. A bounded
follow-up Obligation asks which declared mechanism explains the obstruction.

This describes the fixture's internal records only. It does not claim that a
physical metric empirically improved or that any physical emergence test was
performed.

## Required Separation

| Fixture record | Contract representation | Authority result |
|---|---|---|
| Qualitative metric improvement relative to earlier fixture | Result `comparisons[].relation: IMPROVED` with a baseline Evidence ID and no numerical fields | Observation only; not proof |
| Exact-nullity gate failure | Independent mandatory Result gate observation with `FAIL` | Blocks target promotion |
| Leakage gate failure | Independent mandatory Result gate observation with `FAIL` | Blocks target promotion |
| Useful failure knowledge | Retained Evidence plus a scoped `NEGATIVE_DIAGNOSTIC` Claim | Commit is limited to negative knowledge |
| Rejected interpretation | `REJECT` effect on the full-emergence target | Target is not promoted |
| Next question | Bounded obstruction-analysis Obligation | Candidate future work |

## Fixture Chain

1. `evidence_baseline.example.yaml` supplies the abstract earlier-run reference
   and explicitly declares that no empirical value is present.
2. `experiment.example.yaml` declares the method, inputs, two success gates,
   kill gate, environment, seed, tools, outputs, and completed execution record.
3. `result.example.yaml` records the qualitative improvement relation, two
   failed mandatory emergence gates, environment, seed, directly bound tool
   version, capture record, typed produced Evidence, and explicit limitations.
   It makes no interpretation.
4. `evidence.example.yaml` retains the abstract observation with provenance and
   execution context but no truth or authority field.
5. `challenge.example.yaml` sustains hostile review against full-emergence
   promotion.
6. `claim.example.yaml` commits only the scoped negative diagnostic through
   Decision, Receipt, parent-transition, and passing transition-gate lineage.
7. `obligation.example.yaml` opens one finite obstruction question with inputs,
   allowed and forbidden methods, gates, outputs, budget, and stop conditions.
8. `transition_proposal.example.yaml` commits the negative Claim, rejects the
   target interpretation, retains the Evidence, and creates the Obligation.
9. `decision.example.yaml` has passing mandatory verifier records and distinct
   human `APPROVE`, limited to those effects.
10. `research_receipt.example.yaml` separately records completed execution,
    Evidence recording, verifier satisfaction, authorization, replay, and
    canonical commitment for only the scoped transition.

Two IDs are intentionally pre-existing nodes outside this closed authored
fixture set: `claim:dec24c.full-emergence` is the target Claim being challenged,
and `obligation:dec24c.fixture.reference-evaluation` is the prior Obligation that
specified the reference Experiment. `transition_proposal.example.yaml` declares
exactly these nodes in the explicitly non-authoritative
`extensions.fixture.external_references` structure with role
`pre_existing_external_node`. The fixture-graph test recognizes that declaration
only in example/test context. It cannot satisfy Evidence, Decision, Receipt,
transition-lineage, or authorization requirements. In canonical operation the
future transition verifier must still require both objects to exist and match
their claimed types and hashes.

The fixture tests traverse these links. Reference existence, canonical hash
correctness, real replay reproduction, identity authenticity, and consistency
with an actual state mutation remain future transition-verifier duties because
Phase 0 has no canonical store or runtime.

## Verdict

The reference case preserves the required combination without overstating the
physics: a fixture comparison is labelled improved; both mandatory emergence
gates still fail; retained Evidence supports useful negative knowledge; the
target interpretation is not promoted; and a bounded follow-up Obligation is
opened. No empirical measurement or emergence result is claimed.
