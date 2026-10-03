# Security Model

**Status:** Partially implemented — authority scoping, key handling, and the ledger guarantees are built; server-side capability enforcement covers only some routes, and TLS is a deployment requirement and not a built-in.

Authority in Avalon is scoped. No single actor (an integrator, a node operator, the network itself) is omnipotent: users control their identity, integrators control their own worlds and attestations, guilds govern themselves, and infrastructure transports, indexes, settles, and verifies without owning any of it. Hosted infrastructure is not protocol authority.

## Who controls what

| Actor | Controls | Cannot |
| --- | --- | --- |
| **User** | identity keys; profile declarations; social actions; permission grants and visibility; guild participation | issue attestations about themselves; rewrite issued history |
| **Integrator** | its bindings and integrator-side characters; attestations under its own issuer key; its recognition policy | touch another integrator's profile or characters; issue under another issuer's identity; alter an identity's history or unrelated guild history |
| **Guild** | governance, membership, roles, settings, channels | act as an issuer; reach into a member's other data |
| **Avalon infrastructure** | transport, indexing, settlement, discovery, verification | fabricate an issuer claim; fabricate an identity; silently become the owner of user or integrator data |

Details per actor: [identity](./identity.md), [bindings](./bindings.md), [guilds](./guilds.md), [nodes](../architecture/nodes/README.md).

## Authorization: one capability, one check

An endpoint an integrator calls on a user's behalf must check the specific capability it needs, never a blanket "does this integrator have access to this user". Two caller kinds exist: a **user** acting on their own data (always allowed), and an **integrator acting for a user**, which needs both an active [binding](./bindings.md) and an active `PermissionGrant` (see [privacy](./privacy.md)) for exactly the capability the endpoint names.

The server implements this as one shared check (`Caller::User` or `Caller::Integrator` and `require_capability`), a plain function called explicitly per handler, whose capability argument is mandatory so a call site cannot accidentally check nothing. A revoked grant is rejected on the very next request, since each check reads the grants fresh (there is deliberately no cache: a wrong invalidation rule would violate "revoked is rejected immediately"). A failure is a 403 with an identical body regardless of why (no binding, wrong integrator, no grant, revoked grant). The integrator caller resolves by the pair (identity id, integrator id) and not by a `binding_id` it names, so using one user's binding against a different integrator is a lookup miss and not a check that fails after the fact.

**Limit:** this server-side check is currently called only from integrator write paths: `presence.publish` and attestation issuance (`achievements.issue`, `milestones.issue`). Reads such as friends and guild rosters accept only an identity's own session, and the SDKs check capabilities client-side against that session. Server-side capability enforcement for integrator reads is [planned](./social-graph.md#what-an-integrator-sees).

## Node authority

```text
Integrator A
    signs:  Dragon Slayer -> User X   (issuer key)

Hosted Avalon node
    transports, indexes, settles that claim
    cannot replace Integrator A's signature
    cannot produce "Integrator A issued ..." when Integrator A did not
```

This holds because every durable claim of that kind is signed by the party with authority over it and the log is independently verifiable ([settlement](../architecture/settlement.md)). The guarantee extends to identities: an identity signs its own `identity.created` with its inception key, the identity id is derived from that key, and the signature rides in the ledger event, so any reader who verifies it can tell that a node did not mint an identity that never registered. Limit: nodes that mirror and project another shard's identity events do not yet verify those signatures when projecting (see [identity](./identity.md#what-is-not-built-yet)), so today the guarantee holds for a reader who verifies and not yet for what a mirroring node projects. Note the scope: only some event kinds carry a signature by the actor (see [signing posture](./protocol-events.md#signing-posture)); for node-attributed kinds, the log proves what the node recorded, not that the actor signed it.

## Key domains

| Key | Held by | Compromise means | Response |
| --- | --- | --- | --- |
| identity passkey | the identity | an attacker can log in as that identity | revoke it from a session with another passkey; total loss if it was the only one, recoverable through [guardian recovery](./identity/recovery.md) if configured |
| identity signing key | the identity (per device) | an attacker can author signed events and fresh signatures going forward | revoke the key (`POST /me/devices/{id}/revoke`, signed by an active key of the identity; the last active key cannot be revoked); rotation is add-then-revoke; events signed by the old key stay valid, the same principle as issuer keys. Losing every signing key cannot be repaired today, since recovery restores a passkey and not a signing key |
| issuer key | the integrator | an attacker can issue authentic-looking claims under that integrator | revoke the key as of T; claims after T are rejected, claims before T are untouched |
| log operator key (tree heads only) | the settlement operator | an attacker can sign bogus tree heads | mirrors and witnesses detect divergence through gossiped, cosigned heads; there is no validator set (see [witness cosigning](./witness-cosigning.md)) |

Keys are never shared across domains. They may share primitives (established signature schemes, existing crates), never a bespoke construction. Shard operators add a further purpose-scoped issuer key; see [issuers](./issuers.md#key-domains-kept-apart).

## Key compromise, concretely

Compromise is handled by time-bounded revocation, not by deleting history. A `key_revoked` entry names the key and the time T from which it is no longer trusted. Verification of any claim resolves the key set as of that claim's `issued_at`. "The legitimate key at the time" and "a compromised key now" are different facts and both stay answerable; see [issuers](./issuers.md).

## Credentials never enter the ledger

A password hash, a session token, a private key, or any other secret is never part of a protocol event. Public keys are fine. There is no password anywhere in the system, and `identity.created` carries no `username`.

## Transport

The node runs plain HTTP by default in local development, which is acceptable only on loopback. Before any non-local deployment TLS terminates in front of it. This is a deployment requirement, not an optional hardening step, and the server does not terminate TLS itself.

## Explicit limitations

- **Authenticity is not meaning.** No mechanism stops an issuer from signing a meaningless claim ([trust model](./trust-model.md)).
- **A single log operator can still censor or delay appends.** Mirrors and verifiability make divergence detectable after the fact, but nothing forces liveness from one operator. This is deliberately not solved with a validator set: there is no contested resource for validators to referee, so multi-validator consensus would add operational complexity for a guarantee (censorship resistance, not tamper evidence) it does not buy here (see [ADR 0186](../architecture/decisions/0186-no-blockchain-validator-consensus-transparency-log-only.md)). The real mitigation is witnessed, gossiped, cosigned tree heads catching a divergent operator. Sharded settlement narrows liveness risk from the whole network to one shard.
- **A managed settlement host can stall or refuse its own integrator, though it can never forge that integrator's history.** Two-phase signing keeps the integrator's key off the host, so the host is limited to withholding service. A shard's trust anchor is tied to the integrator's key and not the host, so switching hosts or self-hosting has no continuity break, and the new host can sync the shard's log from any mirror. An integrator is never cryptographically locked in, though it can be operationally slow to switch. See [self-hosting](../architecture/self-hosting.md).
- **Statistics can be gamed.** Sybil identities can inflate registry numbers; documented, not solved ([registry](./registry.md)).
- **Persistent identity makes harassment persistent.** Blocking is network-wide; cross-integrator moderation remains open ([social graph](./social-graph.md), [privacy](./privacy.md)).
- **Recovery is real but not exhaustive.** A lost passkey with no second one and no guardians is permanent loss ([recovery](./identity/recovery.md)).
- **Topology endpoints and the peer table are unauthenticated inputs.** `POST /nodes/probe` and `POST /nodes/trace` make a node send requests to URLs learned from gossip, and the peer table is fed by unauthenticated announces. Both are bounded by an outbound address policy that refuses link-local, cloud-metadata, and other unsafe ranges, connection pinning to the checked address, no redirects, hop and concurrency caps, per-source rate limits, and table size caps. Trace measurements are self-reported by the nodes involved and not verified facts. A residual risk remains: an attacker with many reachable public addresses can still churn the inactive part of the peer table. The full mitigations and hoster switches are in [node safety limits](../architecture/nodes/safety-limits.md).

## Implementation

Status: partially implemented.

- [`auth.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/auth.rs): the WebAuthn instance, Ed25519 event signature verification, and opaque CSPRNG session tokens (revocable by row deletion).
- [`authz.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/authz.rs): `Caller` and `require_capability`, unit-tested as a pure-logic matrix plus a live-Postgres matrix.
- [`error.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/error.rs): internal error text never reaches the client, and unknown or expired tokens are indistinguishable to the caller.
- [`crates/chain/src/postgres.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/chain/src/postgres.rs): hash-chained entries, content re-verified on read, signed at the tree-head level and not per entry.

## Related

- [Privacy](./privacy.md), [identity](./identity.md), [authentication](./identity/authentication.md), [issuers](./issuers.md), [trust model](./trust-model.md)
- [Witness cosigning](./witness-cosigning.md), [network trust anchors](./network-trust-anchors.md), [node safety limits](../architecture/nodes/safety-limits.md)
