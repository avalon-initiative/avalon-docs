# Connectivity

**Status:** Partially implemented — detection, relays, hole punching, connectivity reporting, and stream transport for node-to-node requests are live; admitting a node with no reachable URL, relay selection, and transport selection are Planned

Connectivity is how other nodes and clients can reach a node. It is a property of the network path, not of the node's standing: a node in any connectivity state is a full node. This page defines the states, how a node detects which one it is in, and how relays let a node that cannot accept inbound connections still be reached.

The decision behind this is [ADR 0903](../decisions/0903-node-participation-must-not-depend-on-public-reachability-nat.md): participation must not depend on public reachability.

## States

| State | Meaning | Wire name | Status |
| --- | --- | --- | --- |
| Direct | Peers open connections straight to a routable address of this node. | `direct` | Implemented |
| NAT-traversed | Peers reach this node over a direct connection established by hole punching, with no routable address of its own. | `nat_traversed` | Implemented; attempts start once a relayed connection exists |
| Relayed | Peers reach this node through a relay node that only carries bytes. | `relayed` | Implemented |
| Outbound-only | This node only dials out. Peers never open a connection to it; it pulls and pushes over connections it initiated. | `outbound_only` | Implemented |

Preference order is `direct`, then `nat_traversed`, then `relayed`, then `outbound_only`. When more than one path exists, selection uses the most preferred one and falls back automatically. Outbound-only is the floor, not a failure: it is a complete way to participate. The order is a transport preference only and ranks nothing about the node.

## Separate from authority

Connectivity is independent of authority, roles, capabilities, services, and trust. No state changes what a node may sign, store, verify, mirror, or serve, and a publicly reachable node is not more authoritative than an outbound-only one. Relays and traversal are transport: they never create separate networks, authorities, or state domains, and they never relax verification. Every rule in [node authority](README.md#node-authority) holds in every state.

## Where it is advertised

All additions are additive; no existing field changes meaning or is removed.

- `GET /nodes/status` carries a `connectivity` field with one wire name above (Implemented), plus `reachability`, `confirmed_external_addrs`, `relay_reservations`, `relayed_listen_addrs`, `hole_punches`, and `punched_peers` described below.
- Announce requests, the responder's own entry in announce responses, and peer table entries carry an optional `connectivity` field (Implemented). Older peers omit it and readers treat a missing value as unknown, never as `direct`.
- `GET /nodes/topology` carries `connectivity` on the node itself, on each neighbor, and on each known peer (Implemented). It is omitted until detection has finished for the node itself, and for a peer that does not announce one. Each neighbor's `latency` also carries a `path` (`direct`, `traversed`, or `relayed`); see [topology and tracing](topology-and-tracing.md#node-topology-view) for what populates it today.

Connectivity is self-reported until an observer can confirm it, so consumers treat it as a hint for path selection and display, never as an input to any trust or authorization decision.

## Detection

Every node runs libp2p AutoNAT as both client and server on its DHT swarm. As a client it asks connected peers to dial it back and learns whether it is dialable; as a server it dials back peers that ask, within a rate limit. Detection runs in the background and never delays startup: until a probe finishes, reachability is `unknown`.

| `reachability` | `connectivity` |
| --- | --- |
| `public` | `direct` |
| `private`, a hole-punched direct connection is open | `nat_traversed` |
| `private`, at least one accepted relay reservation | `relayed` |
| `private`, no reservation | `outbound_only` |
| `unknown` | omitted; never reported as `direct` |

`unknown` also covers a node with the DHT or AutoNAT disabled and a node with no peer to probe it, such as the first node in a network. `GET /nodes/status` reports `confirmed_external_addrs` (addresses a peer confirmed by dialing them; empty unless `public`), `relay_reservations` (each with relay peer id, relayed address, and renewal count; empty unless `private`), and `relayed_listen_addrs` (the circuit addresses peers can dial).

The addresses a node advertises in announce are its confirmed addresses, its accepted relayed addresses, and an operator-stated external address that AutoNAT also probes. Bind addresses are never advertised unconfirmed, and a relayed address is advertised only after the relay accepts the reservation. A network therefore needs at least one node with an operator-stated external address (a seed) so other nodes have something to dial and be probed through.

Known limitation: detection is AutoNAT v1, where a peer the node has already talked to dials it back. A restricted-cone NAT lets that peer's address through, so the node is reported `public` and `direct` although a peer it never contacted cannot reach it. Detecting this needs a dial-back from an address the node has never contacted, which v1 does not do.

Dial-back safety: the server dials only the IP it observed on the requesting connection, never one the requester supplies; refuses observed private and loopback addresses unless explicitly allowed for development; drops peers connecting from always-refused addresses; and answers a bounded number of dial-backs per minute in total and per peer.

## Relays

Nodes speak libp2p circuit relay v2 on the same DHT swarm. A relay carries bytes and nothing else: the two ends of a relayed connection run their own noise handshake over the circuit, so the relay cannot read or alter the traffic and never holds state or authority.

**Client role** (on by default). A node whose reachability is `private` reserves a slot on a relay and listens on its circuit address; once the relay accepts, that address is advertised and connectivity becomes `relayed`. Nothing is reserved while reachability is `unknown`, and reservations are released if the node turns out to be `public`. A node holds up to a small configurable number of reservations at once (default 2).

Relay candidates are, in order: relays the operator listed, then connected peers that advertise the relay hop protocol. The choice is deterministic; ranking by latency or capacity is Planned (#914); no selection beyond that order exists yet. Candidate addresses obey the [outbound address policy](safety-limits.md#outbound-address-policy). Reservations are managed without a restart: the client renews each before expiry; when a relay refuses, times out, drops the connection, or stops, the reservation is dropped, that relay is skipped for 30 seconds, and the next candidate is tried at the next 5-second reconcile.

**Server role** (off by default). A relay is only useful when peers can dial it, so it advertises the hop protocol only while its reachability is `public`, or `unknown` with an operator-stated external address; a `private` node never relays. Every limit is finite, at least 1, and has a ceiling.

| Limit | Default | Ceiling |
| --- | --- | --- |
| Reservations at once | 128 | 4096 |
| Reservations per peer | 2 | 4096 |
| Reservation lifetime | 3600 s | 86400 s |
| Circuits at once | 16 | 1024 |
| Circuits per peer | 4 | 1024 |
| Circuit lifetime | 120 s | 3600 s |
| Bytes per circuit | 524288 | 67108864 |

A node with the relay server role reports its limits and live usage in `GET /nodes/status` under `relay_server` (omitted when the node does not relay). `limits` repeats the table above for this node. `usage` has the reservations and circuits open right now plus totals since start: reservations and circuits accepted, denied, and closed, reservations timed out, and circuits closed with an error. Bytes carried are bounded per circuit but not measured.

libp2p's per-peer and per-IP request limiters also apply. A relay dials nothing itself: circuits run over connections the two peers opened to it. With the defaults at most 16 circuits are open, each cut after 2 minutes or 512 KiB, bounding relayed traffic to about 8 MiB per circuit window. Relayed circuits are limited by design, so they suit control traffic and small exchanges.

## Hole punching

Nodes run libp2p DCUtR on the same swarm (`AVALON_DCUTR_ENABLED`, default on). When two nodes are connected through a relay, the node that was dialed offers its observed addresses, the two exchange them over the relayed connection, and both dial each other at the same moment so that each NAT sees an outbound packet first. If a direct connection results, it replaces the relayed one for that peer; libp2p retries a few times before giving up.

Which local port a dial leaves from matters for this. A dial to a direct address uses a fresh port rather than the listen port, so a NAT mapping left behind by a failed direct dial cannot block a later punch from the listen port. A dial through a relay, or to a peer whose known addresses include a relayed one, keeps the listen port, so the relay sees the port the punch will use. Direct addresses are tried before relayed ones.

A failed attempt never drops the relayed connection: the peer stays reachable through the relay and the node keeps reporting `relayed`. `GET /nodes/status` lists the most recent attempts, oldest first and bounded (`hole_punches`: peer id, `succeeded`, and an `error` on failure), and `punched_peers`, the peers a hole-punched connection is open to right now. A private node reports `nat_traversed` while `punched_peers` is not empty and falls back to `relayed` or `outbound_only` when the last punched connection closes.

Whether a punch can succeed depends on the NATs. Endpoint-independent mapping (the cone types) usually works; a symmetric NAT that picks a new external port per destination usually does not, and the connection stays relayed. A successful punch shows the other node this node's public address, which the relay already knew.

## Node-to-node requests over libp2p streams

Node-to-node HTTP can ride a libp2p stream instead of a TCP connection to a URL, so relays and hole punching carry it and a peer with no usable URL is still reachable. A stream base URL is `p2p://<libp2p peer id>`. The request and response keep their HTTP shape (method, path and query, headers, body, status); one exchange uses one stream, on a protocol id scoped to the `network_id`, so a node of another network never negotiates it. The server handles the request by dispatching it into the same router the HTTP listener serves, so authentication, validation, and rate limits behave as they do over HTTP.

**When a stream is used.** A peer is addressed by stream when it has a verified libp2p id and either its connectivity is `relayed` or `outbound_only` or its base URL is not a usable http(s) URL. Otherwise its base URL is used. Separately, any request to a peer whose id is verified falls back to a stream when the HTTP attempt fails to connect (and, for reads only, when it times out); a write is never retried after a timeout, since it could apply twice. The announce loop, relayed trace forwarding, realtime relay, chat replication, and cosign gathering pick the address this way; mirror polling and settlement submission start from the configured http(s) URL and use the fallback. Probe measures the target's base URL over HTTP.

**Authenticated peer id.** The sender of a stream request is the peer id authenticated by the noise handshake, which a relay cannot forge. A peer id counts as bound to a peer table entry only when the entry's own URL reported that same id (in its status answer or its own announce response entry), never through gossip or a third party. Streams are routed only by bound ids. Three routes that inject data without a credential of their own (`/nodes/relay`, `/nodes/replicate-chat`, `/mirror/notify`) are refused over a stream unless the sender is bound. Binding says which node sent a request; it is not a statement that the node is trusted ([discovery and peering](discovery-and-peering.md#identity-binding-is-not-a-security-boundary)).

**What is reachable.** Only an explicit set of node-to-node routes is served over a stream: announce, peers, discover, status, relay, probe, trace, topology, chat replication, mirror notify, and the read and write ledger routes nodes call on each other (tree heads, proofs, entries, submit, batch prepare and finalize, cross-shard root, remote submit status, mirror progress). Admin, internal-role, and every user-facing route are refused with 403, as are paths with encoding, dot segments, or backslashes. Only GET and POST are carried, and connection-framing and proxy headers (`Host`, `X-Forwarded-For`, and similar) are dropped so a stream cannot spoof a client address.

**Bounds.** Every limit is finite, at least 1, and has a ceiling; an out-of-range value is a startup error. Frame lengths are checked before any allocation.

| Limit | Default | Ceiling |
| --- | --- | --- |
| Request body | 1 MiB | 16 MiB |
| Response body | 8 MiB | 64 MiB |
| Request timeout | 30 s | 300 s |
| Requests being served at once | 64 | 1024 |
| Requests being served per peer | 8 | 256 |
| Request bytes buffered at once | 64 MiB | 1 GiB |
| Established connections | 512 | 8192 |
| Connections per peer | 4 | 64 |
| Pending incoming connections | 64 | 1024 |

Streams in flight in either direction are capped at 16, headers at 32 lines and 16 KiB, and the path at 4 KiB. A request over a limit gets 429 (with `Retry-After` for the concurrency limits) before its body is read. Peers that are not bound share one synthetic client address for per-IP limits, so free peer ids cannot multiply a rate budget, and each bound peer gets its own, so the table cap bounds the number of buckets. A stream request is answered 503 while the node is starting or shutting down. A response is carried whole, not streamed.

**Not done yet.** Stream transport is not selected by measured quality or by policy; the rule above is the whole choice. A peer known only from gossip and confirmed over libp2p is not bound, so the paths above do not address it by stream. WebSocket upgrades and user-facing routes are not carried. Clients and SDKs do not use it.

## Planned and unbuilt

- Admitting a node with no `AVALON_NODE_URL`: announcing needs this node's own reachable base URL, and a new announcing peer is verified by a direct inbound fetch of its URL, so an outbound-only node is found through gossip and confirmed over libp2p rather than announcing itself (#918).
- Path labels on probe and trace results, and a `path` that reflects the transport used: every round trip the server records today is labeled `direct`, including announces carried over a stream.
- A fronting gateway for nodes that cannot be reached, and a policy for choosing between transports.
- Relay selection by latency or capacity (#914).

## Implementation

Status: Partially implemented, as above. Detection, relays, and the status fields are in the [server crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/server) of avalon-protocol, and the connectivity type is in its [protocol crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/protocol). Lab procedures for testing NAT behavior are in the [avalon-protocol docs](https://github.com/avalon-initiative/avalon-protocol/tree/main/docs).

## Related

- [Nodes](README.md)
- [Discovery and peering](discovery-and-peering.md)
- [Topology and tracing](topology-and-tracing.md)
- [ADR 0903](../decisions/0903-node-participation-must-not-depend-on-public-reachability-nat.md)
