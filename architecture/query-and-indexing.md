# Query and Indexing

**Status:** Implemented

The query layer is the second vertical: fast, conventional reads over a projection of durable history. Every query database is a projection, never a source of truth. Fast reads never walk settlement data directly, and the indexer consumes protocol semantics but never redefines them ([ADR 0075](decisions/0075-durable-protocol-history-is-canonical-query-databases-are-projections.md)).

## What it is

A read model. PostgreSQL is a reasonable first implementation and the one in use, but the property that matters is not the engine: it is that the whole thing can be dropped and regenerated from the log. The indexer is what makes "durable history is canonical" true in practice rather than on paper.

Responsibilities:

- consuming durable protocol events, in order, idempotently
- building queryable projections (current state) and historical views
- maintaining the Postgres read models the server serves
- aggregating network statistics for the [registry](../protocol/registry.md)
- exposing data to the server, and through it to SDKs and the Hub

It serves profiles, friends lists, guild rosters, achievement lists and attestation status, integrator discovery, integrator and issuer statistics, recognition relationships, and aggregate network analytics. Point-in-time historical queries are Planned: no history projections exist yet.

## The contract

The indexer has two operations:

- **`apply(event)`**, which must be idempotent. Redelivery, retries, and rebuilds all replay events, and an index that double-counts on replay is not derived state.
- **`rebuild(events)`**, which drops and rebuilds from scratch by replaying every durable event from genesis. This is the proof that the index is a projection, and it is the disaster-recovery path ([disaster recovery](disaster-recovery.md)).

## Not a second source of truth

The indexer does not decide what an event means (semantics live in the protocol types, see [protocol events](../protocol/protocol-events.md)), accept writes that did not come from an event, compute a trust judgment (it derives facts with published definitions, see [trust model](../protocol/trust-model.md)), or store presence or other ephemeral state in rebuild scope ([presence](../protocol/presence.md)).

A "current status" column (an attestation's revoked flag, a member's current role) is a cache of the latest relevant event. History remains in the log.

## Events with their own source of truth

Not every durable event kind has an indexer projection, and that is by design. An event's data has exactly one of two homes.

- **Indexer-projected.** The handler writes only to the outbox. The event's data reaches Postgres when the indexer dispatches it into a projection table (profiles, friendships, guild members, attestations, integrator bindings, integrator schemas). These are the only tables a rebuild truncates and replays, and the only ones "always rebuildable" promises.
- **Server-owned.** The handler writes its own table synchronously, in the same transaction as the outbox enqueue that makes the event durable. The event is emitted for other consumers (mirrors, subscribers, audit), but this server's own reads never go through the indexer. Rebuilding the projections has nothing to do with that table's correctness.

The indexer's dispatch treats a server-owned kind as an explicit no-op, distinct from a genuinely unrecognized kind (an old indexer surviving a new event kind added elsewhere), so a rebuild's log distinguishes "intentionally server-owned" from "unknown".

Server-owned kinds and where their data lives:

| Event kinds | Table |
| --- | --- |
| `game.registered` | integrators, with issuer keys and requested capabilities |
| `issuer.key_added`, `issuer.key_revoked` | issuer keys |
| `issuer.registered` | issuer network registrations (separate from keys) |
| `permission.granted`, `permission.revoked` | permission grants |
| `achievement.defined`, `.definition_updated`, `.definition_retired`, and the `milestone.*` equivalents | achievement definitions (achievements and milestones share one claim-vocabulary table) |
| `milestone.issued`, `milestone.revoked` | achievement attestations |
| `identity.recovery_configured` | recovery guardians and settings |
| `identity.recovery_requested`, `.recovery_approved`, `.recovery_cancelled`, `identity.recovered` | recovery requests and approvals; a recovery updates the identity's keys |
| `guild.updated`, `guild.owner_transferred` | guilds |
| `guild.role_defined`, `guild.role_deleted` | guild roles |
| `guild.channel_created`, `.channel_renamed`, `.channel_archived` | guild channels |
| `guild.game_associated` | guild-integrator associations |
| `guild.favorite_games_updated` | guild favorite integrators |

Bindings and permission grants are genuinely server-owned capability and grant state, not "two writers of one projection". The event catalogue itself is in [protocol events](../protocol/protocol-events.md).

`achievement.issued` and `achievement.revoked` are the one asymmetric case: they get both a direct server-owned table write and an indexer projection that feeds the registry's achievement metrics. Milestone issuance and revocation deliberately get only the direct table, because those metrics are achievement-scoped by definition. Whether milestones should feed their own or a combined metric is Undecided.

## Settlement versus querying

Kept apart on purpose: the settlement component commits and verifies, and the indexer reads and aggregates. They may share a database today. They must never share a definition of truth. A server reading directly from the ledger to answer a profile lookup is exactly what this separation exists to prevent. The narrow exceptions are a caller's own history and the subject-filtered entry read ([settlement](settlement.md#query-reads-are-not-settlement-reads)). A source-scanning test guards that the main handlers never query the profile table or the ledger directly.

## Scaling the read side

Indexers are the natural place to partition and specialize: an operator can run indexer plus gateway nodes without settlement ([nodes](nodes/roles-and-extraction.md)), shard projections by domain, or keep a registry-only projection. Rebuild time is a first-class scaling dimension ([scalability](scalability.md)).

A gateway can run without a local indexer by calling a remote one. Each write becomes two steps: the app-data write commits in its own transaction, and then the remote apply is called. That is a deliberate eventual-consistency trade-off, not full atomicity. Between the commit and the remote call completing, or for as long as a transient failure takes to be corrected, the app-data write is durable and authoritative while the remote projection can lag or miss it. A failure there is logged loudly but does not fail the request, and the rebuild guarantee lets the projection catch up. A background retry or backfill for this gap is a possible improvement, not built. The default combined deployment is unaffected: there the apply is atomic with the write.

## Implementation

Status: Implemented. The Postgres indexer, its per-read-model projection modules, the registry projections, the rebuild command, and the boundary tests are in the [indexer crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/indexer) and [server crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/server) of avalon-protocol. Rebuild is exercised by a live test described in [disaster recovery](disaster-recovery.md).

## Related

- [Settlement](settlement.md)
- [Disaster recovery](disaster-recovery.md)
- [Nodes](nodes/README.md)
- [Registry](../protocol/registry.md), [protocol events](../protocol/protocol-events.md)
- [ADR 0075](decisions/0075-durable-protocol-history-is-canonical-query-databases-are-projections.md)
