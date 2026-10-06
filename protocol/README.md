# Protocol Concepts

**Status:** Reference

This section explains the concepts the Avalon Protocol defines: identity, the social graph, guilds, presence, attestations and how they are trusted, integrator registration and data, the durable event log, and how the network's own trust anchors work. Read [architecture](../architecture/README.md) first for the system-level picture (nodes, settlement, indexing, invariants); this section states what each concept means and what is built. The implementation lives in the [avalon-protocol repository](https://github.com/avalon-initiative/avalon-protocol), and every page ends with links into it.

## How the concepts fit together

```text
                          Avalon identity  (self-custodied keys)
                 ┌───────────────┼────────────────┐
             Profile          Social graph        Guild memberships
                 │             (friends,            (network-level,
                 │              blocks)              not game-owned)
                 │
     ┌───────────┴─────────────────────────────────────────┐
     │  Integrator bindings  (the identity opts in, per integrator)
     │       │
     │       ├── capability grants  (what the integrator may do)
     │       └── attestations  (signed claims the integrator issues)
     │              authentic ─ valid ─ recognized  (three separate questions)
     └─────────────────────────────────────────────────────────┘

Everything durable is a protocol event -> hash-chained, Merkle-committed,
signed tree head -> cosigned by independent witnesses -> pinned by clients.
Presence and chat are NOT in that log.
```

Two rules run through every page. An identity and its social data belong to the network and to the person who holds the keys, never to an integrator. And Avalon records provenance but never decides meaning: consumers decide what they recognize.

## Pages

**Identity and people**

| Page | Status | One line |
| --- | --- | --- |
| [Identity](./identity.md) | Implemented | Self-owned, integrator-independent keypair identity; what is promised durable |
| [Authentication and signing keys](./identity/authentication.md) | Implemented | Passkey login, the event-signing key, fresh-signature tier, pairing, session continuation |
| [Recovery and rollback](./identity/recovery.md) | Implemented | Guardian-based recovery and post-compromise compensating events |
| [Per-identity event chains](./identity/event-chains.md) | Partially implemented | Deterministic convergence and fork detection for layer-1 edits |
| [Identity aggregate view](./identity-aggregate-view.md) | Proposed | The target current-state shape of one identity, and the two data layers |
| [Aggregate view field reference](./identity-aggregate-view-fields.md) | Reference | Field-by-field table with backing types |
| [Social graph](./social-graph.md) | Partially implemented | Friends, blocks, and discovery; integrator-facing reads planned |
| [Guilds](./guilds.md) | Implemented | Network-level groups; an integrator is a client, never the owner |
| [Presence](./presence.md) | Implemented | Ephemeral realtime state, never in durable history |
| [Privacy](./privacy.md) | Partially implemented | Visibility scopes, aggregates, and erasure versus permanence |

**Integrators, attestations, and trust**

| Page | Status | One line |
| --- | --- | --- |
| [Bindings](./bindings.md) | Implemented | The identity's consented, scoped participation in an integrator |
| [Issuers](./issuers.md) | Partially implemented | Registration, root and operational keys, key history |
| [Achievements and attestations](./achievements-and-attestations.md) | Implemented | An achievement is an issuer's signed claim, namespaced by issuer |
| [Provenance](./provenance.md) | Implemented | Who said what, when, under which key, and whether it still stands |
| [Trust model](./trust-model.md) | Partially implemented | Authentic, valid, and recognized are three separate questions |
| [Revocation](./revocation.md) | Partially implemented | Revocation adds history; it never erases it |
| [Registry](./registry.md) | Partially implemented | Derived, labeled facts about integrators; never a score |
| [Integrator Space](./integrator-space.md) | Implemented | Integrator-defined schemas, data exposure, and mappings |
| [Cross-integrator events](./cross-integrator-events.md) | Planned | Tournament and campaign results as attestations |

**The durable log and the network's trust**

| Page | Status | One line |
| --- | --- | --- |
| [Protocol events](./protocol-events.md) | Implemented | The event envelope, pipeline, and versioning policy |
| [Ledger entry envelope](./ledger-entry-envelope.md) | Partially implemented | The hashed entry layout byte by byte, stored form, and the proposed full envelope |
| [Event catalogue](./protocol-events-catalogue.md) | Reference | Every event kind, payload, and attribution |
| [Worked ledger example](./worked-ledger-example.md) | Reference | One user's ledger as real ordered events, and what never appears on it |
| [Network trust anchors](./network-trust-anchors.md) | Implemented | Pinning a network id to the operator's real key |
| [Shard trust and names](./network-trust-anchors/shard-identity-and-names.md) | Implemented | Per-shard keys, self-certifying ids, domain-proven names |
| [Witness cosigning](./witness-cosigning.md) | Partially implemented | Independent witnesses replace trust in a single key |
| [Security model](./security-model.md) | Partially implemented | Scoped authority, key domains, and stated limitations |
| [API specification](./api.md) | Partially implemented | Where the wire API and conformance vectors are specified |

## Concepts by question

- *Who am I on the network?* [Identity](./identity.md), then [authentication](./identity/authentication.md).
- *What does a game or app learn about me?* [Bindings](./bindings.md), [privacy](./privacy.md), [Integrator Space](./integrator-space.md).
- *How do achievements work across games?* [Achievements](./achievements-and-attestations.md), [trust model](./trust-model.md), [revocation](./revocation.md).
- *What is actually written to the shared log?* [Protocol events](./protocol-events.md) and the [worked example](./worked-ledger-example.md).
- *Why should I believe a server or its history?* [Network trust anchors](./network-trust-anchors.md) and [witness cosigning](./witness-cosigning.md).
- *What can each party never do?* [Security model](./security-model.md).

## A note on status and vocabulary

Each page states a status at the top (see the [status vocabulary](../reference/status-vocabulary.md)). Where a page mixes states, the page states its main state and labels individual sections. Terms such as integrator, issuer, attestation, and shard are defined in the [glossary](../reference/glossary.md). Some event kinds, routes, and fields still use a `game` spelling ("game.registered", `/games`) from before Avalon supported non-game integrators. Those names are permanent wire strings and apply to every integrator category; see [registry](./registry.md#beyond-games-integrator-category).

## Implementation

The protocol, server, ledger, indexer, and CLI live in [avalon-protocol](https://github.com/avalon-initiative/avalon-protocol); the wire contract is [`docs/generated/openapi.json`](https://github.com/avalon-initiative/avalon-protocol/blob/main/docs/generated/openapi.json). See [API specification](./api.md) for how the contracts and conformance vectors are organized.

## Related

- [Architecture](../architecture/README.md), [overview](../architecture/overview.md)
- [Concepts tour](../getting-started/concepts.md)
- [SDK overview](../sdk/README.md), [integrations](../integrations/README.md)
- [Decision records](../architecture/decisions/README.md)
