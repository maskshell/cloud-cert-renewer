# Remediation Plan — CAS certificate relay (commits e0e5b4b..1ab316e)

Status: **csr substantive-converged** (process-axis). Outcome-axis (which fixes are
"right" to ship, priority, release scope) stays human. See convergence-record at
the bottom. Input = code-review report + psv gate record
(docs/psv/cas-relay-review.psv.md).

## Context (load-bearing facts)

> The psv record (docs/psv/cas-relay-review.psv.md) is a **non-authoritative GATE
> run** — the authoritative full-M coverage record would follow csr as a follow-up.
> Facts below are quoted from fetched Alibaba docs in that gate run; code-facing
> facts are verified against the repo in this csr pass.

- CAS `UploadUserCertificate` requires cert names unique per account (duplicate
  → error). [psv C2 verified]
- CAS `ListUserCertificateOrder` `Keyword` = fuzzy match on **domain or resource
  ID** — NOT cert name; `ShowSize` default 50, paginate via `CurrentPage`. The
  list response DOES expose `Name` (and `CertificateId`) for OrderType=CERT|UPLOAD.
  [psv C5 NARROWED; Name field confirmed in fetched SRC-CAS-LIST response]
- SLB `UploadServerCertificate` `AliCloudCertificateRegionId` = CAS cert region
  (cn-hangzhou), not LB region; fixed in 90215f1. [psv C1 verified]
- **CertId↔CertificateId identity (psv C3, VERIFIED-by-convergence, NOT a proof):
  `UploadUserCertificate` returns `CertId`; `ListUserCertificateOrder` returns
  `CertificateId` (both "证书 ID", integer, for uploaded certs). The doc does not
  state equality verbatim — the reuse path assumes they are the same ID. This is a
  load-bearing dependency that must be confirmed before Item 1 ships.**
- Current code `find_existing_certificate_by_name` queries `keyword=<cert name>`
  (unsupported by the doc) and reads only page 1 (`show_size=50`, no `CurrentPage`
  loop). `find_existing_certificate_by_fingerprint` (SLB path) has the SAME
  no-pagination defect.

## Remediation items (converged)

### Item 1 — CAS upload duplicate-name fallback + regression test (P1; gated by C3)

On `UploadUserCertificate` duplicate-name error, catch → re-lookup → reuse.
**Precondition:** first verify CertId↔CertificateId equivalence (live test or a
GetUserCertificateDetail source check) — the relookup returns `CertificateId`
while upload returns `CertId`; if they differ, the reuse returns the wrong ID.
**Caveat (F3):** the catch-and-relookup reuses `find_existing_certificate_by_name`,
so it inherits that lookup's failure modes (incl. swallowed list exceptions) — the
relookup must not route through the broken keyword path. **Test scope (F7):**
single-process TOCTOU only by default (helm `replicas:1`, no leader election found);
add a concurrent-replica test only if multi-replica deploy is confirmed supported.

### Item 2 — Make name-reuse lookup actually work (P0)

Do NOT rely on `keyword=<cert name>` (doc scopes keyword to domain/resource-ID).
Enumerate UPLOAD certs with `CurrentPage` pagination and enforce the exact
`item.name == name` match client-side (the `Name` response field is confirmed
present). _(Scope: CAS name-lookup only. The SLB-default path's
`find_existing_certificate_by_fingerprint` has the identical no-pagination gap but
is out of this CAS-relay plan's scope — track separately.)_ Item 1 is INSUFFICIENT without this — if lookup never finds the cert,
every retry hits the duplicate-name path Item 1 catches. Optionally validate live
that keyword matches name (if so, keyword can stay as a narrowing hint, not the
sole match).

### Item 2b — (NEW, from csr F2) CAS path lacks SLB-side reuse (P1)

`renew_cert` CAS branch always calls `UploadServerCertificate` referencing the CAS
cert with **no SLB-side fingerprint reuse check**, unlike the SLB-default branch
(`_upload_or_reuse_slb_cert` → `find_existing_certificate_by_fingerprint`). So the
CAS path **may** create an orphaned SLB `server_certificate` entry per invocation
even when the CAS cert is reused (SLB dedup for repeated `ali_cloud_certificate_id`
uploads is NOT documented in fetched sources — verify live, or treat conservatively).
Decide: add an SLB-side reuse check (mirror the
fingerprint path) OR explicitly declare it a non-goal. (This is the structural
cause behind Item 5's SLB-accumulation claim.)

### Item 3 — Helm template ASSERTIONS (P2)

CI already has a `helm-test` job (.github/workflows/ci.yml:416) that runs
`helm template` for default/CDN/SLB/webhook values — so rendering IS tested. The
gap is **assertions** on the rendered manifest: add grep/yq checks that
`LB_CERT_SOURCE` == `SLB_CERT_SOURCE`, and that `slb.certSource` falls through when
`lb.certSource` is unset (regression for the 1ab316e fallthrough fix).

### Item 4 — (DESCOPED, from csr F6) k8s/deployment.yaml sync

`LB_CERT_SOURCE`/`SLB_CERT_SOURCE` were introduced by **e0e5b4b** (feature), with
the lb→slb fallthrough added in 1ab316e. The static `k8s/deployment.yaml` is
**CDN-hardcoded** (`SERVICE_TYPE=cdn`), its LB env block is commented out, and it
has **no cert-source env at all** — it is not an active LB+CAS deploy path.
**Descope:** drop unless the k8s manifest is revived for LB; if revived, sync
`LB_CERT_SOURCE` then.

### Item 5 — Document certificate accumulation (P4, advisory)

Each renewal **with changed cert content** (new fingerprint → new name) creates a
new CAS cert; and per Item 2b the CAS path **may** create a new SLB entry per
invocation regardless (SLB dedup undocumented — verify live). Old CAS certs and orphaned SLB entries are never deleted.
Document the operational impact + a cleanup/lifecycle policy. Non-blocking.

## Convergence-record

- **substantive_converged: true (process-axis).** Core claims coverage-verified
  against fetched sources + repo; no new Blocker across rounds.
- **Size tier:** short (cap=2). **Rounds run:** round 1 (same-family F1–F8 +
  different-family DF1–DF3); round 2 (same-family confirmation — no new blocker).
- **R1 same-family (solidforge:doc-reviewer):** 8 findings, all warning/advisory,
  all accepted (verified: CI helm-test job exists; CAS branch has no SLB-side reuse;
  SLB fingerprint path unpaged; k8s manifest CDN-hardcoded).
- **R1 different-family (hetero_doc_review.py, deepseek; qwen3 malformed→skipped):**
  3 findings. DF1 (C3 omitted, BLOCKER) → accepted; DF2 (list `name` field) →
  RESOLVED by fetched SRC-CAS-LIST; DF3 (gate-record status) → accepted.
- **R2 same-family confirmation:** no new blocker; F4 (SLB-default pagination)
  resolved at disclosure level via an explicit scope note in Item 2; 2 advisory
  warnings (SLB-default pagination scoping; "every invocation" dedup claim) applied
  — the dedup-runtime claim softened to "may create … verify live".
- **Outcome-axis (human):** which items ship, priority, and release scope are not
  converged by csr — the P0/P1 ordering above is the plan's recommendation.
- **Follow-up:** authoritative psv full-M coverage record (post-csr) optional;
  CertId↔CertificateId live verification (Item 1 precondition).
