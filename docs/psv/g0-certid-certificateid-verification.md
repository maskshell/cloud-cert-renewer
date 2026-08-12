# G0 — CertId ↔ CertificateId live-verification gate (OPEN)

Status: **OPEN — pending live verification.** Cannot be completed without Alibaba
Cloud credentials. This is the blocking precondition for shipping Item I1
(CAS duplicate-name fallback) to production.

## Why this gate exists

psv C3 (docs/psv/cas-relay-review.psv.md) verified by convergence — but NOT by
proof — that the ID returned by `UploadUserCertificate` (`CertId`) equals the
`CertificateId` returned by `ListUserCertificateOrder` for the same uploaded
certificate. Both are documented as "证书 ID" (integer) for uploaded certs, but
the Alibaba docs do not state the equality verbatim.

Item I1's catch-and-relookup path (`upload_or_reuse_certificate`) crosses these
two fields: it looks up an existing cert via `ListUserCertificateOrder` and
returns the `CertificateId`, which is then passed as SLB's `AliCloudCertificateId`
(the same slot `UploadUserCertificate`'s `CertId` fills). If the two IDs differ,
the relookup would reuse the WRONG ID.

## How to verify (live)

1. With a real Alibaba Cloud account (RAM: `yundun-cert:UploadUserCertificate`,
   `yundun-cert:ListUserCertificateOrder`), upload a test cert via
   `UploadUserCertificate` and record the returned `CertId`.
2. Call `ListUserCertificateOrder` with `OrderType=UPLOAD` and find the cert by
   name; record its `CertificateId`.
3. Confirm `CertId == CertificateId` (as integers/strings).
4. (Optional but recommended) also confirm the same value works as SLB's
   `AliCloudCertificateId` in an `UploadServerCertificate` reference upload.

## While G0 is open

- The I1 code + unit tests are merged (mocked), but I1 must NOT be relied on in
  production until G0 is recorded PASS here.
- The `_is_duplicate_name_error` matcher (alibaba.py) ALSO needs its real
  duplicate-name error code/string confirmed live (it currently matches on
  generic indicators) — track alongside G0.

## On resolution

Record the result (PASS/FAIL + evidence) in this file and close the gate. If
FAIL (IDs differ), redesign I1 to map `CertificateId → CertId`.
