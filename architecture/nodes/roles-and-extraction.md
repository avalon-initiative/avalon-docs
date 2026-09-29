# Node Roles and Role Extraction

**Status:** Implemented

A node's role list decides which services a process runs and which routes it serves. By default one process runs everything; each role can be extracted into its own process, with the Gateway reaching extracted roles through configured backing-service URLs. This page describes those mechanics and the operating modes built on them.

Definitions of the roles are on the [nodes page](README.md).

## The role gate

The operator gives a node a comma-separated role list (settlement, indexer, realtime, gateway) or leaves the default, `combined`. The list changes behavior:

- A list that excludes `indexer` (and is not `combined`) routes indexer reads and writes to a remote indexer instead of a local one.
- A list that excludes `realtime` stops the process handling presence and message WebSockets locally and proxies those connections to a remote Realtime node ([ADR 0672](../decisions/0672-realtime-websocket-extraction-proxies-through-gateway-not-direct-connect.md)).
- A list resolving to exactly `settlement` serves a reduced route table with no Gateway-facing module at all.
- `combined` behaves as one process with the full route table.

## Backing-service discovery

A process that does not run a role locally needs the URL of the process that does. This is deliberately static configuration, not a service registry: a fixed deployment needs nothing more elaborate than an operator writing the URL down.

| Role | Shape | If missing while the role is excluded |
| --- | --- | --- |
| Indexer | one base URL, plus an internal shared secret | hard startup failure |
| Realtime | one base URL | hard startup failure |
| Settlement | one URL, or a per-shard map of shard id to URL | a warning only; the node can always commit to its own local ledger |

Indexer and Realtime are each all-or-nothing: with no local role there is exactly one place to route traffic, and no valid URL means the process cannot serve that role, so it refuses to start rather than silently degrade. Settlement is a per-shard map, and a node whose roles exclude settlement but has no remote authority configured simply keeps committing to its own ledger. Every URL passes the same validation, and each gets a startup reachability probe (`GET /nodes/status`) logged as a warning, never a hard failure, since an unreachable but well-formed URL is what a rolling restart looks like.

## Extraction

Historically one node type existed. That is still the default, but each role can now run alone.

- **Operator-internal RPC.** Once a Gateway and its backing processes are separate, the Gateway needs a way to call a role that is not in-process. This is a distinct protocol from the multi-operator, trust-minimized ledger sync: HTTP and JSON under `/internal/*`, gated by a shared-secret bearer token, and refused entirely when no secret is set. A remote role that is unreachable surfaces as a `503`, never conflated with "not found".
- **Indexer.** The server holds either a local indexer or a remote one, chosen at startup. The remote variant makes a write in two steps: the app-data write commits first, then the remote apply is called. That is a deliberate eventual-consistency trade-off (see [query and indexing](../query-and-indexing.md)). A mirror watcher keeps its own local indexer regardless of role.
- **Realtime.** A WebSocket is stateful, so extraction needed a connection-topology decision: proxy through the Gateway, or connect directly. The decision was to proxy through the Gateway, preserving the invariant that a client always talks to one node's URL. The Gateway authenticates the caller locally, then dials the remote node's identical endpoint and pumps frames both ways. The relay already forwards realtime events to same-network peers with a realtime, gateway, or combined role, so a dedicated Realtime node needs no new relay logic.
- **Settlement.** With roles exactly `settlement`, no WebAuthn configuration is required, a dedicated router mounts only the ledger routes, node announce, peer, status, and log-level routes, and the mirror notification route, and Gateway-only workers (outbox, archive expiry, identity locator) never start. Retention pruning, the mirror watcher, the replication gate, and node announcement keep running. A managed-hosting operator wants exactly this: no Gateway attack surface with no legitimate caller ([managed shard hosting](../self-hosting/managed-shard-hosting.md)). The mirror-image case, a Gateway-only node pointed at a remote authority, needed no new mechanism.

Every extraction combination has been live-verified with multiple real server processes, including negative cases (a settlement-only node returning 404 on Gateway routes while serving the ledger; malformed or missing remote URLs refusing to start).

## Replica-only mode

A replica mirrors the network and serves it without authoring anything. It needs no settlement signing key, shard registration, or integrator, and it generates neither a settlement key nor a default shard on first boot (its peer-network identity is still generated). It authors no shard and never signs a tree head. It still mirrors its configured peers, verifies core and sibling shards like any node, serves reads (heads and proofs come from its mirror), relays, answers probes, and announces itself, so it appears in other nodes' peer tables. Witness cosigning is a separate setting: a replica cosigns only if it has its own witness key.

Anything that would append a protocol event is refused with `403` and code `REPLICA_ONLY`: registration, every write that enqueues a ledger event, and the submit, prepare, and finalize ledger endpoints. The outbox worker does not run. Declaring an own shard on a replica is a startup error, and a replica with no mirror peers logs a warning since it has nothing to serve. Its status reports it is not eligible for new registrations.

## First-boot keys

Each of the settlement signing key, submit key, witness signing key, and peer-network identity that the environment leaves unset is loaded from the node's data directory or generated there once, with restrictive file permissions and an atomic no-clobber write. With no shard id and no remote authority configured, the node authors a self-certifying shard `node:<hash of its public key>`, so no registration against any authority is needed. Other nodes can mirror and verify that shard with only the public key its tree-head response carries ([sharding](../settlement/sharding.md)).

## Implementation

Status: Implemented. Role gating, backing-service configuration, the internal RPC, extraction, replica mode, and first-boot key generation are in the [server crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/server) of avalon-protocol. Environment variables and deployment recipes are in the [hosting docs](https://github.com/avalon-initiative/avalon-protocol/tree/main/docs).

## Related

- [Nodes](README.md)
- [Query and indexing](../query-and-indexing.md)
- [Settlement](../settlement.md), [self-hosting](../self-hosting.md)
- [ADR 0672](../decisions/0672-realtime-websocket-extraction-proxies-through-gateway-not-direct-connect.md)
