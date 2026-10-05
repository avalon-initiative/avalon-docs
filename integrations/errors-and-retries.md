# Errors and retries

**Status:** Partially implemented — the error taxonomy applies to all three SDKs; automatic retries exist only in the Rust SDK.

Every SDK maps failures into a small, stable set of categories, so a game does not need to understand HTTP. This page is the integrator-facing summary; the design rationale is in [SDK design](../sdk/design.md#errors-and-retries).

## Categories and what to do

| Category | Meaning | Typical response |
| --- | --- | --- |
| Unauthorized | The session token is stale or rejected. | Re-authenticate. |
| Capability not granted | The token is valid but the grant is missing or was revoked. | Ask the person to grant it. See [capabilities](capabilities.md). |
| Not found | The resource does not exist. | Treat as absent. |
| Conflict | Already exists or already in that state. | Treat as done, or reconcile. |
| Rejected | A final server decision. | Do not retry unchanged. |
| Unavailable | A transient node failure. | Surface as "try again later", not a gameplay error. |
| Protocol | An unexpected response shape. | Likely a version mismatch; upgrade. |

Each category carries the server's stable machine-readable `code`, which is safe to match on when finer handling is needed. The code is not free text and does not change when wording changes. Language-specific extras exist (for example a distinct conversation-participant error and missing-issuer-credentials error).

## Session calls

Revoking a session that is not the caller's, whether the id is unknown or belongs to another identity, returns 404 with the code `SESSION_NOT_FOUND`. It lands in the not-found category in every SDK, and the code is available as a string to match on. Treat it as already gone: the session either never existed for this identity or has already ended. Listing and logging out have no code of their own. A logout with a token that is already ended or expired is an ordinary unauthorized failure. See [SDK design](../sdk/design.md#the-callers-own-login-sessions).

## Retries

Automatic retries are implemented in the Rust SDK only. The TypeScript and C# SDKs do not retry: each call is a single attempt, and a caller that wants retries applies its own policy around the call.

The Rust SDK retries connection errors, timeouts, and 502, 503, and 504 with exponential backoff and full jitter, only where a retry is provably safe: every read, a write carrying an `Idempotency-Key` the server honors, a write with an existing dedup key, or a write whose HTTP method is inherently idempotent. Any other write gets exactly one attempt. Defaults are 3 retries, 200 ms base delay, and a 10 s per-request timeout, configurable per client.

## Duplicate achievement issuance

A retry cannot double-issue only when every attempt carries the same `Idempotency-Key`. The server caches the first successful issuance response per integrator, key, and endpoint and replays it for a repeat of that key, for single and bulk issuance (achievements and milestones). Without a repeated key the server has no other protection: there is no uniqueness on issued attestations, each issuance gets a fresh attestation id, and two issuances of the same achievement to the same identity are two valid attestations (a repeatable achievement relies on this).

- The Rust SDK generates one key per logical issuance call and reuses it across its internal retries of the whole challenge-then-issue exchange, so its own retries do not double-issue.
- The TypeScript and C# SDKs generate a fresh key on every call and never retry. A caller that retries the call itself after a lost response sends a new key, and the server issues a second attestation. To make an application-level retry safe, issue through the Rust SDK or avoid retrying issuance blindly: read the identity's attestations first and issue only if the achievement is absent.
- Two concurrent requests with the same key can both pass the cache lookup before either stores its response, so both issue; the cache protects sequential retries.
- Cached responses are not pruned today.
- Undecided: a server-side policy for duplicate issuance of the same achievement. Until one is decided, the behavior above is the whole guarantee.

Conversation sends can dedupe on a client-supplied entry id. Other writes, such as guild-message posts without a dedup key and schema or instance publication, are single-attempt, and callers should not assume otherwise.

## Offline queuing is separate

Retries are not offline support: a call that fails still fails, synchronously, to the caller. The SDKs include an opt-in durable journal for queuing intent locally, but it is not drained automatically yet. See [synchronization](../architecture/synchronization.md) and [SDK design](../sdk/design.md#known-limitations).

## Related

- [SDK design](../sdk/design.md)
- [Capabilities](capabilities.md)
- [Building an integration](building-an-integration.md)
