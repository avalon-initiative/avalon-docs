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

## Relays and hole punching

Relays and hole punching let a node with no open port take part, and they add an abuse surface. This is the threat model and what each control does. The mechanics are on the [connectivity](connectivity.md) page.

| Threat | Control |
| --- | --- |
| A relay is used for free bandwidth | Every relay resource has a finite, configurable bound with a safe default: reservations and circuits in total and per peer, reservation and circuit lifetimes, and bytes per circuit. A circuit is cut at its lifetime or byte cap. Relaying is off unless the operator turns it on. |
| Reservations or circuits are exhausted to lock others out | The per-peer and total limits above, plus libp2p's per-peer and per-IP request limiters. A refused request costs the relay one reply. A relay reports limits and usage in `GET /nodes/status` (`relay_server`), so an operator can see pressure and the denial counts; bytes carried are bounded per circuit but not measured. |
| Dial-back or hole punching is used to make a node attack a third party | A node dials back only the IP it observed on the requesting connection, refuses private and loopback addresses unless allowed for development, and answers a bounded number of dial-backs per minute. Every libp2p address that enters the peer table is validated under the outbound address policy before it is stored or dialed. |
| A relay reads or alters traffic, or pretends to be a peer | Both ends run their own noise handshake over the circuit, so the relay carries bytes it cannot read, and a peer id is authenticated end to end: a relay that terminates the circuit itself cannot complete the handshake as the peer. A forged address that names another peer id is dropped at admission. |
| A node picks a hostile or unstable relay, or ends up with every reservation on one network | Selection skips relays in backoff and prefers operator-listed relays, then a relay outside every network already held (IPv4 /24, IPv6 /48 or DNS host). Failures back a relay off for 30 seconds, doubling to 15 minutes, and only a renewal clears it. A relay's reported capacity is only a tie-break. Sybil relays across different networks, NAT64, and self-reported addresses are not defended against ([relay selection](connectivity.md#relay-selection)). |
| A peer table fills with unverifiable relayed entries | A gossiped peer with no reachable URL waits in the small unverified pool. It is promoted only when an outbound libp2p connection authenticates its peer id. Pool size, dials per scan, and table size are all bounded. |
| A relay operator learns who talks to whom | It does, and this is stated rather than hidden. |

What a relay operator can observe: the address and peer id of each node that reserves a slot or opens a circuit, the peer id at the other end, when circuits start and stop, and how much moves through them. It cannot read or change the content, and it holds no state or authority: a relay is transport, never a source of truth. Relay use is logged with reasons for denials.

What hole punching exposes: the two nodes learn each other's public IP address to open the direct connection. The relay already knew both. A node that does not want its address shown to a peer can turn hole punching off (`AVALON_DCUTR_ENABLED=false`) and stay on the relay.

One detection limit is stated here because it affects what a node believes about itself: AutoNAT v1 is a self-measurement, and a restricted-cone NAT is a case it handles by outcome rather than by design: in the lab such a node is observed to be reported `private` and `relayed`, because direct dials leave from a fresh port and open no mapping on the listen port ([connectivity](connectivity.md#detection)). Reported reachability stays a hint, not a guarantee for every NAT type.

## Node-to-node streams

Node-to-node requests carried over libp2p streams ([connectivity](connectivity.md#node-to-node-requests-over-libp2p-streams)) are bounded like any other unauthenticated input. Request and response bodies, request time, requests in flight in total and per peer, buffered request bytes, header count and size, path length, and the swarm's connection counts all have finite defaults and ceilings; an over-limit request is answered 429 before its body is read. Only a fixed allowlist of node-to-node routes is served, and admin, internal, and user-facing routes are refused. Failover between HTTP and streams ([transport failover](connectivity.md#transport-failover)) is bounded the same way: the per-peer outcome record holds at most 4096 peers, a demotion lasts 10 to 300 seconds, a dial waits at most `AVALON_NODE_HTTP_CONNECT_TIMEOUT_SECS` (default 15, at most 60) with at most 32 requests waiting per peer, and a request whose caller gave up is not delivered later. A stream request that falls back to a peer's URL is made only for reads, only to the one bound entry holding the id, only after the URL passes the outbound address policy, through the address-pinned client with no redirects and no proxy, and with only `Content-Type`, `Accept`, and the trace header forwarded and no body. Writes are never replayed after a timeout, and an application answer is never retried elsewhere. Peers whose libp2p id is not bound to a peer table entry share one synthetic client address, so inventing peer ids does not multiply per-IP budgets. The three routes that write data without their own credential are limited to bound peers, which narrows who can reach them and is not an authorization check ([identity binding](discovery-and-peering.md#identity-binding-is-not-a-security-boundary)). A `p2p://` entry, being free to create, is not bound for them, is capped in the table, the unverified pool, and the shard registry, and is evicted before HTTP entries ([nodes with no public URL](connectivity.md#nodes-with-no-public-url)).

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
