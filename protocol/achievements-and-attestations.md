# Achievements and Attestations

**Status:** Implemented — the issuer trust-signal directory is Planned and on hold, and supersession is not built.

An achievement in Avalon is an issuer's signed claim, not a `user_id -> achievement_id` row. The durable fact is "Integrator A asserts that Identity X accomplished Y", signed by Integrator A's key, with a timestamp and a schema. Avalon records that claim and its provenance and never dictates what another integrator does with it. The mechanism is domain-agnostic: any issuer can assert a claim about an identity. Examples here are drawn from games because games are the first live use case. The design decision is recorded in [ADR 0076](../architecture/decisions/0076-attestation-trust-model-authenticity-validity-and-recognition-are-separate.md).

## Vocabulary is category-driven, mechanism is not

A `game` issuer's claims are **achievements**. An `app` or `service` issuer's claims are **milestones**. The record shape, verification path, and namespacing pattern are the same. Only the human-facing label and the `GlobalId` kind segment differ (`game:<slug>:achievement:<key>` versus `app:<slug>:milestone:<key>` or `service:<slug>:milestone:<key>`), and both are derived from the issuer's own registered category so a label cannot drift from what the issuer is. One shared term serves both non-game categories: a service's "user completed onboarding" and an app's "user hit their 100th session" are the same kind of fact to Avalon. A consumer verifies a claim without caring what it is called. An issuer that wants to attach a custom shape to its claims (a `schema` reference) can, for any category; see [Integrator Space](./integrator-space.md).

## Shape

```text
Issuer (Integrator A, signing key k1)
    │
    ▼
Attestation
    ├── achievement     game:ashen-realms:achievement:dragon_slayer
    ├── subject         Avalon Identity X
    ├── issued_at       2027-03-14T21:07:00Z
    ├── proof           signature by k1 over the claim
    ├── evidence        opaque reference the issuer chooses to attach (not signed)
    └── status          derived: Active | Revoked
```

The signature answers "did Integrator A issue this". Nothing in it answers "was this hard", and nothing can; see the [trust model](./trust-model.md). `evidence` is an opaque pointer (a hash, URL, or short identifier), not a place to store content. Its serialized size is capped at 4096 bytes, a network-wide validity rule and not a per-node setting, since it gates what every node accepts into the permanent ledger.

## Namespacing

Human-readable names are never globally unique. Ids are namespaced under the issuer via `GlobalId` (`<namespace>:<owner>:<kind>:<key>`):

```text
game:ashen-realms:achievement:dragon_slayer
game:worldzero:achievement:dragon_slayer
game:random-mmo-47:achievement:dragon_slayer
```

Three distinct claims that share a title. The display name stays "Dragon Slayer"; provenance makes the distinction.

## Same title, different provenance

Integrator A issues Dragon Slayer after a brutal raid. Integrator B issues it after a different hard achievement. Integrator C lets every user click a button labeled Dragon Slayer. All three are cryptographically authentic. Avalon does not pretend they are semantically identical and does not rank them. The Hub shows each with its issuer, a consuming integrator recognizes whichever it chooses, and the identity's owner features or hides whichever they like.

## The receiving integrator decides meaning

Integrator A says "User X defeated the Dragon Lord." Integrator B may unlock a title, C a quest, D may ignore it. A consumer verifies authenticity and validity (universal), then applies its own recognition policy (contextual). SDKs expose those three results separately so an integrator can display claims it does not recognize.

## Issuer trust signals (Planned, on hold)

Issuer key lifecycle answers authenticity. Who decides an issuer is worth attention at all is meant to be answered by an open, universally visible issuer directory, never a federated or web-of-trust model: every registered issuer is always visible and verifiable, and nothing is gated behind another issuer vouching for it, the same "mirrors, not federation" posture as [settlement](../architecture/settlement.md). Instead of a trust verdict, each issuer would carry objective, computable signals derivable from the ledger (issuance volume, issuer age, revocation rate), and each consuming client would set its own display threshold. This is a read-side aggregation over data the protocol already keeps and not a new trust primitive. The shape is decided; it is on hold and not implemented.

## Definitions

An integrator defines its achievements before issuing them. An `AchievementDefinition` carries the namespaced id, issuer, name, description, an optional `schema` reference, a `version`, and an optional visual identity. Definitions are durable (`achievement.defined`) so the registry and Hub can render an attestation even after the integrator is gone. `achievement.definition_updated` bumps `version` while the id never changes. A definition can be retired (`achievement.definition_retired`), stopping new issuances without touching any already issued.

`icon` is a key into a small fixed built-in set (`trophy`, `star`, `shield`, `sword`); `icon_url` is an integrator-hosted image that takes precedence. Both are optional, and the server (not clients) supplies the default `trophy`, so every reader sees the same one. `icon_url` is validated only for an `http`/`https` scheme and never fetched or re-hosted.

## Lifecycle

```text
achievement.defined  ->  achievement.issued  ->  achievement.revoked
                                                (attestation.superseded: not built)
```

Every step is an appended protocol event, and revocation never removes the issuance; see [revocation](./revocation.md). Integrator event results such as tournaments are attestations with a game-event schema and not a separate mechanism; see [cross-integrator events](./cross-integrator-events.md).

## Issuance is signed, not merely authenticated

Two independent proofs are both required:

1. **HTTP-level challenge-response** proves the request came from whoever holds an issuer key.
2. **A detached signature in the request body** proves the issuer's key vouches for this exact attestation. The signed bytes fold in the claim kind, the issuer, the subject, and the achievement, so a signature cannot be replayed across vocabularies, and the key is resolved against the issuer's full key history at the moment of issuance. This proof still holds if the HTTP layer's auth were somehow bypassed: a node operator can never produce a valid attestation for an issuer it does not control.

Issuing also requires the subject's own consent: an active [binding](./bindings.md) plus an active grant for `achievements.issue` (game issuers) or `milestones.issue` (app and service issuers). Neither proof substitutes for the other. Checks run in order and any failure short-circuits: the caller is an integrator and not a user session, the subject has a binding and grant, the definition exists and is not retired, and the signature verifies against a currently valid key of the issuer.

**Bulk issuance.** One challenge-response plus one signature over a length-prefixed encoding covers an ordered claim list for one subject. Every claim still becomes its own attestation and its own event through the same write path, and a bulk call is never all-or-nothing: an unknown or retired definition fails only that claim. The SDKs wrap bulk issuance for achievements only; there is no milestones wrapper yet. Revoking one attestation out of a batch is an ordinary revocation on its id; there is no bulk revoke.

## Network admission

Signatures are network-agnostic, so a second, independent check runs after signature verification: is this exact public key admitted to write on this server's network? Explicit self-service registration proves possession of the key with a signed nonce. On development and integration networks a key is also admitted automatically the first time it appears on a valid signed write; on `avalon-mainnet-*` networks (and any unrecognized `network_id`, failing closed) an unregistered key's write is rejected. SDKs and the CLI additionally refuse client-side to register against a network that does not match independent network verification. See [ADR 0479](../architecture/decisions/0479-network-isolation-via-per-network-issuer-registration-not-signature.md) and [network trust anchors](./network-trust-anchors.md).

## Reading

`GET /me/achievements` lists the caller's own attestations, cursor-paginated newest first, optionally filtered by issuer or claim vocabulary; the response is `{ achievements, next_cursor }`. `GET /attestations/{id}` is a public read of one attestation with computed authenticity, validity, and history (see [trust model](./trust-model.md)).

## Implementation

Status: implemented.

- Types: `AchievementDefinition`, `Issuer::{Game, App, Service}`, `Signature`, `AchievementAttestation`, and the canonical signing-bytes functions in [`crates/protocol/src/achievements.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/achievements.rs). The attestation has no `revoked_at`: a mutable status on durable history would contradict append-only history.
- Server: [`achievements.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/achievements.rs) (definitions, issuance, bulk issuance), [`attestations.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/attestations.rs), [`issuer_registration.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/issuer_registration.rs).
- Signing-bytes conformance vectors: [`attestation-signing.json`](https://github.com/avalon-initiative/avalon-protocol/blob/main/conformance/vectors/attestation-signing.json), shared by all three SDKs.

## Related

- [Trust model](./trust-model.md), [provenance](./provenance.md), [revocation](./revocation.md), [issuers](./issuers.md)
- [Cross-integrator events](./cross-integrator-events.md), [Integrator Space](./integrator-space.md), [registry](./registry.md)
- [ADR 0076](../architecture/decisions/0076-attestation-trust-model-authenticity-validity-and-recognition-are-separate.md)
