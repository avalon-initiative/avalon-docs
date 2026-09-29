# Integrators and Issuers

**Status:** Partially implemented — registration, key management, and historical key resolution are built; issuer status transitions and root-key recovery are not.

Every participating integrator has a durable issuer identity with registered signing keys, a key history, and a status. Attestations are only as verifiable as the issuer record behind them. The node operator is never the issuer: hosted infrastructure transports, indexes, and settles an integrator's claims but cannot sign them.

## Registration

An integrator connecting to Avalon establishes:

| Field | Notes |
| --- | --- |
| integrator id | `game:ashen-realms`: namespaced, globally unique |
| issuer identity | today the same thing as the integrator; modeled separately so other issuer kinds stay possible |
| signing key(s) | public keys, each with an id, algorithm, role, and validity window |
| key history | every add, revoke, and expiry as an appended event |
| status | `Active`, `Suspended`, `Revoked`, `Deprecated` (only `Active` is reachable today) |
| category | `game`, `app`, or `service`; additive, defaults to `game` |
| capabilities requested | what it will ask identities for. A request, never a grant |
| public metadata | name, developer |

Registering grants nothing. An identity still authorizes each capability through its own [binding](./bindings.md). Integrator registration and key addition are rate-limited per source by default. A separate, optional naming path for self-certifying shard ids exists alongside `game:<slug>` without touching this flow; see [network trust anchors](./network-trust-anchors.md).

**Not built:** the original design also listed a website, the supported protocol version and features, and a recognition policy as registration fields. The `Integrator` record carries only id, slug, name, developer, registration time, status, and category. Recognition is published later through its own endpoint (see [registry](./registry.md#recognition-relationships)).

## Issuer lifecycle

```text
Integrator registers
      ↓
Issuer identity created            game.registered (root key attached)
      ↓
Integrator declares signing key(s) issuer.key_added
      ↓
Integrator issues attestations     achievement.issued (signed by the integrator's key)
      ↓
Avalon records and indexes         settlement + projection
      ↓
Integrator B verifies
    ├── signature                  against the key valid at issued_at
    ├── issuer identity            exists, matches
    ├── key validity               not revoked or expired as of issued_at
    ├── attestation status         not revoked or superseded as of now
    ├── issuer status              per Integrator B's policy
    └── recognition policy         Integrator B's own decision
```

## Key management requirements

The protocol handles the following without inventing cryptography:

- **rotation:** a new key is added and the old one retired; every historical claim signed by the old key stays verifiable
- **multiple active keys:** regions, environments, staged rotation
- **historical keys:** a retired key still resolves for claims from its validity window
- **compromise:** a key is revoked as of time T; claims signed after T are rejected, claims before T are untouched
- **expiry:** keys carry validity windows
- **historical verification:** "was this key legitimate for this issuer when this was signed" is a first-class query

The system distinguishes "signed by the legitimate key at the time" from "this key is compromised now". Rotating a key never invalidates history. A shard operator's settlement signing key is held to the same custody standard: a managed host never holds it, for the same reason an issuer's key is never handed to Avalon's infrastructure (see [self-hosting](../architecture/self-hosting.md)).

## Who authorizes key changes

Every issuer has exactly one **root key**, established at registration, which is the only key that can add or revoke keys. It governs the key set and does not sign attestations in the common case. Zero or more **operational keys**, added and revoked by the root, sign attestations day to day, and several concurrent operational keys are ordinary.

Registration requires one keypair, not two: the registering key doubles as root and first operational key, so a solo registrant pays no extra friction. A studio that wants isolation (keep the root cold, expose only an operational key to CI) can add one later with a single `issuer.key_added` call.

The reason for the split: if one key could both sign attestations and manage the key set, a leaked operational key (the realistic leak, since it is embedded in a build pipeline) could also revoke the developer's keys and register the attacker's, hijacking the issuer. Root governance removes that race. Root key loss or compromise is a known, honestly unsolved residual risk, the same shape as identity recovery.

A node operator cannot add a key to an issuer it does not control. Suspending or revoking an issuer at the network level is a separate operator action with its own authorization and audit trail, **not yet specified or built**.

## Key domains, kept apart

| Key | Belongs to | Governs |
| --- | --- | --- |
| identity key | the identity | mutations to the identity's own data |
| issuer key (`attestation` purpose) | the integrator | attestations the integrator issues |
| issuer key (`shard_settlement` purpose) | the integrator, as a shard operator | signing that integrator's own shard's log entries and tree heads |
| log operator key (core shard) | the core shard's operator | signing the core shard's log entries and tree heads |

They may share primitives and are never the same key or lifecycle. The two issuer purposes are authorized through the same registration flow, scoped by a `purpose` field, and are mechanically non-interchangeable: a `shard_settlement` key can authenticate ordinary calls but can never be resolved as an attestation-signing key, and vice versa. See [network trust anchors](./network-trust-anchors/shard-identity-and-names.md#per-shard-trust-anchors).

## Scenarios

**E: Integrator A rotates its operational key.** The root key authors `issuer.key_added(k2)`, then `issuer.key_revoked(k1, reason: rotated)`. A claim signed by k1 in 2027 verifies against k1's validity window and stays authentic.

**F: Integrator A's operational key is compromised.** The root key authors `issuer.key_revoked(k1, at: T)`. Claims signed by k1 before T remain authentic and valid, claims after T are rejected, and A continues under k2. The compromised k1 could never have authorized its own revocation or a replacement, so there is no race against an attacker also holding it.

## Implementation

Status: partially implemented.

- **Types.** `Integrator`, `IntegratorStatus`, `IntegratorCategory`, `IntegratorRegistration`, `IssuerKey` (with `KeyRole { Root, Operational }`, validity window, and revocation), and pure point-in-time resolvers `resolve_valid_signing_key` and `resolve_valid_root_key` in [`integrators.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/integrators.rs).
- **Registration.** `POST /integrations` takes a unique lowercase slug (409 on collision), name, developer, requested capabilities, an optional category, and an initial Ed25519 public key, recorded atomically with a `game.registered` event. That event is network-attributed and not integrator-signed, because nothing has yet proven the registrant controls the submitted key. The registration key is always stored as `root`.
- **Authentication.** `POST /integrations/{slug}/challenge` returns a short-lived nonce, which the integrator signs with a registered key; `GET /integrations/whoami` confirms it. Revoked and expired keys are filtered out.
- **Key set.** `POST /integrations/{slug}/keys` and `POST /integrations/{slug}/keys/{key_id}/revoke` require a currently valid root key (an operational key gets `IssuerKeyNotRoot`). They emit `issuer.key_added` and `issuer.key_revoked`. Revoking an already-revoked or nonexistent key is a 403, not a no-op. `GET /integrations/{slug}/keys` is public and returns every key the issuer has ever registered.
- **Namespaces.** `/integrations` is the canonical API path; `/games` remains as redirects. `Issuer::Game`, `Issuer::App`, and `Issuer::Service` mint the `game:`, `app:`, and `service:` namespaces.
- **CLI.** `avalon register-integrator` generates a keypair locally and registers it; the server only ever stores the public half.
- **Not built:** `issuer.key_expired` (no expiry sweep), issuer status transitions (`issuer.suspended`, `.reinstated`, `.revoked`, `.deprecated`), and root-key recovery.

## Related

- [Achievements and attestations](./achievements-and-attestations.md), [trust model](./trust-model.md), [revocation](./revocation.md), [registry](./registry.md), [bindings](./bindings.md)
- [Security model](./security-model.md), [network trust anchors](./network-trust-anchors.md)
- [Integrator Space](./integrator-space.md)
