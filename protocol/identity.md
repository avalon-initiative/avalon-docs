# Identity

**Status:** Partially implemented — self-certifying ids and signed key changes are built in the server; verification of those signatures on mirroring nodes and recovery of a signing key are not. The SDKs (0.1.6) implement the client side.

An Avalon identity is a self-custodied keypair plus a small amount of self-described profile data. It belongs to the person who holds the keys, not to any integrator, node, or database, and it is the one thing that survives any single integrator or server disappearing. Integrators establish their own scoped participation under it (see [bindings](./bindings.md)); the identity itself stays the same across all of them.

This page covers the model, what the protocol promises to keep durable, and what identity is not. The mechanics are split into focused pages:

| Page | Covers |
| --- | --- |
| [Authentication and signing keys](./identity/authentication.md) | passkey login, the separate event-signing key, the fresh-signature tier, device pairing, session continuation across nodes |
| [Recovery and rollback](./identity/recovery.md) | M-of-N social recovery, the public delay, post-compromise rollback |
| [Per-identity event chains](./identity/event-chains.md) | how concurrent edits converge and how a fork is detected |

## The model

```text
Avalon Identity
    ├── Profile (identity-controlled metadata)
    ├── Friends                       social-graph.md
    ├── Guild memberships             guilds.md
    ├── Achievements / attestations   achievements-and-attestations.md
    ├── Permission grants             privacy.md
    └── Integrator bindings           bindings.md
          ├── Integrator A -> characters (integrator-owned)
          └── Integrator B -> characters (integrator-owned)
```

An identity is an opaque, stable handle (`IdentityId`) derived from the identity's first signing key, as described in [the identity id](#the-identity-id). It is never derived from a display name, a username, a wallet address, or anything its owner might want to change later. Everything human-facing hangs off it as profile data. The design decision that identity is separate from any game character is recorded in [ADR 0067](../architecture/decisions/0067-identity-is-separate-from-game-characters.md).

## The identity id

An identity id is the lowercase hex SHA-256 of the domain tag `avalon-identity-id-v1` followed by the identity's inception Ed25519 public key (32 raw bytes): exactly 64 characters of `[0-9a-f]`, with no prefix. Parsing is strict and never normalizes; uppercase, any other length, UUID text, and `id:` or `node:` prefixes are all rejected. The domain tag keeps the id distinct from the `node:` shard id derived from the same key. The decision is recorded in [ADR 1129](../architecture/decisions/1129-identity-ids-are-self-certifying.md).

- **Commits to the first key only.** Adding, rotating, or revoking later signing keys, and recovery, never change the id. Different inception keys give different ids, so two people cannot be handed a clashing id by construction, and no registry is needed. This does not by itself stop a hostile shard from publishing events for someone else's id; rejecting those is the verification listed under [what is not built yet](#what-is-not-built-yet).
- **Key acceptability.** The inception key must be a canonical Ed25519 encoding and not of small order. Keys with a torsion component that are neither are accepted, because the id binds the exact key bytes. Identity signatures are verified strictly (small-order components and non-canonical signatures are rejected).
- **Registration.** `POST /identities/register/start` takes `identity_id`, `event_signing_public_key` (base64 raw key), and `display_name`. The server recomputes the id from the key and refuses a mismatch (400 `IDENTITY_ID_MISMATCH`), an unacceptable key or malformed id (400 `INVALID_IDENTITY_ID`), and an id already present on the node (409 `IDENTITY_ID_TAKEN`). Its response carries the ticket, the ledger's network id, and the shard id the node authors. `POST /identities/register/finish` takes a signature by the inception key over the `identity.created` v2 bytes (below) and emits `identity.created`, the first passkey event, and `identity.signing_key_added` for the inception key.
- **The signed bytes.** `avalon:identity.created:v2:{len(network_id)}:{network_id}:{len(shard_id)}:{shard_id}:{ticket_id}:{identity_id}:{public_key_hex}:{display_name}`, where `len` is the decimal UTF-8 byte length. Binding the network, shard, and ticket means a copied payload does not verify in another shard or ceremony. The display name comes last so a `:` in it is harmless.
- **On the ledger.** `identity.created` v2 carries `identity_id`, `ticket_id`, `display_name`, `public_key` (base64), and `signature`, so a reader holding the entry, the network id, and the shard id can recompute the id and verify the signature without asking the node. Version 1 of `identity.created`, `identity.signing_key_added`, and `identity.signing_key_revoked` is no longer decoded.
- **Display names** stay best-effort unique per node and are never the key anything hangs off. Registration refuses a name that, after dropping invisible characters, trimming, and lowercasing, is shaped like an identity id, and names with control, zero-width, or bidirectional-override characters, or longer than 128 characters.
- **WebAuthn.** The WebAuthn user handle is the first 16 bytes of the id, because the WebAuthn library takes a UUID.

The conformance vectors `identity-id.json`, `identity-created-signing.json`, `device-grant-approval.json`, and `signing-key-revoked.json` pin the derivation and the signing bytes. They are vendored into `avalon-sdks` and run in the Rust, TypeScript, and C# SDKs as well as the protocol runner.

### SDK support (0.1.6)

- **Registration.** The Rust and TypeScript SDKs generate the inception key first, derive the hex id, send `event_signing_public_key` in `register/start`, and sign the v2 `identity.created` bytes using the `network_id`, `shard_id`, and ticket exactly as the server supplied them. They also reject an unacceptable generated key. The C# SDK has the `IdentityId` type, derivation, and all the signing functions, but no registration flow.
- **Other signing.** All three SDKs build the v2 device-grant-approval and signing-key-revoked bytes, verify identity signatures strictly, and parse ids strictly. `revoke_device` signs with the session's own local signing key and fails without one. `approve_device_grant` also requires a local signing key and checks the requested key is acceptable before signing.

### What is not built yet

- **Verification on mirroring nodes.** A node that mirrors a shard and projects its identity events checks only shape and derivation, not signatures. For `identity.created` it creates the identity row only when the id derives from an acceptable key and matches the id in the entry's issuer and subject; for an inception `identity.signing_key_added` it accepts the key only when it derives the id. It does not yet verify the `identity.created` signature, the device-grant `approval_signature`, or the `identity.signing_key_revoked` signature when projecting, and the profile projection still applies a repeated `identity.created` for an existing id as an upsert instead of reporting a conflict. Passkey events and the recovery events carry no proof. Cross-node login does verify the creation signature, against the network and shard it fetched from, before it provisions a local stub. This verification is tracked in [avalon-protocol#1130](https://github.com/avalon-initiative/avalon-protocol/issues/1130).
- **Recovering a signing key.** See [recovery](./identity/recovery.md#recovery-restores-a-passkey-not-a-signing-key).

## Self-described metadata is self-expression, not fact

The profile carries what an identity's owner chooses to say about themselves:

- `display_name`: the globally unique, case-insensitive handle itself. There is no separate discriminator suffix; a taken name is rejected rather than auto-suggested.
- `avatar_url` and `banner_url`: `http`/`https` image URLs.
- `bio` (up to 500 characters), `pronouns` (40), `status` (100), `location` (100, free text).
- `favorite_genres`: up to 5 entries from a fixed, small vocabulary, not free text.
- `links`: up to 5 self-reported `http`/`https` URLs, each up to 200 characters.
- `timezone`: free text up to 64 characters. It is not validated against the IANA time zone database, a known gap.
- `theme_color`: a six-digit hex accent color.
- `main_guild`: a pointer to one of the identity's own current guild memberships (see [guilds](./guilds.md#a-users-main-guild)).

`location` is self-described text only, never IP-derived or geocoded. Nothing in the protocol infers where a user physically is. Writing "I am an Avion" in a bio does not make Avion a network-level race: an integrator can display, interpret, or ignore it. Facts about what an identity has done come from issuer attestations with [provenance](./provenance.md), never from the profile. The profile is deliberately small and is not where game-specific data lives.

## What is promised durable

Anything Avalon promises to preserve must be reconstructable from protocol history, and every change to it must emit a protocol event in the same unit of work as the projection change (see [protocol events](./protocol-events.md)). For optional profile fields, `null` in a `profile.updated` payload means the field was explicitly cleared and an absent key means it was untouched.

| State | Durable? | Canonical record | Notes |
| --- | --- | --- | --- |
| identity exists, `created_at` | yes | `identity.created` | v2 carries the inception key and its signature, so the id and signature can be re-verified from the ledger |
| `display_name` | yes | `identity.created`, then `profile.updated` | |
| other profile fields | yes | `profile.updated` | sparse payload: only changed fields are present. List fields (`favorite_genres`, `links`) are always fully replaced when the key is present, including with `[]` |
| `main_guild` | yes | `profile.updated` | must name a guild the identity currently belongs to; cleared automatically if the identity leaves that guild |
| WebAuthn passkey(s) | yes | `identity.passkey_registered` / `.passkey_revoked` | public credential material only, never anything secret |
| event-signing public key(s) | yes | `identity.signing_key_added` / `.signing_key_revoked` | a separate durable fact from the `identity.created` issuer field, which is a `GlobalId` string and not key bytes; a device key carries its approving device's signature and a revocation carries the revoking key's signature |
| recovery configuration and attempts | yes | `identity.recovery_*`, `identity.recovered` | see [recovery](./identity/recovery.md) |
| credentials (password hash) | no | none | there is no password authentication anywhere in the protocol |
| sessions and tokens | no | none | bearer tokens are node-local; a separate self-signed continuation credential is verified statelessly |
| presence | no | none | see [presence](./presence.md) |
| visibility settings | no, unless later promoted | none | see [privacy](./privacy.md) |

A session token or any other shared secret is never part of an event payload. The `identity.created` event carries no `username`.

## What identity is not

- **Not a universal integrator account.** An integrator asks for scoped capabilities and gets only those.
- **Not a universal character.** See [bindings](./bindings.md).
- **Not a platform identity in the Steam or Xbox sense.** No single operator owns it; nodes are infrastructure providers, not authorities (see [nodes](../architecture/nodes/README.md)).
- **Not a real-world identity system, and not headed toward becoming one.** An Avalon identity identifies a keypair, never a person. No field in identity creation asks for a legal name, date of birth, government ID, biometric, phone number, or email, and there is no KYC step. Because identity is self-custodied with no central issuer, no party, including maintainers and node operators, holds a mapping from a keypair to a real person. That mapping is never created. An owner who loses every passkey with no recovery configured loses the identity outright. What Avalon makes portable is online activity (friendships, guild membership, achievements), never personhood.

## Portability means mirrored, not movable

"Your identity is not trapped in one game's world" is a claim about mirrored history. An identity's durable facts (friend, guild, and achievement events) are visible from any node that mirrors the network's history. There is no user-facing export bundle, and none is planned, because there is nothing a person is trapped inside.

The real limit is authentication. A WebAuthn passkey is scoped to the node (its relying-party ID) it was registered on and cannot be presented against a different node; that is part of the WebAuthn specification, not something the protocol can route around. Session-continuation tokens cover the already-logged-in half of reaching another node but never count as a login credential, since they prove key possession and not human presence. A destination-bound, human-approved signed grant, modeled on device pairing, covers first login on a node the identity never registered on; see [ADR 0786](../architecture/decisions/0786-on-demand-cross-node-identity-data-resolution.md) and [cross-node login](../architecture/nodes/cross-node-login.md).

## Open questions

- Recovery when every passkey is lost and no guardians are configured. The answer today is total loss of the identity.
- Recovery when every signing key is lost. Guardian recovery restores a passkey only, so nothing can authorize a replacement signing key today. The design is decided in [ADR 1135](../architecture/decisions/1135-recovery-authorises-a-new-signing-key-with-guardian-signatures.md) and not built.
- Whether identities can be transferred.
- The minimum replication guarantee for identity-bearing shards, so one operator's node disappearing cannot strand the identities that live there.

## Implementation

Status: the server side is implemented, running end to end against Postgres; the gaps are listed under [what is not built yet](#what-is-not-built-yet).

- Types: [`crates/protocol/src/identity.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/identity.rs) (`Identity`, `Profile`, `Genre`) and [`ids.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/ids.rs). The protocol crate has no reference to WebAuthn, Ed25519 verification, or any character schema.
- Registration, login, and profile endpoints: [`crates/server/src/handlers.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/handlers.rs). Registration verifies both the WebAuthn ceremony and the Ed25519 event signature before writing anything. The derivation and signing-byte builders are in [`identity_id.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/identity_id.rs) and the key policy in [`ed25519_key.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/ed25519_key.rs).
- Wire API: [OpenAPI document](https://github.com/avalon-initiative/avalon-protocol/blob/main/docs/generated/openapi.json); see [API specification](./api.md).

## Related

- [Authentication and signing keys](./identity/authentication.md), [recovery and rollback](./identity/recovery.md), [per-identity event chains](./identity/event-chains.md)
- [Bindings](./bindings.md), [social graph](./social-graph.md), [guilds](./guilds.md), [privacy](./privacy.md)
- [Identity aggregate view](./identity-aggregate-view.md)
- [Security model](./security-model.md)
- [ADR 0067: identity is separate from game characters](../architecture/decisions/0067-identity-is-separate-from-game-characters.md)
- [ADR 1129: identity ids are self-certifying](../architecture/decisions/1129-identity-ids-are-self-certifying.md)
- [Glossary](../reference/glossary.md)
