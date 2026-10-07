# Avalon Architecture

**Status:** Implemented — invariants and boundaries; sections on later phases are marked Planned

This is the normative architecture reference for Avalon: the invariants, the authority boundaries, and the tests every change is held to. Avalon is an open interoperability layer for independently operated games, apps, and services ("integrators"): it owns identity, social graph, guilds, durable history, and provenance, and nothing inside an integrator's own world.

> Don't build the universe. Build the infrastructure that lets others build worlds. Avalon is the railroad between integrators, not an attempt to own every destination.

[Design proposal](design-proposal.md) is the narrative version. When it disagrees with this set, this set wins and the proposal is updated. New terms are defined in the [glossary](../reference/glossary.md).

## Map

### Architecture (this directory)

| Topic | Page | One line |
| --- | --- | --- |
| Overview | [overview.md](overview.md) | What Avalon is and is not; the three verticals; component boundaries |
| As built | [as-built.md](as-built.md) | How the repositories and protocol crates depend on each other, and where contracts flow |
| Settlement | [settlement.md](settlement.md) | Batched commitments; a transparency log on Postgres, no blockchain and no validator consensus |
| Query and indexing | [query-and-indexing.md](query-and-indexing.md) | Postgres read models are projections, rebuildable from history |
| Nodes | [nodes/README.md](nodes/README.md) | Infrastructure providers, not authorities: roles, shards, mirrors, discovery, connectivity |
| Distributed topology | [distributed-topology.md](distributed-topology.md) | Sharded settlement with no aggregator; interest-scoped realtime mesh |
| Synchronization | [synchronization.md](synchronization.md) | Offline and deferred SDK participation; an offline claim never carries online trust |
| Communication | [communication.md](communication.md) | Direct messages, voice, notifications: realtime infrastructure, not a Discord replacement |
| Scalability | [scalability.md](scalability.md) | 1,000 integrators by 100,000 identities without becoming a gameplay bottleneck |
| Disaster recovery | [disaster-recovery.md](disaster-recovery.md) | Every Postgres disappears; what is rebuilt, and from what |
| Self-hosting | [self-hosting.md](self-hosting.md) | Mirroring, running a shard, and running a private fork are three different things |
| Future layers | [future-layers.md](future-layers.md) | Portable assets and economy: later phases, not foundations |
| Design proposal | [design-proposal.md](design-proposal.md) | The narrative product overview |
| Decisions | [decisions/](decisions/) | Architecture decision records |

### Protocol concepts (see the [protocol section](../protocol/README.md))

| Topic | Page |
| --- | --- |
| Identity | [identity.md](../protocol/identity.md) |
| Integrator bindings | [bindings.md](../protocol/bindings.md) |
| Achievements and attestations | [achievements-and-attestations.md](../protocol/achievements-and-attestations.md) |
| Provenance | [provenance.md](../protocol/provenance.md) |
| Trust model | [trust-model.md](../protocol/trust-model.md) |
| Revocation | [revocation.md](../protocol/revocation.md) |
| Integrators and issuers | [issuers.md](../protocol/issuers.md) |
| Guilds | [guilds.md](../protocol/guilds.md) |
| Social graph | [social-graph.md](../protocol/social-graph.md) |
| Presence | [presence.md](../protocol/presence.md) |
| Cross-integrator events | [cross-integrator-events.md](../protocol/cross-integrator-events.md) |
| Integrator registry | [registry.md](../protocol/registry.md) |
| Protocol events | [protocol-events.md](../protocol/protocol-events.md) |
| Worked ledger example | [worked-ledger-example.md](../protocol/worked-ledger-example.md) |
| Identity aggregate view | [identity-aggregate-view.md](../protocol/identity-aggregate-view.md) |
| Network trust anchors | [network-trust-anchors.md](../protocol/network-trust-anchors.md) |
| Witness cosigning | [witness-cosigning.md](../protocol/witness-cosigning.md) |
| Security model | [security-model.md](../protocol/security-model.md) |
| Privacy | [privacy.md](../protocol/privacy.md) |
| Integrator Space | [integrator-space.md](../protocol/integrator-space.md) |

Two related topics live with the projects that consume the protocol, since each is a separate deployable: the [SDK design](../sdk/design.md) (language-agnostic; exposes protocol capabilities, not infrastructure topology) and the [Hub](../ecosystem/hub.md) (a client of the network, not the network).

## Invariants

These hold unless an explicit, documented decision changes them.

| Area | Invariant |
| --- | --- |
| Identity | Avalon identity is self-owned and integrator-independent. |
| Identity | An identity is a self-custodied keypair: a WebAuthn passkey for login and a separate Ed25519 key that signs the events it authors. No password, no shared secret. |
| Characters | Characters, and every integrator-defined attribute, belong to the integrator unless explicitly promoted. |
| Guilds | Guilds are network-level, integrator-independent social primitives ([ADR 0074](decisions/0074-guilds-are-network-level-primitives-not-game-owned.md)). |
| Achievements | Achievements are issuer attestations, not shared rows. |
| Provenance | Durable interoperable claims preserve provenance. |
| Trust | Authenticity, validity, and recognition are separate concepts ([ADR 0076](decisions/0076-attestation-trust-model-authenticity-validity-and-recognition-are-separate.md)). |
| Recognition | Consuming integrators choose what they recognize. There is no network-wide trust list. |
| History | Revocation adds history; it does not erase history. |
| Settlement | Settlement is not the general-purpose query database. |
| Settlement | Settlement is a public, verifiable, mirrorable log, never federation ([ADR 0070](decisions/0070-settlement-is-a-public-transparency-log.md)). |
| Settlement | No blockchain and no validator or BFT consensus: a transparency log on Postgres. No native currency or token at launch ([ADR 0186](decisions/0186-no-blockchain-validator-consensus-transparency-log-only.md)). |
| Settlement | Settlement storage is Postgres, not a per-node embedded store. |
| Trust anchors | `network_id` alone is never sufficient to trust a server; a client verifies tree heads against the key pinned for the claimed `network_id`. See [network trust anchors](../protocol/network-trust-anchors.md). |
| Batching | One event is never one settlement transaction. |
| Gameplay | Real-time gameplay stays integrator-side. |
| Query | Query databases are projections ([ADR 0075](decisions/0075-durable-protocol-history-is-canonical-query-databases-are-projections.md)). |
| Rebuild | Promised-durable state is reconstructable from canonical history. |
| Presence | Realtime presence is ephemeral and never enters durable history ([ADR 0078](decisions/0078-realtime-presence-is-ephemeral-and-never-enters-durable-history.md)). |
| Integrator Space | Schema publication and data exposure are independently authorized; historical data is read under the schema version it was recorded against. See [integrator space](../protocol/integrator-space.md). |
| Nodes | Nodes are infrastructure providers, not authorities. A node cannot fabricate an issuer's claim. |
| Connectivity | How a node is reached never changes what it may sign, store, verify, or serve ([ADR 0903](decisions/0903-node-participation-must-not-depend-on-public-reachability-nat.md)). |
| Self-hosting | A private instance (its own `network_id`) is cryptographically incapable of merging with the public network's log: a fork, not membership. See [self-hosting](self-hosting.md). |
| SDK | SDKs expose protocol capabilities, not infrastructure topology. |
| Hub | The Hub is a client of the network, not the network ([ADR 0077](decisions/0077-the-hub-is-a-client-of-the-network-not.md)). |
| Registry | Network statistics inform decisions; they never determine trust. |
| Privacy | Network visibility is intentionally scoped. |
| Economy | Universal economic interoperability is not foundational. See [future layers](future-layers.md). |
| Implementation | Domain functionality grows by module, not by new component, unless a real compilation, ownership, or deployment boundary appears. |

Open design questions, deliberately unsettled: identity recovery when every passkey is lost beyond the guardian-based social recovery that exists today; revocation mechanics beyond the append-only history model; offline operation classification and the trust model for client-recorded claims versus server-attested ones ([synchronization](synchronization.md)).

## What survives an integrator's death

If integrator A shuts down tomorrow:

| Survives (Avalon) | Disappears (integrator A) |
| --- | --- |
| Avalon identity | Character |
| Friends | Level, stats, skill trees |
| Guild membership and guild history | Quest progress |
| Achievements and attestations integrator A issued | World position |
| Integrator event results | NPC relationships |
| Ownership and asset provenance (Planned: later phase) | Housing |
| Recognition history | Game-specific inventory |
| Integrator A's registration and key history | Game-specific economy |

Anything in the right column survives only if integrator A explicitly promoted it into durable protocol history while it was alive. This boundary is foundational; see [bindings](../protocol/bindings.md) and [disaster recovery](disaster-recovery.md).

## Architecture tests

Ask these of any proposed change. The expected answer follows each.

- Could the protocol domain types still make sense if PostgreSQL disappeared? Yes.
- Could they still make sense if the settlement backend changed? Yes.
- Could they still make sense if HTTP were replaced? Yes.
- Could an integrator use Avalon without knowing the database topology? Yes.
- Could Avalon rebuild durable query state after losing PostgreSQL? Yes. Tested projection-rebuild machinery backs this ([disaster recovery](disaster-recovery.md)).
- Can a node operator fabricate an issuer claim? No.
- Can Avalon prove that an achievement is meaningful? No.
- Can a receiving integrator choose not to recognize a valid achievement? Yes.
- Does the change preserve integrator independence? Does it give Avalon authority it does not need? Does it force a game-specific concept into the protocol? Does it put hot gameplay on infrastructure that cannot scale with gameplay? Is it needed today rather than architecture for a hypothetical future?

## Scenarios

Concrete cases the design is tested against, each with the page that answers it.

| | Scenario | Answered in |
| --- | --- | --- |
| A | An identity's owner enters a second integrator; it recognizes them without owning their identity | [bindings](../protocol/bindings.md) |
| B | Integrator A issues `Dragon Slayer`; integrator B verifies it | [achievements and attestations](../protocol/achievements-and-attestations.md), [trust model](../protocol/trust-model.md) |
| C | Integrator A revokes it; history shows issued and revoked | [revocation](../protocol/revocation.md) |
| D | Integrator C issues a trivial `Dragon Slayer`; Avalon preserves it, integrator B rejects it | [trust model](../protocol/trust-model.md) |
| E | Integrator A rotates its signing key; old claims stay verifiable | [issuers](../protocol/issuers.md) |
| F | Integrator A's key is compromised; new claims are rejected, history is intact | [issuers](../protocol/issuers.md), [security model](../protocol/security-model.md) |
| G | Integrator A issues a cross-integrator event result that integrator B can verify | [cross-integrator events](../protocol/cross-integrator-events.md) |
| H | A guild exists outside any integrator, with members in three integrators at once | [guilds](../protocol/guilds.md) |
| I | Integrator A shuts down; what survives | the table above |
| J | Every PostgreSQL database disappears; projections are rebuilt | [disaster recovery](disaster-recovery.md) |
| K | A node disappears; SDKs route elsewhere | [nodes](nodes/README.md), [SDK design](../sdk/design.md) |
| L | 1,000 integrators and 100M identities; Avalon is not a gameplay bottleneck | [scalability](scalability.md) |

## Implementation priority

When choosing what to build next, in this order: correct protocol semantics; correct authority boundaries; durable history; verifiable attestations; identity; guild and social primitives; developer experience; indexing and query; the Hub; settlement optimization; portable assets; economy. Settlement throughput is not optimized before the semantics it settles are right.

## Conventions

One page per topic. Each states its invariants up front and describes the current model. Sections that describe code layout, environment variables, or local development belong in the implementing repository ([avalon-protocol](https://github.com/avalon-initiative/avalon-protocol)); pages here link to them.

## Related

- [Getting started](../getting-started/README.md)
- [Protocol concepts](../protocol/README.md)
- [Ecosystem map](../ecosystem/README.md)
- [Glossary](../reference/glossary.md)
- [Status vocabulary](../reference/status-vocabulary.md)
