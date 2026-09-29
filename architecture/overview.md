# Architecture Overview

**Status:** Implemented — later phases (portable assets, economy) are Planned

Avalon is an open interoperability protocol for independently operated integrators: games, apps, and services. It owns the connective layer (identity, social graph, guilds, durable history, provenance) and nothing else. Integrators stay sovereign over their own worlds; Avalon lets those worlds recognize the same users and communities without surrendering control of anything inside them.

This page is the map. Each topic has its own page, listed in the [architecture README](README.md). Terms are defined in the [glossary](../reference/glossary.md).

## What Avalon is

A shared, opt-in network that independent integrators connect to for:

- persistent identity and integrator-scoped profiles
- friends, presence, and guilds (with guild chat)
- achievements as verifiable attestations, with provenance and revocation
- integrator and issuer registration, key lifecycle, and an integrator registry
- integrator events and cross-integrator results (tournaments, seasonal championships)
- Planned: portable assets and ownership history ([future layers](future-layers.md))

An integrator may be commercial, open source, proprietary, self-hosted, community run, an MMO, a strategy game, or an application that is not a game. Avalon has to be useful regardless.

## What Avalon is not

| Not this | Because |
| --- | --- |
| A centralized platform | Avalon does not control identity, distribution, rules, economy, or governance for anyone's integrator. |
| One universal world | There may be thousands of independent worlds; none is canonical. |
| A universal character format | Race, class, level, stats, appearance, and inventory belong to each integrator. See [bindings](../protocol/bindings.md). |
| A blockchain | Settlement is a signed, append-only transparency log with no validator set and no native currency. Real-time gameplay never touches it. See [settlement](settlement.md). |
| A universal economy | No universal currency, market, or financial layer is foundational. See [future layers](future-layers.md). |
| A universal trust oracle | A signature proves who signed a claim, never that the claim is meaningful. See [trust model](../protocol/trust-model.md). |
| A ranking of "good integrators" | The registry publishes facts with definitions, never a score. See [registry](../protocol/registry.md). |

## The fundamental question

What should survive the death of a particular server or integrator?

| Integrator state (belongs to the integrator) | Protocol history (belongs to Avalon) |
| --- | --- |
| HP, XP ticks, movement, physics, combat | achievement issued or revoked |
| NPC state, quests, world state, position | integrator event victory or participation |
| ordinary chat, matchmaking | integrator and issuer registration, key rotation, suspension |
| inventory changes with no interoperability meaning | guild creation, durable membership and role changes |
| game-specific progression and economy | attestations (ownership changes and asset provenance are Planned) |
| | cross-integrator event results and other explicitly durable facts |

The left column is high-volume, temporary, and integrator-owned. It is never a protocol event. The right column is durable facts that may matter outside the integrator that produced them; it is what the settlement layer preserves. [Protocol events](../protocol/protocol-events.md) draws the line precisely.

## Three logical verticals

Avalon separates three categories of state. They are responsibilities first and deployment units second.

```text
                Avalon Network
                       |
       +---------------+---------------+
       |               |               |
   Settlement       Query          Realtime
       |               |               |
      Log          Postgres       Presence
```

- **Settlement (durable history):** canonical protocol facts, commitments, provenance. Not the query database. See [settlement](settlement.md).
- **Query (indexing):** fast reads, profiles, rosters, discovery, statistics. A rebuildable projection of durable history. See [query and indexing](query-and-indexing.md).
- **Realtime (presence):** online state, current integrator, heartbeat. Ephemeral, never in the log. See [presence](../protocol/presence.md) and [communication](communication.md).

These boundaries are load-bearing, although the implementation does not split them into separate services by default. The server binary contains all of them, and an operator chooses per process which roles to run (settlement-only, indexer-only, realtime-only, gateway-only, or combined). One artifact, several deployable node processes. See [nodes](nodes/README.md).

## The big picture

```text
                         AVALON NETWORK
                              |
          +-------------------+-------------------+
          |                   |                   |
      Identity             Social              History
          |                   |                   |
          |            +------+------+            |
          |            |             |            |
       Profiles      Friends       Guilds      Attestations
       Bindings        |             |            |
          |            |          Chat            |
          +------------+-------------+------------+
                              |
                     Integrator Registry
                              |
             +----------------+----------------+
             |                |                |
        Integrator A     Integrator B     Integrator C
             |                |                |
         Characters       Characters       Characters
         World state      World state      World state
         Combat           Combat           Combat
         Economy          Economy          Economy
             |                |                |
             +----------------+----------------+
                              |
                        Avalon SDK / API
                              |
                 +------------+------------+
                 |            |            |
             Query DB      Realtime     Settlement
                 |            |            |
             PostgreSQL     Presence       Log
```

Avalon is the connective tissue. The integrators are the experiences.

## Components and boundaries

The reference implementation ([avalon-protocol](https://github.com/avalon-initiative/avalon-protocol)) builds one server binary from four components plus a command-line tool. Each has a concrete boundary; none exists merely because a concept has a name.

| Component | May know about | Must not know about |
| --- | --- | --- |
| Protocol types | domain types, ids, events, traits | Postgres, any chain, HTTP, the server, any node implementation |
| Settlement | commitments, verification, the ledger and log | general domain semantics (those live in the protocol types) |
| Indexer | consuming events, projections, read models, aggregates | redefining what an event means |
| Server | everything: it composes protocol, settlement, indexer, realtime, and the API | being reached around by clients (the Hub and integrators use the API or an SDK) |
| CLI | development and operations workflows: registration, inspection, diagnostics, migrations | being a second server |

Internal growth is by module, not by new component. A new domain such as assets becomes a module of the protocol types unless a real compilation, ownership, or deployment boundary appears.

The SDKs live in [avalon-sdks](https://github.com/avalon-initiative/avalon-sdks), generated from the server's OpenAPI description. An SDK may know about protocol capabilities, authentication, retries, discovery, and routing; it must not expose Postgres, chain internals, Merkle trees, or node topology to an integrator. See [SDK design](../sdk/design.md).

## Architecture tests

Every proposed dependency or abstraction is checked against the [architecture tests](README.md#architecture-tests): could the protocol types survive PostgreSQL, the settlement backend, or HTTP changing; can a node fabricate an issuer claim (no); can Avalon prove an achievement is meaningful (no); can a receiving integrator decline a valid claim (yes). The answers there are the requirement, not an aspiration.

## Building the smallest thing that does not block the future

The eventual vision is large. The first implementation does not need every SDK, every node role, a universal economy, reputation, or every social feature. It needs a foundation that is correct enough that the project can grow without becoming structurally wrong: correct semantics, correct authority boundaries, and durable history that can actually be rebuilt.

Phases, as laid out in the [design proposal](design-proposal.md#roadmap):

1. **Network:** identity, profiles, friends, guilds and chat, achievements and attestations, integrator and issuer registration, a basic registry and Hub, a developer API. Implemented.
2. **SDKs:** Rust, C#, and TypeScript. Implemented; see [SDK design](../sdk/design.md).
3. **External integrators:** independent integrators validating the protocol. This is an adoption milestone, not a code milestone.
4. **Portable assets:** provenance, ownership, transfers, recognition. Planned.
5. **Economy:** only after the network shows real utility. Planned, and optional.

Implementation priority is in the [architecture README](README.md#implementation-priority).

## Implementation

Status: Implemented. The protocol types, settlement ledger, indexer, and server are in the [avalon-protocol repository](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates). The server covers identity and login, friends and blocks, guilds with channels and events, conversations, achievements, integrator and issuer registration, the registry, a WebSocket presence service, settlement with an outbox, retention, and recovery. The Hub and other first-party clients are separate projects; see the [ecosystem map](../ecosystem/README.md).

## Related

- [Architecture README](README.md)
- [Design proposal](design-proposal.md)
- [Settlement](settlement.md), [query and indexing](query-and-indexing.md), [nodes](nodes/README.md)
- [Protocol concepts](../protocol/README.md)
- [Glossary](../reference/glossary.md)
