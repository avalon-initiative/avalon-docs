# Topology and Tracing

**Status:** Implemented — probe and trace carry no path label yet, and the latency `path` is not yet populated beyond `direct`

Each node can describe the part of the network it can see, measure its round trip to another node, and trace the path a request takes. These read models exist for observability tools such as the [topology visualizer](../../ecosystem/topology.md). Everything they report is self-reported and advisory, and none of it feeds trust, admission, or authorization.

## Node topology view

`GET /nodes/topology` is this node's own view of the network. It is public, read-only, briefly cacheable, and served unless the operator disables it (default: served). It returns:

- `self`: base URL, peer-network identity, protocol version, network id, roles, a stale flag, resource metrics, this node's coordinate, its [connectivity](connectivity.md) (omitted until detection finishes), and the latest tree size and head time of each shard this node authors.
- `neighbors`: the active announce set, with roles, protocol version, peer identity, last announce time, whether it is a bootstrap peer, the neighbor's self-reported connectivity, the measured round-trip statistics (labeled with this node as observer, and carrying the `path` the measurement took), and the neighbor's own coordinate ([discovery and peering](discovery-and-peering.md)).
- `known`: peer-table entries that are not active neighbors, newest first, bounded by a limit, with the total before the limit, each with its self-reported connectivity.
- `mirrors`: one entry per configured mirror source, with the observed tree size, entries mirrored, last mirrored time, lag in entries, and any unresolved equivocation findings. Shards auto-mirrored from gossip are not listed.
- `generated_at`.

No aggregator exists. Each node reports only what it sees, and clients assemble the graph by walking node to node. The response is assembled from local state only and carries nothing that is not already public elsewhere, except the observer's own measurements. Connectivity is a hint each node reports about itself, absent for a peer that does not announce one and never assumed to be `direct`.

The `path` on a round trip is `direct`, `traversed` (a hole-punched connection), or `relayed`, and a relayed measurement includes the relay's hop, so it is never reported as direct. The field and its wire names are defined, but the server currently labels every round trip it records `direct`, including announces carried over a libp2p stream, so a consumer cannot yet tell a relayed latency from a direct one by this field. Use the neighbor's `connectivity` as the hint meanwhile. Path labels on probe and trace results are Planned.

## Probe

`POST /nodes/probe` lets a client ask any node it can reach to measure its round trip to another node it knows. The body names a target and a sample count from 1 to 3. The node makes up to that many sequential status requests to the target and returns the samples, the minimum and median, and an error class (`timeout`, `unreachable`, `bad_status`) on failure.

The target must already be in the probing node's peer table on its network, so the endpoint is not an open proxy. It returns timings only; nothing the target sent is passed back. Outbound requests go through the [outbound address policy](safety-limits.md#outbound-address-policy), and the target is measured by its base URL over HTTP, so a node with no usable URL cannot be probed yet. Dedicated per-IP and concurrency limits apply. Timings are the probing node's own observations (the first sample includes connection setup), advisory and unverified.

## Trace

`POST /nodes/trace` is a traceroute across the overlay: which nodes carry a request toward a target and how long each leg takes. The body has a target, a time-to-live from 1 to 16 (default 12), and an optional trace id. The receiving node applies the next-hop rule below toward the target and, unless it is the target, forwards the same request to the chosen active neighbor and waits. Each node prepends its own hop entry to the path that returns, so the first node returns the whole path: trace id, target, whether it was reached, a stop reason, total time, and hops (index, base URL, roles, protocol version, processing time, and time to the next hop).

- It traces the overlay route (the path gossip and key-space lookups take), not every request type. Most node-to-node calls are direct. A forwarding hop to a neighbor with no reachable URL goes over a libp2p stream ([connectivity](connectivity.md#node-to-node-requests-over-libp2p-streams)); the hop entry does not say which transport it used.
- Every forwarding decision is the next-hop rule's, so the cost is one forward per hop with no fan-out, and the target is contacted only if it is an active neighbor.
- Stop reasons when the target is not reached: `ttl`, `no_route` (with a detail such as `no_neighbors`, `no_progress`, `all_visited`, `foreign_network`), `loop`, `timeout`, and `target_unreachable`.
- Forwarded requests carry a visited list and a remaining time budget (default 10 s, clamped to 15 s). Every request field is untrusted and clamped, and a downstream response is validated before use (same trace id, bounded hop count, clipped strings, finite non-negative numbers, bounded size).
- Durations are relative, each measured on the reporting node's own clock; no timestamp crosses nodes.
- **The data is self-reported.** Each hop describes itself and the assembling node cannot verify it. Treat it as advisory, never as a verified fact about the path.

## Operation tracing

`POST /nodes/trace` follows the overlay route. Operation tracing follows a real forwarded request: a request carrying an `X-Avalon-Trace` header (a UUID) asks the nodes that handle or forward it to report a hop, and nothing else about the request changes. The response carries an `X-Avalon-Trace-Hops` header holding the branches and hops, as unpadded URL-safe base64 of a JSON structure.

Covered operations are the realtime relay (a presence update, or a channel or conversation message send or delete, causes the receiving node to relay to every eligible peer, one branch per target) and remote settlement submit (a write on a node configured with a remote authority is committed later by the outbox worker; its path is kept in a bounded in-memory store for ten minutes and read back through `GET /ledger/remote-submit-status` with the same trace id).

Invariants: requests without the header behave exactly as before; tracing adds no outbound calls (the header rides calls already made), except that a traced relay fan-out is awaited so the response can carry its branches; downstream hop data is untrusted and validated; trace data never fails the operation; the layer is not mounted when topology is disabled; and branch, hop, and header sizes are capped, with anything beyond dropped and a `truncated` flag set. The header is meant for non-browser clients, and browsers can send it and read the hop header back through CORS.

## Overlay next-hop selection

Given a target node, a pure function picks where a node forwards:

1. If the target is an active neighbor, the next hop is the target itself.
2. Otherwise the unvisited active neighbor with the smallest XOR distance to the target, and only if it is strictly closer than the node itself, so every hop makes progress.
3. Otherwise no route, with a reason (target is self, foreign network, no neighbors, all visited, no progress).

Only nodes on the caller's own `network_id` are considered. The result is deterministic for a given neighbor set, and the visited set plus the strict progress rule rule out cycles.

**Key derivation.** When the node, the target, and every candidate neighbor announce a peer-network identity, a node's key is SHA-256 of that identity's bytes, the same key libp2p Kademlia uses for its XOR metric, so routing and DHT lookups agree on distance. If any of them lacks one, all nodes in that decision use SHA-256 of the canonical base URL (trimmed, trailing slashes removed, ASCII-lowercased), so distances always come from one key space.

The DHT resolves which nodes hold an interest ([distributed topology](../distributed-topology.md)); this rule chooses which neighbor to forward a request toward a named node.

## Exposure and opt-out

The topology, probe, and trace routes are public and readable from any origin by default. A hoster who prefers not to publish a neighbor list can turn them off, after which they return 404. The peer and discover routes stay available either way because peers rely on them ([safety limits](safety-limits.md)).

## Implementation

Status: Implemented. Topology, probe, trace, operation tracing, and next-hop selection are in the [server crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/server) of avalon-protocol; their request and response shapes are in the [OpenAPI description](https://github.com/avalon-initiative/avalon-protocol/blob/main/docs/generated/openapi.json). The Rust SDK includes a topology walker, and live coverage is in the protocol repository's live-test suite.

## Related

- [Nodes](README.md)
- [Discovery and peering](discovery-and-peering.md), [connectivity](connectivity.md)
- [Topology visualizer](../../ecosystem/topology.md)
- [Distributed topology](../distributed-topology.md)
