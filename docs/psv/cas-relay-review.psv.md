# PSV Coverage Record — CAS certificate relay review (commits e0e5b4b..1ab316e)

Mode: GATE run (load-bearing-claims subset, GO/NO-GO before csr). Gate record is
**non-authoritative**; the authoritative full-M coverage record would follow csr.
Artifact under verification: the code-review report produced in this session.
Profile: external load-bearing citations (Alibaba Cloud API docs) — the recall
blind-spot zone, so the gate pays.

## oracle_verified_under_known_coverage

**N=5 verified / R=0 refuted / W=1 narrowed / K=0 unverifiable of M=6 claims.**

Gate signal: **GO** (no refuted claim; the single `narrowed` REFINES review
suggestion #2, it does not block csr). The review's load-bearing API facts hold
against fetched sources; one refinement (C5) is carried into csr/bc/pd.

## Authority registry (sources actually fetched)

| ref          | source                                                            | durability                       | fetched?                            |
| ------------ | ----------------------------------------------------------------- | -------------------------------- | ----------------------------------- |
| SRC-SLB      | help.aliyun.com …/classic-load-balancer/…/uploadservercertificate | external durable URL             | yes (full text)                     |
| SRC-CAS-UP   | help.aliyun.com …/ssl-certificate/…/uploadusercertificate         | external durable URL             | yes (full text)                     |
| SRC-CAS-LIST | help.aliyun.com …/ssl-certificate/…/listusercertificateorder      | external durable URL             | yes (full text)                     |
| SRC-FAQ      | help.aliyun.com …/faq-about-certificate-upload-failures           | external durable URL             | snippet only (page did not extract) |
| SRC-SDK      | .venv/.../alibabacloud_slb20140515/models.py                      | pinned dependency (semi-durable) | yes (read)                          |

No volatile (repo-external unversioned) authorities. SRC-FAQ is quote-grounded
via the search snippet derived from the official help domain; its claim is also
independently grounded by SRC-SLB's parameter definition, so the finding does
not rest on the snippet alone.

## Per-claim verdicts

(verified claims are counted, not listed; grounding noted for audit.)

### C1 — AliCloudCertificateRegionId is the CAS cert region, not the LB region — VERIFIED

Fetched quote (SRC-SLB, AliCloudCertificateRegionId param): _"阿里云签发证书所属的
地域 ID。 … 示例值: cn-hangzhou"_. Corroborated (SRC-FAQ snippet): _"该报错通常由
AliCloudCertificateRegionId 地域参数填写不当引起。调用该接口时需填写阿里云SSL证书
签发地域，而非CLB 实例所在地域。"_. Error code `InvalidParameter.AliCloudCertificateId`
(400, "The specified AliCloudCertificateId is invalid.") is listed in SRC-SLB.
The review's claim — and the 90215f1 fix — are source-correct.

### C2 — CAS cert names unique per account — VERIFIED

Fetched quote (SRC-CAS-UP, Name param):_"自定义的证书名称 … 说明 同一个用户下的证书
名称不能重复。"_ Directly grounds the duplicate-name constraint the idempotency
design relies on.

### C3 — ListUserCertificateOrder CertificateId == UploadUserCertificate CertId — VERIFIED (by convergence)

SRC-CAS-UP returns `CertId` (integer, "证书 ID"). SRC-CAS-LIST returns
`CertificateId` (integer, "证书 ID，当入参 OrderType=CERT 或者 UPLOAD 时返回"). Both
are the canonical certificate ID of the uploaded cert. The doc does NOT state the
equality verbatim; verdict is by convergence (same cert → same ID), no
contradiction found. Not a proof of equality.

### C4 — cas.aliyuncs.com endpoint stores certs in cn-hangzhou — VERIFIED (endpoint→region inferred)

SRC-SLB shows AliCloudCertificateRegionId example = `cn-hangzhou`; SRC-FAQ places
the SSL issuance region in mainland China. The specific "cas.aliyuncs.com →
cn-hangzhou" mapping is inferred from the example value + the CAS China-site
convention, not from an explicit endpoint-region doc statement.

### C5 — Keyword fuzzy + ShowSize pagination — NARROWED (highest-value finding)

SRC-CAS-LIST, Keyword param: _"模糊查询，匹配**域名或对应的资源 ID**。"_ and ShowSize:
_"分页，每页展示数据条数，默认 50。"_ with `CurrentPage` pagination.

- Verified sub-parts: keyword IS fuzzy (模糊查询); ShowSize default 50 caps a
  page; pagination via CurrentPage exists (code reads only page 1).
- NARROWED sub-part: the doc says Keyword matches **domain or resource ID**, NOT
  the certificate **name**. `find_existing_certificate_by_name` calls
  `keyword=<cert name>` (e.g. `lb-xxx-aabbccdd`), which is neither a domain nor a
  resource-ID format. The doc does NOT support keyword matching the name field.
  Implication: the lookup may return empty even when a same-name cert exists,
  making the "idempotent reuse by name" path **non-functional in the documented
  contract** (every retry would fall through to upload → duplicate-name error).
  This is a HIGHER-severity issue than the review's suggestion #2 (pagination):
  the real risk is keyword semantics, not page size.
- Cannot REFUTE (live API may match name despite the doc), but the code's
  reliance is **unsupported by the fetched source** → narrowed, escalate to csr.

### C6 — SLB UploadServerCertificate has direct-upload and CAS-reference modes — VERIFIED

SRC-SLB: `AliCloudCertificateId/Name/RegionId` notes _"如果使用阿里云签发证书…
该参数必选"_; `ServerCertificate/PrivateKey` notes _"如果上传非阿里云签发证书…
该参数必选"_. Two modes are explicit. (The "required by WAF" framing is the
review's use-case interpretation, not in this source — not a refutable factual
claim; the mechanics are grounded.)

## Carry-into-csr (refined from C5)

Review suggestion #2 ("increase show_size / paginate") is **partly mis-targeted**.
Source-grounded refinement for csr/bc/pd:

1. Do not rely on `keyword=<cert name>` to find a cert — the doc scopes keyword
   to domain/resource-ID. Prefer listing UPLOAD certs (paginate via CurrentPage)
   and enforcing the exact-name match client-side (already done via
   `item.name == name`), or confirm via live test that keyword matches name.
2. Pagination is still needed (ShowSize default 50, code reads page 1 only), but
   it is secondary to the keyword-semantics issue above.
