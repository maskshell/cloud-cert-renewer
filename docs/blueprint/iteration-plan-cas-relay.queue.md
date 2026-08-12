---
queue_version: v1
frozen_at: 2026-08-12
plan_ref: docs/csr/cas-relay-remediation-plan.md
authority_chain:
  - docs/csr/cas-relay-remediation-plan.md
  - docs/psv/cas-relay-review.psv.md
status: frozen
---

# Plan Queue — iteration-plan

FROZEN plan interpretation emitted by blueprint-crafting `freeze`. Read-only for the executor; revise only via the Revision Channel (`status` -> `revising` -> edit + queue_version bump -> `status: frozen`). See parallel-development `references/plan-driven-mode.md`.

## Summary (checkpoint view)

6 item(s). DoD source: docs/csr/cas-relay-remediation-plan.md.

## Items

```json
[
  {
    "item_id": "G0",
    "seq": 0,
    "depends_on": [],
    "dod_ref": "#g0-dod",
    "title": "Verify CertId<->CertificateId equivalence (psv C3 precondition)",
    "scope": "Spike: confirm UploadUserCertificate.CertId == ListUserCertificateOrder.CertificateId for the same uploaded cert (psv C3 was 'not a proof'). Blocks I1.",
    "source_location": "docs/psv/cas-relay-review.psv.md (C3); docs/csr/cas-relay-remediation-plan.md Item 1 precondition",
    "parallel_group": "wave-1",
    "blueprint_subset": [],
    "producer": "blueprint-crafting",
    "plan_model_version": "v1"
  },
  {
    "item_id": "I2",
    "seq": 1,
    "depends_on": [],
    "dod_ref": "#i2-dod",
    "title": "Make CAS name-reuse lookup work (P0)",
    "scope": "find_existing_certificate_by_name: stop relying on keyword=<cert name>; paginate UPLOAD certs via CurrentPage + enforce exact item.name==name client-side.",
    "source_location": "docs/csr/cas-relay-remediation-plan.md Item 2; cloud_cert_renewer/clients/alibaba.py CasCertUploader.find_existing_certificate_by_name",
    "parallel_group": "wave-1",
    "blueprint_subset": [],
    "producer": "blueprint-crafting",
    "plan_model_version": "v1"
  },
  {
    "item_id": "I1",
    "seq": 2,
    "depends_on": ["G0", "I2"],
    "dod_ref": "#i1-dod",
    "title": "CAS duplicate-name fallback + regression test (P1, gated)",
    "scope": "upload_or_reuse_certificate: catch duplicate-name error from UploadUserCertificate, re-resolve by name (via fixed lookup), reuse. Regression test = single-process TOCTOU.",
    "source_location": "docs/csr/cas-relay-remediation-plan.md Item 1; cloud_cert_renewer/clients/alibaba.py CasCertUploader.upload_or_reuse_certificate",
    "parallel_group": "wave-2",
    "blueprint_subset": [],
    "producer": "blueprint-crafting",
    "plan_model_version": "v1"
  },
  {
    "item_id": "I2b",
    "seq": 3,
    "depends_on": ["I2"],
    "dod_ref": "#i2b-dod",
    "title": "CAS-path SLB-side reuse check (P1)",
    "scope": "renew_cert CAS branch: add SLB-side fingerprint reuse check mirroring find_existing_certificate_by_fingerprint before UploadServerCertificate, to avoid orphaned SLB entries.",
    "source_location": "docs/csr/cas-relay-remediation-plan.md Item 2b; cloud_cert_renewer/clients/alibaba.py LoadBalancerCertRenewer.renew_cert CAS branch",
    "parallel_group": "wave-2",
    "open_decisions": [
      {
        "id": "I2B-IMPL-VS-NONGOAL",
        "kind": "resolve-now",
        "resolution": "Implement the SLB-side reuse check (mirror find_existing_certificate_by_fingerprint). Chosen to prevent orphaned SLB server_certificate entries; if live testing later proves SLB dedups, downgrade to a documented non-goal."
      }
    ],
    "blueprint_subset": [],
    "producer": "blueprint-crafting",
    "plan_model_version": "v1"
  },
  {
    "item_id": "I3",
    "seq": 4,
    "depends_on": [],
    "dod_ref": "#i3-dod",
    "title": "Helm template assertions in CI (P2)",
    "scope": "Add assertions on the rendered helm manifest: LB_CERT_SOURCE==SLB_CERT_SOURCE and slb.certSource fallthrough when lb.certSource unset. CI helm-test job already renders.",
    "source_location": "docs/csr/cas-relay-remediation-plan.md Item 3; .github/workflows/ci.yml helm-test job",
    "parallel_group": "wave-1",
    "blueprint_subset": [],
    "producer": "blueprint-crafting",
    "plan_model_version": "v1"
  },
  {
    "item_id": "I5",
    "seq": 5,
    "depends_on": [],
    "dod_ref": "#i5-dod",
    "title": "Document certificate accumulation (P4, advisory)",
    "scope": "Document that renewals with changed content create new CAS certs and the CAS path may add SLB entries per invocation; old entries are never deleted. Add lifecycle/cleanup note.",
    "source_location": "docs/csr/cas-relay-remediation-plan.md Item 5",
    "parallel_group": "wave-1",
    "blueprint_subset": [],
    "producer": "blueprint-crafting",
    "plan_model_version": "v1"
  }
]
```
