# Errors and retries

**Status:** Implemented — the taxonomy and retry behavior apply to all three SDKs; names differ by language idiom.

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

## Retries

Connection errors, timeouts, and 502, 503, and 504 are retried automatically with exponential backoff and full jitter, only where a retry is provably safe: every read, a write carrying an `Idempotency-Key` the server honors, a write with an existing dedup key, or a write whose HTTP method is inherently idempotent. Any other write gets exactly one attempt.

Achievement issuance carries an `Idempotency-Key`, so a retry cannot double-issue. Conversation sends can dedupe on a client-supplied entry id. Other writes, such as guild-message posts without a dedup key and schema or instance publication, are single-attempt, and callers should not assume otherwise. Defaults are 3 retries, 200 ms base delay, and a 10 s per-request timeout, configurable per client.

## Offline queuing is separate

Retries are not offline support: a call that fails still fails, synchronously, to the caller. The SDKs include an opt-in durable journal for queuing intent locally, but it is not drained automatically yet. See [synchronization](../architecture/synchronization.md) and [SDK design](../sdk/design.md#known-limitations).

## Related

- [SDK design](../sdk/design.md)
- [Capabilities](capabilities.md)
- [Building an integration](building-an-integration.md)
