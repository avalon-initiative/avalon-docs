# Design Proposal

**Status:** Reference — a narrative overview that defers to the architecture pages; unbuilt items are marked Planned or Undecided

This is the narrative product overview of Avalon: what it is, the problem it answers, and the principles behind the design. The normative statements (invariants, authority boundaries, what the code is held to) live in the [architecture README](README.md) and the pages it links. When this page and those pages disagree, they win and this page is corrected.

> Games are experiences. Your identity, friends, guilds, achievements, and history belong to you.

## What Avalon is

Avalon is an open, self-hostable identity and social layer for games, apps, and services. It gives a person one persistent identity, friends list, guild membership, and achievement history that exist independently of any single integrator and survive that integrator shutting down. An integrator is any independently operated game, app, or service that connects to Avalon.

An identity is a self-custodied keypair, not an account any company controls. Friends, presence, guilds, and achievements are network-level facts, stored once and read by every integrator a person has connected, rather than duplicated in each integrator's own database.

An integrator opts into whichever parts of Avalon it wants (identity alone, or identity plus guilds plus achievements), capability by capability. Avalon never owns the integrators it connects, never sees their internal data unless they choose to publish it, and never dictates what an integrator's world looks like or means.

## The problem

A person's identity is disposable today: a different login for every service, a friends list that means nothing outside the app it lives in, and achievements that vanish when the issuing game shuts down. Every studio rebuilds the same friends, guilds, chat, and presence infrastructure, and none of it outlives that one game.

Avalon exists to answer one question: what should survive the death of a particular game or server? The answer is the person's identity and history, not the game. See [overview](overview.md) and [why Avalon](../getting-started/why-avalon.md).

## System structure

Three layers:

- **Protocol:** the shared vocabulary (identity, guilds, achievements, permissions) every implementation is held to.
- **Network:** the running implementation, a server process (or several role-specialized ones) backed by Postgres, speaking the protocol over HTTP and WebSocket. See [nodes](nodes/README.md).
- **Integrators:** sovereign games, apps, and services that opt into whichever parts of the network they want.

The reference implementation is a Rust workspace of protocol types, a settlement ledger, an indexer, and a server, with SDKs and a development CLI built on top ([overview](overview.md#components-and-boundaries)).

## Identity

An identity is a self-custodied keypair: a WebAuthn passkey for login and a separate Ed25519 key that signs the events it authors. It identifies a keypair, not a person; no name, government ID, biometric, or other real-world identifier is in it by construction. An identity can register several passkeys and devices, recover access through M-of-N guardian approval if every device is lost, and pair a new device without starting over. See [identity](../protocol/identity.md).

Login today is identity-id-first rather than fully usernameless: the registration path used does not create discoverable credentials, and passkey-only login would need attested resident keys, which are not built (Planned).

A character (race, class, level, inventory, progression) is entirely integrator-owned gameplay data. Avalon never sees it unless the integrator publishes a schema describing some of it ([bindings](../protocol/bindings.md)).

## Social graph and guilds

Friends, presence, and communication persist across every integrator a person uses. None of it is handed to an integrator wholesale, only through explicit capability grants and visibility scopes the identity controls. Presence is ephemeral and never enters durable history ([social graph](../protocol/social-graph.md), [presence](../protocol/presence.md)).

A guild is a network-level social primitive with members across many integrators, roles, per-resource permission overrides, channels, chat, and events with RSVP. It survives any single integrator shutting down. An integrator is a client of a guild, never its owner ([guilds](../protocol/guilds.md), [ADR 0074](decisions/0074-guilds-are-network-level-primitives-not-game-owned.md)).

## Achievements

An achievement (attestation) is a signed claim of the form "issuer X asserts identity Y accomplished Z", timestamped and schema-typed. Integrators register as issuers under a two-tier root and operational signing-key model, sign issuance locally, and can revoke a claim later. Revocation is appended history, never deletion ([achievements](../protocol/achievements-and-attestations.md), [revocation](../protocol/revocation.md)).

Verification answers three separate questions ([trust model](../protocol/trust-model.md)):

- **Authentic:** the signature verifies against the issuer's registered key.
- **Valid:** the claim is not revoked, and its issuer was not suspended or revoked at issuance.
- **Recognized:** whether a specific receiving integrator chooses to honor the claim. Decided per integrator, never by the network.

Avalon computes and publishes the first two. The third is always the receiving integrator's own judgment.

## Settlement

Every identity, guild, and achievement write commits atomically with its ledger entry through an outbox. The ledger is a hash-chained, Merkle-rooted, append-only, Postgres-backed log with periodically signed tree heads, mirror-facing proof endpoints, and tiered retention. It is a public transparency log, not a blockchain: no validator set and no mining, because nothing written to it is contested. One event is never one chain transaction, and real-time gameplay never touches settlement ([settlement](settlement.md)).

Trust in a log head does not have to rest on one key. Nodes can act as witnesses: each independently checks that a head only grew from the last one it saw and cosigns it. A verifier keeps a bounded, diversity-limited list of witnesses and accepts a head once a majority of that list has cosigned. Two conflicting heads that both reach a majority must share a witness, so a forked log is provable from signatures alone. A network of one node runs the same rule as a network of many. Shard identity is self-certifying (derived from the shard's own key), so joining needs no registry ([witness cosigning](../protocol/witness-cosigning.md), [sharding](settlement/sharding.md)).

## Permission model

An integrator never automatically receives everything associated with an identity. Every capability (`friends.read`, `guilds.chat`, `achievements.issue`, and so on) is granted explicitly by the person and can be revoked at any time. SDK methods check their required grant before a request, and the server enforces the same check independently; the client-side check is a fast failure for developer experience, never the security boundary. Least privilege is the default: access to guild membership does not imply access to friends, private messages, or achievement history ([security model](../protocol/security-model.md)).

## Clients

The Hub is a person's front door with no integrator open: identity setup, friends, guilds, achievements, and connected integrators. It is a client of the network like any other, using the same API, authentication, and capability model as an integrator or third-party client, with no backend of its own ([ADR 0077](decisions/0077-the-hub-is-a-client-of-the-network-not.md), [Hub](../ecosystem/hub.md)). A desktop and mobile shell around the same UI shows other clients are possible by construction. The Hub is not a launcher, a store, a distribution platform, or an integrator authority, and it presents every authentic, valid claim with its provenance without implying the network judged one integrator more prestigious than another.

## SDKs

An integrator integrates through an SDK for its own language instead of talking to the network directly. The SDK handles network calls, signing, retries, and capability checks, so a developer thinks in identity, guilds, achievements, and presence, not Postgres instances or node addresses. Official SDKs exist for Rust (the reference), C# (Unity-targeted), and TypeScript (browser-facing, and what the Hub is built on), released together ([SDK overview](../sdk/README.md), [SDK design](../sdk/design.md)).

Each SDK exposes two session types: a capability-gated session for an integrator acting on a person's explicit grants, and a first-party account session for an identity's own account operations. There is no conversion between them in either direction, so an integrator credential can never yield account-level power, by construction. The SDKs can also verify a head by witness cosignature against a known list the caller supplies, with shared conformance vectors across all three. Whether a client that connects with only a pinned key gets a default witness policy is Undecided (see open questions).

## Self-hosting

Avalon is open source and self-hostable. Running the code under your own `network_id` is fully supported but is a fork, cryptographically incapable of merging back into the public log. Several organizations mirroring and serving reads from the same public log is supported and encouraged, as with Certificate Transparency: that is participation, not federation ([self-hosting](self-hosting.md)).

## Limitations and non-goals

- **No economic layer.** No currency, wallet, or purchase primitive exists or is planned near term ([future layers](future-layers.md)).
- **No portable assets.** Ownership and provenance for in-game items is unbuilt; an achievement is a claim about an event, not an asset.
- **Login is not fully usernameless yet**, as above.
- **No validator-set consensus and no committee.** Ordering is never contested, so there is nothing to vote on. The network relies on witness cosigning to make a rewritten or forked log detectable. This is resistance, not proof: an attacker who controls most of a victim's known witnesses can still mislead that victim, which is why the known list is diversity-limited and anchored.
- **Not a launcher, store, or distribution platform, and not an integrator authority.** There is no score or recommended ordering anywhere in the network's own surfaces.
- **Federation is explicitly rejected.** Visibility is a property of the public log, not a relationship between servers.
- **Not a blockchain-currency or NFT project.** Settlement exists for verifiability, not speculation, and there is no token at any layer.

## Known challenges

- **Identity recovery.** Guardian-based social recovery mitigates but does not eliminate the risk of losing an identity for good.
- **Trust.** Integrators must decide which issuers to trust. Avalon deliberately does not make that judgment.
- **Privacy.** A portable identity creates surveillance risk if visibility scoping is not kept correct ([privacy](../protocol/privacy.md)).
- **Abuse.** A persistent identity can make harassment persistent; blocking and visibility controls have to hold up under misuse.
- **Interoperability of meaning.** Avalon records provenance, not meaning; a receiving integrator decides what a claim means to it.
- **Centralization risk.** A single dominant operator could become a de facto gatekeeper without formal authority; mirroring exists so that is not structurally required.
- **Adoption.** The network has limited value until enough independent integrators use it.

## Open questions

Open on purpose, not silently resolved by whatever gets implemented first.

- How should guild ownership transfer and leadership succession work at the edges (contested transfers, abandoned guilds)?
- How much social information should be portable by default versus opt-in?
- How should released clients and SDKs adopt a default witness policy without breaking clients pinned to a single key?
- What does the settlement log ultimately anchor to or become, if anything, beyond its own verifiable history?
- Should integrator data (assets, schemas) ever standardize across integrators, or stay integrator-defined?
- How should economic transactions work, if an economic layer is ever built?

## Roadmap

1. **Network:** identity, profiles, friends, guilds and chat, achievements and attestations, integrator and issuer registration, a basic registry and Hub, a developer API. Implemented.
2. **SDKs:** Rust first, then the languages actual integrations demand. Rust, C#, and TypeScript are Implemented.
3. **External integrators:** independent integrators validate the protocol. An adoption milestone.
4. **Portable assets:** provenance, ownership, transfers, recognition. Planned.
5. **Economy:** only after the network shows real utility. Planned, and optional.

## Guiding principles

1. **Integrators remain sovereign.** Avalon connects them; it does not control them.
2. **Identity belongs to the person**, not to any integrator or company.
3. **Interoperability is opt-in.** No integrator is forced to support anything it does not want.
4. **Least privilege.** An integrator receives only the capabilities it is explicitly granted.
5. **History is portable and append-only.** Revocation is recorded, never erased.
6. **Functionality is contextual.** A claim need not mean the same thing everywhere it is recognized.
7. **Settlement is a public log, not a blockchain, and not federation.** Anyone can verify and mirror it without being trusted first.
8. **Open source first.** The protocol does not depend on a proprietary implementation.
9. **Developer experience matters.** Integration should be simple, and the SDK should hide infrastructure, never domain concepts.
10. **Build the infrastructure, not the universe.** Avalon connects worlds; it does not try to become one.

## Related

- [Architecture README](README.md), [overview](overview.md)
- [Why Avalon](../getting-started/why-avalon.md)
- [Settlement](settlement.md), [self-hosting](self-hosting.md), [future layers](future-layers.md)
- [Protocol concepts](../protocol/README.md)
