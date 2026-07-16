# Authority Precedent

## Standalone Boundary

TS-LAB is an independent repository rooted at `/home/boggersthefish/TS-LAB`.
It has no runtime import dependency on BoggersTheAI and does not write into it.
BoggersTheAI is constitutional precedent only, not a writable dependency or
vendored implementation.

No nearby local checkout was available during Phase 0 planning. The public
repository `BoggersTheFish/BoggersTheAI` was inspected read-only on its `main`
branch at commit `73fd3e8ee9053e77a56367126ca64713004c5a59`.

## Sources Inspected

- `README.md`
- `ARCHITECTURE.md`
- `experiments/frontier/COGNITIVE_PHYSICS_ROADMAP.md`
- the `core/kernel/` directory inventory
- `core/kernel/ir.py`
- `core/kernel/receipts.py`
- `core/kernel/commit.py`
- `core/kernel/transaction.py`
- `core/kernel/kernel.py`
- `core/kernel/obligations.py`
- `core/kernel/replay.py`
- `tests/test_canonical_kernel.py`
- `interface/autonomous_loop.py`
- `interface/self_improvement.py`

The TSIR and TSReceipt references were the definitions in `core/kernel/ir.py`
and `core/kernel/receipts.py`; no separate TSIR or TSReceipt schema files were
present in the inspected tree.

## Principles Adopted

- Language and learned models may propose but cannot prove.
- Confidence, model identity, provider identity, eloquence, and volume have zero
  authority.
- Execution completion and evidence collection are not semantic proof.
- Evidence, verification, authorization, and commitment are distinct events.
- Unknown, unsupported, errored, missing, or failed mandatory results fail
  closed.
- Canonical change requires verifier-backed authorization, explicit provenance,
  a hash-linked receipt, and valid replay.
- Generated explanations are non-authoritative.
- Negative and rejected outcomes remain auditable.

## Deliberate Non-Copies

TS-LAB does not copy the BoggersTheAI graph runtime, TSKernel transaction path,
TSIR dataclasses, TSReceipt implementation, BOGVM execution, verifier code,
autonomous loop, background thread, self-improvement manager, confidence-based
quality gate, training pipeline, UI, adapters, or persistence.

Phase 0 does not implement TSKernel integration. Later compatibility must name
both contract versions, define an explicit adapter boundary, undergo human
review, and preserve TS-LAB authority rules even if an external system uses
different status or confidence semantics.

