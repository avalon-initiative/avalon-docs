# Identity

**Status:** Implemented

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

An identity is an opaque, stable handle (`IdentityId`, a UUID). It is never derived from a display name, a username, a wallet address, or anything its owner might want to change later. Everything human-facing hangs off it as profile data. The design decision that identity is separate from any game character is recorded in [ADR 0067](../architecture/decisions/0067-identity-is-separate-from-game-characters.md).

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
| identity exists, `created_at` | yes | `identity.created` | self-signed by the identity's own key |
| `display_name` | yes | `identity.created`, then `profile.updated` | |
| other profile fields | yes | `profile.updated` | sparse payload: only changed fields are present. List fields (`favorite_genres`, `links`) are always fully replaced when the key is present, including with `[]` |
| `main_guild` | yes | `profile.updated` | must name a guild the identity currently belongs to; cleared automatically if the identity leaves that guild |
| WebAuthn passkey(s) | yes | `identity.passkey_registered` / `.passkey_revoked` | public credential material only, never anything secret |
| event-signing public key(s) | yes | `identity.signing_key_added` / `.signing_key_revoked` | a separate durable fact from the `identity.created` issuer field, which is a `GlobalId` string and not key bytes |
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
- Whether identities can be transferred.
- The minimum replication guarantee for identity-bearing shards, so one operator's node disappearing cannot strand the identities that live there.

## Implementation

Status: implemented, running end to end against Postgres.

- Types: [`crates/protocol/src/identity.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/identity.rs) (`Identity`, `Profile`, `Genre`) and [`ids.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/ids.rs). The protocol crate has no reference to WebAuthn, Ed25519 verification, or any character schema.
- Registration, login, and profile endpoints: [`crates/server/src/handlers.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/handlers.rs). Registration verifies both the WebAuthn ceremony and the Ed25519 event signature before writing anything.
- Wire API: [OpenAPI document](https://github.com/avalon-initiative/avalon-protocol/blob/main/docs/generated/openapi.json); see [API specification](./api.md).

## Related

- [Authentication and signing keys](./identity/authentication.md), [recovery and rollback](./identity/recovery.md), [per-identity event chains](./identity/event-chains.md)
- [Bindings](./bindings.md), [social graph](./social-graph.md), [guilds](./guilds.md), [privacy](./privacy.md)
- [Identity aggregate view](./identity-aggregate-view.md)
- [Security model](./security-model.md)
- [ADR 0067: identity is separate from game characters](../architecture/decisions/0067-identity-is-separate-from-game-characters.md)
- [Glossary](../reference/glossary.md)
