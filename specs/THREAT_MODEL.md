# Threat Model

Assets include canonical research state, object provenance, immutable Evidence,
verifier rules, human approvals, receipts, replay behavior, scope boundaries,
and the distinction between proposal and authority. Phase 0 provides preventive
contracts and detection tests; runtime controls remain deferred.

| Threat | Attack or failure mode | Affected asset | Prevention | Detection | Response | Remaining risk |
|---|---|---|---|---|---|---|
| Hallucinated provenance | Producer invents a source, hash, or lineage | Provenance and Evidence | Required typed source records and hashes | Source/hash audit and replay | Reject transition; retain incident | External source authenticity still needs runtime verification |
| Assumption laundering | Premise is presented as Evidence or conclusion | Claims and dependencies | Explicit Assumption objects and links | Challenge dependency audit | Quarantine or reject Claim | Natural-language premises can remain subtle |
| Circular derivations | Claims support one another without an external base | Claim graph | Cycles constitutionally forbidden | Future graph cycle check | Reject transition and open Obligation | Cross-repository cycles may be hard to see |
| Target insertion | Desired conclusion is inserted into inputs or verifier rules | Evidence and verifier | Typed inputs and versioned ruleset hash | Hostile input/rule audit | Reject and preserve attempt | Semantically disguised targets need expert review |
| Claim scope drift | Wording silently broadens a prior Claim | Scope and canonical state | Versioned Claim plus scope classification | Scope diff and Challenge | Reject; require BROADER_SCOPE process | Semantic scope equivalence is difficult to automate |
| Correlated multi-agent agreement | Similar models repeat one error as consensus | Review independence | Agreement has zero authority | Provider/model correlation audit | Demand independent Evidence/verifier | Hidden shared training data remains possible |
| Reviewer capture | Reviewer aligns with proposer or suppresses objections | Challenge integrity | Reviewer non-authority and distinct human approval | Identity and review-history audit | Replace reviewer; retain captured review | Social pressure on humans remains |
| Easy-Obligation reward hacking | System selects trivial work to maximize completions | Research priorities | Priority inputs, blocked Claims, concrete gates | Portfolio and blocked-Claim audit | Reject low-value closure; revise priority | Value judgments require governance |
| Text volume as progress | Long outputs masquerade as evidence or work | Research record | Token volume and eloquence have zero authority | Artifact/gate-to-text ratio review | Ignore prose; require outputs | Human reviewers may still be persuaded |
| Hidden numerical fitting | Method is tuned after seeing target data | Experimental validity | Predeclared method, seed, inputs, gates | Artifact and provenance comparison | Quarantine Result; require reproduction | Undocumented manual tuning can escape capture |
| Unstable experiments | Results vary under identical declared inputs | Result reliability | Seeds and environment capture | Repeated deterministic replay | Mark FAILED or NEGATIVE_DIAGNOSTIC | Hardware nondeterminism may persist |
| Unreproducible experiments | Required artifacts or environment are absent | Evidence and receipts | Replay and environment required | Replay failure | Block authorization; retain failure | External services can disappear |
| Evidence deletion | Negative or contradictory artifacts are removed or made unreachable | Audit history | Evidence effects are limited to CREATE/RETAIN; immutable hashes and permanent retention | Future full-graph reachability and ledger audit | Fail closed; restore from immutable source | Phase 0 has no store or redundancy |
| Stale source ingestion | Obsolete source is treated as current | Provenance | Access timestamps and content hashes | Freshness policy review | Quarantine and re-ingest | Freshness thresholds are domain-specific |
| Malicious corpus content | Source attempts to corrupt interpretation | Inputs and Claims | Sources are non-authoritative and sandboxed later | Content and provenance challenge | Isolate source; reject induced effects | Subtle scientific misinformation remains |
| Prompt injection in documents | Document instructs a model to bypass policy | Proposals and interfaces | Document text has zero authority; strict output schemas | Injection scanning and effect audit | Discard proposal; retain source warning | Novel injections may evade filters |
| Self-modifying verifier attack | Verifier changes rules then approves the change | Verifier authority | Ruleset hash, approved registry lineage, and no self-approval | Future registry, ruleset-byte, producer, and approval-lineage comparison | Reject, restore reviewed verifier | Supply-chain compromise remains |
| Receipt tampering | Decision, hash, or effect is edited after creation | Receipts and state | Deterministic receipt hash and parent links | Hash validation and replay | Reject receipt; preserve tampered copy | Keyless hashes do not prove author identity |
| Dependency cycles | Object links form non-terminating authority chains | Object graph | Typed links and cycle prohibition | Whole-graph cycle analysis | Reject transition; break with explicit base | Phase 0 validates documents, not a live graph |
| Model-provider lock-in | Provider-specific metadata becomes authority | Portability and authority | Implementation-neutral schemas; identity zero | Schema and dependency audit | Remove provider coupling | Future adapters may leak assumptions |
| Conversational authority leakage | UI wording or chat action appears to commit truth | Canonical state | Interfaces are proposers only | Transition/receipt audit | Reject unreceipted change | Users may misread fluent output |
| LLM proposer authority leakage | LLM output bypasses verifier gates | Claims and transitions | Proposer non-authority and strict TransitionProposal | Missing gate/approval tests | Reject and log attempt | Bugs in future adapters remain |
| Confidence authority leakage | Score is used as approval or proof | Claim authority | Confidence absent from authority contracts and weight zero | Unknown-field and authority-basis tests | Reject transition | Confidence may influence humans informally |
| Scheduler authority leakage | Background job commits or promotes state | Canonical state | Background commits and daemons forbidden in v0.1 | Process and receipt audit | Stop scheduler; reject changes | Future operational misconfiguration |
| External-system authority leakage | QueryProcessor, AutonomousLoopManager, or confidence self-improvement writes truth | Boundary integrity | No runtime dependency; explicit versioned adapters later | Import/module and receipt audits | Disable adapter; quarantine output | External code can change independently |
| Stale BoggersTheAI assumptions | Copied precedent no longer matches TS-LAB policy | Constitution | Read-only precedent with explicit non-copies | Compatibility/version review | Update TS-LAB through governed spec change | Reference evolution can cause confusion |
| Extension override | Metadata introduces alternate approval, status, truth, verifier state, or commit | All canonical objects | Lowercase namespaces plus recursive reserved-key and string-value rejection; consumers ignore extensions for authority | Functional multi-depth schema mutations and policy audit | Reject object | Semantically encoded synonyms may avoid reserved words but remain non-authoritative |
| Compromised human approval | Approval identity or record is forged/stolen | Authorization | Required identity, timestamp, action, and approval hash | Future signature and identity verification | Block/revoke approval; issue rejection receipt | Phase 0 specifies no cryptographic identity system |
| Assumption adoption laundering | An adopted premise is presented as established truth | Claim and Assumption semantics | Assumption has no epistemic class; COMMITTED is scoped premise adoption with Decision/Receipt lineage and limitations | Future cross-record adoption and dependency audit | Reject or retract adoption while retaining its record | Semantic premise use still requires expert review |
| Branch merge laundering | Branch merge is treated as acceptance of contained work | Branch and contained objects | Branch has a separate lifecycle and Branch transitions can affect only Branch objects | Transition-effect and actual-delta comparison | Reject merge delta; require per-object transitions | Future mutation implementation must preserve container isolation |
| Contradictory effect set | One stable object ID receives incompatible actions, types, or hashes | Decision and transition integrity | One post-state effect per stable ID plus explicit prior/replacement roles | Shared local Phase 0 effect-set check and future actual-delta comparison | Reject the proposal or Decision; retain it for audit | Arbitrary array comparison is not expressible in JSON Schema alone |
| False receipt stage | An early stage boolean claims Evidence or verifier completion without its records | Receipt truthfulness | Independent stage conditionals require typed Evidence records and mandatory PASS outcomes | Schema-stage mutation tests and future canonical-record comparison | Reject Receipt before authorization | Canonical recording and verifier authenticity remain procedural |
| Unsupported-result laundering | `NOT_RUN` or `UNSUPPORTED` is used to claim an improvement or scientific Evidence | Result and Evidence integrity | Outcome matrix forbids execution facts for `NOT_RUN` and permits only typed administrative/capability diagnostics for `UNSUPPORTED` | Schema mutations plus future semantic Evidence review | Reject Result or quarantine downstream interpretation | Prose semantics still require expert review |

## Response Priority

Any suspected authority bypass fails closed before canonical commitment. Preserve
the proposal, source artifacts, negative Evidence, Challenges, and response
Decision. Do not rewrite the incident as absence. Compromise of verifier or
human-approval records requires an independent human review before any new
transition can be authorized.

Phase 0 schema checks and Python test helpers are preventive contract evidence,
not runtime controls. Historical reference existence, content-hash correctness,
true parent state, Evidence reachability, dependency cycles, novelty, actual
Challenge consideration, identity authenticity, verifier registry membership,
ruleset and version lineage, semantic scope comparison, and replay reproduction
remain explicit future transition-verifier duties.
