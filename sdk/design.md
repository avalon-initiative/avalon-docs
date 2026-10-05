# SDK design

**Status:** Partially implemented — the capability model, session types, error taxonomy, codegen, and conformance suite are implemented; the fluent high-level facade shown under "Target shape" is Planned.

Avalon SDKs expose protocol capabilities, not infrastructure. A developer thinks in identity, guilds, achievements, presence, and integrator event verification, never in database instances, indexer shards, or node addresses. This page is the language-agnostic design that all three official SDKs (Rust, C#, TypeScript) share.

## Target shape

**Planned.** The intended developer experience is a small facade with no infrastructure in sight:

```text
avalon = Avalon.connect()
identity = avalon.identity(user_id)
friends  = identity.friends()
guilds   = identity.guilds()
avalon.presence().publish(...)
avalon.achievement("dragon_slayer").issue(user_id)
```

and never `Avalon.connect("postgres://...")`, or a choice of database, cache, region, or node. Today's SDKs are lower level than this: a client is constructed with a server URL (or resolved from a target network) and an integrator credential, then `authenticate` yields a capability-gated session. See [known limitations](#known-limitations).

## What the SDK abstracts

| Concern | Hidden from the integrator | State |
| --- | --- | --- |
| Node discovery and selection | Latency, health, roles | Partially implemented: `connect` resolves a target network to a verified node with no URL supplied and picks the lowest measured round trip; peer-set expansion and health/role ranking are not used |
| Authentication | Identity session exchange, integrator credential | Implemented |
| Capability negotiation | Which node roles are reachable | Implemented for a known URL: a node reports its own roles |
| Retries | Transient failures | Partially implemented: the Rust SDK retries idempotent calls only; the TypeScript and C# SDKs do not retry |
| Realtime connections | Presence and message transport | Implemented (WebSocket subscriptions) |
| Settlement submission | Batching, commitments | Implemented server-side; the SDK submits and does not see batching |
| Verification | Signature checks, key resolution, history walks | Implemented; the SDK returns authenticity and validity as separate results |
| Indexing topology | Which projection served a read | Implemented (opaque to the client) |
| Offline and deferred participation | Whether a call went out now or was journaled | Partially implemented: a journal exists, but the SDK does not drain it automatically |

See [nodes](../architecture/nodes/README.md), [settlement](../architecture/settlement.md), and [synchronization](../architecture/synchronization.md) for what these hide.

## Verification returns separate answers

Per the [trust model](../protocol/trust-model.md), an attestation is authentic, valid, and recognized as three separate answers. The SDK returns authenticity and validity as computed by the server and deliberately has no recognition field. An integrator can:

- show every authentic and valid claim with provenance (a Hub-style view), and
- apply gameplay effects only to claims it recognizes under its own policy.

Collapsing these into one boolean would make the SDK the judge of meaning, an authority Avalon does not have.

## Capability checks per method

A capability-gated session is scoped to the capabilities the person granted the integrator under an active [binding](../protocol/bindings.md). Each method names the capability it needs (for example reading achievements requires `achievements.read`, issuing requires `achievements.issue`), and a call without the grant fails with a capability error instead of returning less.

Capabilities are permanent wire strings, not language enum names. An SDK preserves a capability string it does not recognize instead of failing, so a newer server never breaks an older SDK. The client-side check is a fast failure, not the security boundary: the server enforces the same check on every request. The capability list is in [integrations: capabilities](../integrations/capabilities.md).

## Two session types

- **Integrator session** (capability-gated): a game, app, or service authenticating with its own credential, scoped to what an identity granted it.
- **Account session** (first-party): a client acting as an identity itself, for registration, login, recovery, passkeys, devices, its own login sessions, guild administration, friends, conversations, and integrator consent. Not gated by capability grants.

The two share no conversion in either direction in any SDK, and no account-session constructor accepts an integrator credential. An integrator credential can therefore never yield account-level power, by construction. Within an account session most actions rely on the session bearer token; a smaller named set also requires a fresh Ed25519 signature from the identity's own signing key, which the SDK produces automatically. See [identity](../protocol/identity.md) for the two authorization tiers.

### The caller's own login sessions

An account session can list, end, and log out of the identity's login sessions. These calls act on the session record on the node, not on the SDK object alone. Available on the SDK main branch and in the next release.

| Call | Rust | C# | TypeScript | Route |
| --- | --- | --- | --- | --- |
| List live sessions | `list_sessions()` | `ListSessionsAsync` | `listSessions()` | `GET /me/sessions` |
| End one of the identity's sessions | `revoke_session(id)` | `RevokeSessionAsync` | `revokeSession(id)` | `POST /me/sessions/{id}/revoke` |
| End the session in use | `logout()` | `LogoutAsync` | `logout()` | `POST /sessions/logout` |

- **Listing** returns only live sessions, so an expired session never appears, newest first by creation time. Each summary carries:
  - `id`: the session's id, which is what revoke takes. It is not the bearer token, which the node stores only as a hash and never returns.
  - `created_at` and `expires_at`: when the session was minted and when it lapses if never ended. A session lasts 30 days from minting.
  - `current`: true on the session the listing request itself authenticated with, so a client can tell "this device" from the others.
  - `origin_passkey_id`: set when the session came from a passkey login, and empty otherwise.
  - `origin_signing_key_id`: set when the session came from device pairing or a cross-node login, and empty otherwise. It names the signing key that approved the pairing or signed the grant.

  A session is never minted without an origin, and every minting path sets exactly one. Revoking that passkey or signing key ends the session, so the origin ids show which sessions a credential revocation would take down. See [identity authentication](../protocol/identity/authentication.md#sessions). The field names are snake case on the wire and in Rust, `OriginPasskeyId` and `OriginSigningKeyId` in C#, and `originPasskeyId` and `originSigningKeyId` in TypeScript, where a missing origin is `null`.
- **Revoking** ends one session of the calling identity, and the current one is allowed. A session id that does not belong to the caller, whether unknown or another identity's, is refused with a 404 whose code is `SESSION_NOT_FOUND`. The SDKs pass the code through as a string in their not-found category (see [errors and retries](../integrations/errors-and-retries.md#session-calls)).
- **Logging out** ends the session this account object authenticates with. The token is unusable afterwards, so every later call on that object fails as unauthorized, and so does a second logout.

Integrators are deliberately unable to create guilds, invite, kick, change roles, or manage channels on a person's behalf. Those are identity-authority actions.

## Errors and retries

Every SDK maps failures into a small, stable, protocol-level taxonomy, never a raw HTTP client error:

| Category | Meaning |
| --- | --- |
| Unauthorized | The session token is stale or rejected. |
| Capability not granted | The token is fine but the grant is missing or revoked. |
| Not found | The resource does not exist. |
| Conflict | Already exists, or already in that state. |
| Rejected | The server made a final decision; do not retry unchanged. |
| Unavailable | A transient node failure; safe to surface as "try again later". |
| Protocol | An unexpected response shape, typically a version mismatch. |

The category is chosen by HTTP status. The message carried inside it is the server's stable machine-readable `code`, never free text that may be reworded, and every SDK exposes that code so callers can tell apart failures that share a status.

**Retries.** In the Rust SDK, connection errors, timeouts, and 502, 503, and 504 are retried with exponential backoff and full jitter, but only for calls that are provably safe: every read, a write carrying an `Idempotency-Key` the server honors, a write with an endpoint-specific dedup key, or a write whose HTTP method is idempotent. Any other write is attempted once. Defaults are 3 retries, 200 ms base delay, 10 s per-request timeout, and they are configurable per client. See [integrations: errors and retries](../integrations/errors-and-retries.md).

## Generated types and hand-written logic

Wire types are generated from the server's OpenAPI document: `typify` for Rust, `openapi-typescript` for TypeScript, and NSwag for C#. The generated file is a checked-in artifact for C# and TypeScript and a build output for Rust. Opaque WebAuthn ceremony blobs, WebSocket push payloads, and pure signature-only wrapper bodies stay hand-written. Everything that signs bytes is hand-written and must be covered by a conformance vector.

The Rust SDK has no dependency on any protocol-repository crate, so it is structurally the same kind of thing as the C# and TypeScript SDKs. The cost is that client and server are no longer compiler-guaranteed to sign the same bytes. The conformance suite replaces the compiler.

## Cross-SDK conformance

Shared vectors under `conformance/vectors/` hold canonical inputs and outputs, one JSON file per behavior. Each names the SDKs that implement it (`supportedIn`) and, for the rest, why not (`notSupported`). The server asserts its implementation against the same files, and each SDK has a thin runner. Covered behaviors:

| Vector | Rust | C# | TypeScript |
| --- | --- | --- | --- |
| Attestation issuance, bulk, and revocation signing bytes | yes | yes | yes |
| Cross-node login grant signing | yes | yes | yes |
| Signed tree head | yes | yes | yes |
| Self-certifying tree head | yes | yes | yes |
| Witness announce and witness-cosigned tree head | yes | yes | yes |
| Known-list selection | yes | yes | yes |
| Session-continuation token | no | no | yes |
| WebSocket interest-claim handshake | no | no | yes |
| BIP39 mnemonic-derived signing keys | no | no | yes |

Runners that lack a behavior assert the gap explicitly with a named skip citing the vector's `notSupported` entry rather than faking an implementation. The convention: add a vector in the same change that lands any new smart-client behavior in any SDK. The vector schema is documented with the vectors. See [protocol API](../protocol/api.md).

## Self-certifying shard heads

A shard whose id is `node:<sha256-of-key>` is named by the SHA-256 of the raw Ed25519 public key that signs its tree heads. A node serves that key as an optional `signing_public_key` next to the head (outside the signed bytes). All three SDKs verify such a head from the key and id alone, with no trust anchor, registry, or witness list, and report the first failing check: not self-certifying, missing key, malformed key (not a canonical, non-small-order point), key/id mismatch, or bad signature. Verification is cofactorless and identical in the server and all SDKs. A verified head proves the key holder signed it and that the key belongs to the id. It does not prove the shard is honest or current. A dispatcher decides which check applies to an id: `node:` ids use this one, `core` uses network and witness verification, and any other kind never verifies. See [network trust anchors](../protocol/network-trust-anchors.md) and [witness cosigning](../protocol/witness-cosigning.md).

## Route coverage check

A script in the SDK repository diffs the server's SDK-facing route table (method plus normalized path) against each SDK's actual call sites and fails naming the uncovered routes. A small allowlist covers the WebAuthn ceremony endpoints the C# SDK deliberately does not port. All three SDKs currently report full coverage.

## Known limitations

- **Discovery is real but unranked.** All three SDKs can resolve a target network (an exact `network_id` or a deployment tier) to a live server. Candidates come only from the trust-anchor entries' server URL and seed nodes, are verified with the same signed-tree-head check as an explicit URL, timed in parallel, and the fastest wins. Rejected candidates are retained with reasons. Explicit URLs remain fully supported. No SDK yet expands the peer set from the server's discovery endpoint or ranks by health or role. Topology walking, probe, and trace are available in all three and are advisory: every hop is self-reported by the node it names.
- **Visibility scoping.** Presence and guild rosters are scoped by the subject's visibility setting. The server also filters guild channel lists and message reads by per-channel view permission (role overrides and a public-channel baseline for non-members of public guilds). Some SDK source comments still describe channel reads as unscoped; that text predates the server behavior and is stale.
- **Idempotency-key coverage is partial.** Achievement issuance carries an `Idempotency-Key`, but only the Rust SDK reuses it across retries; the TypeScript and C# SDKs send a fresh key per call and do not retry, so a caller-level retry can issue a second attestation (see [errors and retries](../integrations/errors-and-retries.md#duplicate-achievement-issuance)). Conversation sends can dedupe on a client entry id. Other unkeyed writes are single-attempt.
- **Per-language gaps.** C# does not drive a WebAuthn ceremony. Session continuation on 401, the signed interest-claim WebSocket handshake, and BIP39 mnemonic-derived keys exist in TypeScript only.
- **No server-side SDK-version compatibility enforcement.** Each SDK embeds the schema version it was generated against, but the server does not check it.
- **No automatic journal drain.** The sync journal is a durable local queue. Submitting its contents is not automatic yet.

## Implementation

The SDKs live in [avalon-sdks](https://github.com/avalon-initiative/avalon-sdks): [Rust](https://github.com/avalon-initiative/avalon-sdks/tree/main/languages/rust), [C#](https://github.com/avalon-initiative/avalon-sdks/tree/main/languages/csharp), [TypeScript](https://github.com/avalon-initiative/avalon-sdks/tree/main/languages/typescript), plus the [conformance vectors](https://github.com/avalon-initiative/avalon-sdks/tree/main/conformance/vectors). Method-level surfaces per language are documented there.

## Related

- [SDKs overview](README.md)
- [Language support](language-support.md)
- [Building an integration](../integrations/building-an-integration.md)
- [Trust model](../protocol/trust-model.md)
- [Bindings](../protocol/bindings.md)
- [Synchronization](../architecture/synchronization.md)
