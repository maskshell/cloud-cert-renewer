# Iteration Plan — CAS certificate relay remediation

- artifact_type: iteration-plan
- authority_chain: docs/csr/cas-relay-remediation-plan.md (master, csr substantive-converged) → docs/psv/cas-relay-review.psv.md (psv gate, fetched-source-grounded)
- conflict_rule: on conflict, the csr-converged remediation plan wins; psv narrows/refines it.
- rightness: human_confirm_required (outcome axis — which fixes ship, priority, release — is human).

This is the authoritative reference `parallel-development` consumes to implement. It
is process-axis convergence only; it does NOT assert the fixes are the "right" ones.

## Positioning / scope

Implement the converged CAS-relay remediation items (P0–P4) from
docs/csr/cas-relay-remediation-plan.md, each gated by its settled design and the
psv-grounded live-verification gates. Platform: Python (uv, pytest, ruff).

## Complexity tiers (anchor: complexity-tiers)

- S — spike/verification or single-file config/test addition (G0, I3, I5).
- M — focused logic change in one module + its unit tests (I2, I1, I2b).

## Work items (queue)

### G0 — Verify CertId↔CertificateId equivalence (S, blocking gate for I1)

psv C3 marked the equality of `UploadUserCertificate.CertId` and
`ListUserCertificateOrder.CertificateId` as "verified by convergence, NOT a proof".
Before I1 ships its catch-and-relookup (which crosses these two fields), confirm
equality. Files: none (spike) → record evidence in docs/psv/. Done when: a live test
or GetUserCertificateDetail source check records that the IDs match for the same
uploaded cert; if they differ, I1 is redesigned to map CertificateId→CertId.

### I2 — Make CAS name-reuse lookup work (M, P0) ← highest priority

`find_existing_certificate_by_name` currently relies on `keyword=<cert name>`, but
the CAS doc scopes `Keyword` to domain/resource-ID. Stop relying on keyword for the
match: enumerate UPLOAD certs via `CurrentPage` pagination and enforce the exact
`item.name == name` client-side (the `Name` field IS in the list response; the filter
already exists). Files: cloud_cert_renewer/clients/alibaba.py, tests/test_clients.py.
Done when: lookup finds a same-name cert when keyword does not narrow to it; pagination
loop present; existing unit tests pass + new test for keyword-doesn't-match-name case.

### I1 — Duplicate-name fallback (M, P1, gated by G0 + I2)

In `upload_or_reuse_certificate`, catch the duplicate-name error from
`UploadUserCertificate`, re-resolve by name, reuse. The relookup MUST NOT route
through the broken keyword path (it now paginates). Files: cloud_cert_renewer/clients/
alibaba.py, tests/test_clients.py. Done when: a duplicate-name error is caught and the
existing cert is reused; regression test = single-process TOCTOU (helm replicas:1, no
leader election). Depends on G0 (ID equivalence) and I2 (working lookup).

### I2b — CAS-path SLB-side reuse (M, P1)

`renew_cert` CAS branch calls `UploadServerCertificate` unconditionally with no
SLB-side fingerprint reuse (unlike `_upload_or_reuse_slb_cert`), so it may orphan an
SLB `server_certificate` entry per invocation. Decision (resolved): add an SLB-side
reuse check mirroring `find_existing_certificate_by_fingerprint` before the CAS
UploadServerCertificate. Files: cloud_cert_renewer/clients/alibaba.py, tests/test_clients.py.
Done when: CAS branch reuses an existing SLB entry with a matching fingerprint instead
of always creating one. **Caveat:** `find_existing_certificate_by_fingerprint` itself
reads only page 1 (see out-of-scope SLB-default pagination), so an SLB entry beyond
page 1 will not be found until that gap is fixed; the DoD holds for page-1-visible
entries. Depends on I2 (coordination).

### I3 — Helm template assertions (S, P2)

The CI `helm-test` job (.github/workflows/ci.yml:416) already renders templates; add
ASSERTIONS on the rendered manifest: `LB_CERT_SOURCE` == `SLB_CERT_SOURCE`, and
`slb.certSource` falls through when `lb.certSource` is unset. Files: .github/workflows/ci.yml.
Done when: CI fails on a regression that desynchronizes the two env vars or breaks fallthrough.

### I5 — Document certificate accumulation (S, P4, advisory)

Document that each renewal with changed content creates a new CAS cert (fingerprint→name)
and the CAS path may add an SLB entry per invocation; old entries are never deleted.
Add a lifecycle/cleanup note. Files: README.md (or docs/). Done when: operational note merged.

## Dependency edges + DAG (anchors: dependency-edges, dag)

```
G0 ──► I1
I2 ──► I1
I2 ──► I2b   (coordination / same-file conflict-avoidance, NOT a data dependency)
I3  (independent)
I5  (independent)
```

- G0 → I1 (ID equivalence must be confirmed before the catch-and-relookup).
- I2 → I1 (the relookup must use the fixed lookup, not the broken keyword path).
- I2 → I2b (coordination only: both edit alibaba.py idempotency code; no data/control dependency — could be parallelized with care).
- I3, I5 are independent (parallel-safe).

Parallel fan-out: {G0, I2, I3, I5} can start together; I1 follows once G0+I2 land; I2b follows once I2 lands.

## Per-iteration definition of done (anchor: per-iteration-dod)

Each item's DoD is its "Done when" line above. Shared DoD for ALL code items:
`uv run pytest -q` green; `uv run ruff check .` clean; relevant unit test added/updated;
no regression in tests/test_clients.py, tests/test_config.py, tests/test_providers_adapter.py.

## Phase acceptance gates (anchor: phase-acceptance-gates)

- Gate A (pre-I1): G0 evidence recorded (CertId↔CertificateId confirmed or I1 redesigned).
- Gate B (P0 merge): I2 merged — the idempotency feature is now functional.
- Gate C (P1 merge): I1 + I2b merged — duplicate-name resilience + SLB reuse.
- Gate D (release): full `uv run pytest` + `ruff` green; version re-bump (the 6a05ee0
  bump was reset) after all intended items land.

## Risks and mitigations (anchor: risks-mitigations)

- R1 — live API behavior diverges from doc (keyword may match name in practice; SLB
  may dedup). Mitigation: I2 still works if keyword matches (it's a superset approach:
  paginate + filter); I2b's reuse check is correct regardless of dedup.
- R2 — CertId ≠ CertificateId (G0 fails). Mitigation: I1 redesigned to map the ID;
  G0 is a blocking gate, so this surfaces before I1.
- R3 — pagination changes list-call cost/QPS (CAS list QPS limit 10/s). Mitigation:
  page size 50, small loop; acceptable for renewal cadence.

## Out of scope (anchor: out-of-scope)

- SLB-default path pagination (`find_existing_certificate_by_fingerprint` has the same
  no-pagination gap) — tracked separately, NOT in this CAS-relay plan (csr F4, disclosed).
- k8s/deployment.yaml sync — that manifest is CDN-hardcoded, LB block commented, no
  cert-source env; not an active LB path (csr F6, Item 4 DESCOPED).
- Multi-replica concurrency/leader-election — single-process TOCTOU test only (csr F7).
- Authoritative psv full-M coverage record (post-csr) — optional follow-up.

## Cross-cutting tasks (anchor: cross-cutting-tasks)

- Version re-bump (pyproject/Chart.yaml/**init**/uv.lock) AFTER the chosen items merge
  (the 6a05ee0 bump was selectively reset this session).
- CHANGELOG entry under a new [Unreleased]/[0.3.2] block once items land.
- All code items follow the existing patterns in alibaba.py (CloudApiError wrapping,
  logger.warning/idempotency-check-fallback style).
