# Node Safety Limits

**Status:** Implemented

A public node accepts unauthenticated input from strangers, so every node enforces finite limits and address rules regardless of what the rest of the design allows. This page states the rules and the reasoning. Exact defaults and variable names live with the code and the hosting docs, because they are tuning values, not protocol.

Measured behavior under load is on the [scalability](../scalability.md) page.

## Outbound address policy

Peer URLs arrive through gossip, so they are attacker-influenced. Before a node contacts one, or admits it to the peer table, the address is checked.

- Always refused: non-http(s) schemes, URLs with credentials, query, or fragment, unspecified, multicast, broadcast, reserved, and link-local addresses (including the cloud metadata address).
- Refused unless the operator explicitly allows private peers (default: refused): loopback, RFC 1918, carrier-grade NAT, unique-local, and site-local ranges. Development fleets and local multi-node tests allow them.
- IPv4-mapped IPv6 addresses are judged as the IPv4 address they carry.
- The check covers every address a host resolves to, and the request is then pinned to a checked address, so a different DNS answer at connect time cannot change the destination.
- Outbound clients follow no redirects, use no proxy, and carry a timeout.

## Peer table bounds

Admission is capped and validated, with explicit rejection codes: an invalid, too-long, or forbidden base URL; an unresolvable or unreachable peer; a `network_id` mismatch; rate-limited; and table-full. A new entry into a full table evicts the oldest entry that is neither active nor a bootstrap peer, and if nothing is evictable the newcomer is refused. Refreshing a known entry never evicts. One source address may introduce only a limited number of distinct new peers per minute. Before a brand-new announcer is admitted, the node fetches its status through the pinned client with a short timeout and a body cap and requires the same `network_id`. Gossip-relayed entries go into a separate unverified pool ([discovery and peering](discovery-and-peering.md)).

## Rate, concurrency, and connection limits

- **Per-IP flood ceiling**, applied before authentication and keyed by the connection's peer address only; no request header selects the bucket unless the peer is a configured trusted reverse proxy, in which case the right-most untrusted `X-Forwarded-For` entry is used.
- **Per-principal limit**, applied after a credential is verified and keyed by verified identity or integrator, so users sharing an address each get their own budget.
- **Concurrency limit** that applies backpressure (a bounded wait) and never drops a request without a response.
- **Database pool size** and outbox drain cadence, tunable per deployment.
- **Connection timeouts**: header-read and request timeouts, so idle, slow-header, and slow-body connections are closed. WebSocket upgrades are unaffected.
- **Body size limits**: a general limit, and a smaller one for node-coordination routes, which carry small fixed-shape JSON.
- Over-limit responses are always `429` with `Retry-After`, from either layer.
- Limits are per process by default. An operator can opt into a shared limiter across that one operator's own processes, scoped strictly to one hoster and failing open if the shared store is unreachable. A network-wide shared limiter is deliberately not offered, since it would recreate the single point of control that sharded settlement removes.

## Host resource metrics

`GET /nodes/status` includes a resources block with the node's own CPU, memory, swap, disk, uptime, file-descriptor count, and database pool state. Every field is optional and best-effort; a metric the platform cannot read is absent, not an error. Nothing in it gates protocol behavior or signals a privileged node, and no cross-node aggregation happens in the protocol.

## Public read CORS

A fixed set of read paths (`/nodes/status`, `/nodes/peers`, `/nodes/discover`, `/ledger/sth/latest`, `/ledger/mirror-progress`, and the topology, probe, and trace routes) answer any origin without credentials, so a browser application can read many independently operated nodes without each hoster allowlisting it. Every other route keeps the hub-origin allowlist.

## Implementation

Status: Implemented. Enforcement is in the [server crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/server) of avalon-protocol, and defaults and variables are documented in the protocol repository's [hosting docs](https://github.com/avalon-initiative/avalon-protocol/tree/main/docs). Load-test findings that motivated the timeouts and body limits are summarized in [scalability](../scalability.md).

## Related

- [Nodes](README.md)
- [Discovery and peering](discovery-and-peering.md)
- [Scalability](../scalability.md)
- [Protocol security model](../../protocol/security-model.md)
