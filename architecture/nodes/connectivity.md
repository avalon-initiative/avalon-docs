# Connectivity

**Status:** Partially implemented — detection, relays, relay selection, hole punching, connectivity reporting, stream transport with failover between HTTP and streams, path labels, and admitting a node with no public URL are live; relay re-selection, probing, a relay flag in announce, a fronting gateway, and credentials for the write routes are Planned

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
- `GET /nodes/topology` carries `connectivity` on the node itself, on each neighbor, and on each known peer (Implemented). It is omitted until detection has finished for the node itself, and for a peer that does not announce one. Each neighbor's `latency` also carries a `path` (`direct`, `traversed`, or `relayed`); see [topology and tracing](topology-and-tracing.md#node-topology-view) for what populates it.

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

Known limitation: detection is AutoNAT v1, where a peer asks the node to be dialed back, and a restricted-cone (address-restricted) NAT admits a packet only from an address the node has already sent to. A dial to a direct address leaves from a fresh local port rather than the listen port ([hole punching](#hole-punching)), so nothing leaves the listen port to open a mapping for the dialing peer's address. In the NAT lab, a node behind a restricted-cone NAT is observed to be reported `private` and then `relayed`, not `public`. The only dials that keep the listen port are those through a relay or to a peer whose known addresses include a relayed one; whether such a connection could let a dial-back through was not verified. Reachability is therefore a self-measurement under these rules, not a guarantee about every NAT type, and consumers keep treating it as a hint.

Dial-back safety: the server dials only the IP it observed on the requesting connection, never one the requester supplies; refuses observed private and loopback addresses unless explicitly allowed for development; drops peers connecting from always-refused addresses; and answers a bounded number of dial-backs per minute in total and per peer.

## Relays

Nodes speak libp2p circuit relay v2 on the same DHT swarm. A relay carries bytes and nothing else: the two ends of a relayed connection run their own noise handshake over the circuit, so the relay cannot read or alter the traffic and never holds state or authority.

**Client role** (on by default). A node whose reachability is `private` reserves a slot on a relay and listens on its circuit address; once the relay accepts, that address is advertised and connectivity becomes `relayed`. Nothing is reserved while reachability is `unknown`, and reservations are released if the node turns out to be `public`. A node holds up to a small configurable number of reservations at once (default 2).

Relay candidates are the relays the operator listed (`AVALON_RELAY_ADDRS`) and connected peers that advertise the relay hop protocol; at most 64 are remembered. Which of them to reserve with is decided by [relay selection](#relay-selection). Candidate addresses obey the [outbound address policy](safety-limits.md#outbound-address-policy). Reservations are managed without a restart: the client renews each before expiry; when a relay refuses, times out, drops the connection, or stops, the reservation is dropped, that relay is backed off, and the next candidate is tried at the next 5-second reconcile. A reservation the relay leaves unanswered for 30 seconds is abandoned the same way.

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

## Relay selection

A `private` node with fewer reservations than it wants picks the next relay at each reconcile, in this order.

1. **Hard skips.** A relay that already holds a reservation for this node, or is in backoff, is not considered.
2. **Operator-listed before discovered.** Listed relays are considered first, in list order; discovered relays only when no listed one is eligible.
3. **Spread across networks.** Within that group, a relay outside every network already held is preferred: the IPv4 /24, the IPv6 /48, or the DNS host name of a held relay counts as held, and a relay with no IP address or host name counts as outside. A relay's network is taken from its open direct connection when there is one, else from the address it reported or that would be dialed. When every relay in the group shares a network with a held one, the best relay in the group is taken, so a deployment on a single network still reaches its full reservation count. A slot filled this way is not rebalanced when a more diverse relay becomes available.
4. **Order among discovered relays.** Round trip, compared on a fixed 10 ms grid (a relay with no measurement ranks after every measured one), then outcome history, then the relay's self-reported free capacity as a tie-break, then peer id. Operator-listed relays are ordered by list position alone.

Outcome history scores accepted reservations (counted up to 4) and renewals (up to 16) for a relay and subtracts a penalty for each accepted reservation that was later lost (counted up to 4, weighted double, and halved at each renewal so an old loss fades). The caps keep a relay that accepts and drops repeatedly from outscoring one that stays up.

Capacity is only a tie-break, and it is not fed in production today: nothing records a relay's reported capacity, so the step never separates two relays.

**Backoff.** A relay that refuses, times out, or drops is skipped for 30 seconds after the first consecutive failure, doubling with each further one up to 15 minutes. Only a renewal clears it: a relay that accepts and then drops never does. Only an accepted reservation that was lost counts against the relay's history; a refusal, a dial failure, or an unanswered reservation backs the relay off without that penalty.

**Where latency comes from.** The round trip for a relay is this node's smoothed announce round trip to the peer-table entry that claims the relay's libp2p id. It is used only when exactly one bound entry holds that id and a libp2p connection to the peer is open, and entries known only from gossip are ignored. It measures the round trip to the entry's URL, not to the relay connection. Because binding carries no proof of key possession ([discovery and peering](discovery-and-peering.md#identity-binding-is-not-a-security-boundary)), a node that falsely claims a relay's id can skew or hide that relay's latency; this changes which relay is tried first and never who may relay or what a relay may do.

Not built: probing relays before choosing, replacing a held reservation when a better relay appears, and a flag in announce that says a node serves as a relay. Choices are made when a slot is empty and never revisited.

## Hole punching

Nodes run libp2p DCUtR on the same swarm (`AVALON_DCUTR_ENABLED`, default on). When two nodes are connected through a relay, the node that was dialed offers its observed addresses, the two exchange them over the relayed connection, and both dial each other at the same moment so that each NAT sees an outbound packet first. If a direct connection results, it replaces the relayed one for that peer; libp2p retries a few times before giving up.

Which local port a dial leaves from matters for this. A dial uses a fresh port rather than the listen port unless any of the addresses it tries is relayed, so a NAT mapping left behind by a failed direct dial cannot block a later punch from the listen port. A dial through a relay, or to a peer whose known addresses include a relayed one, keeps the listen port, so the relay sees the port the punch will use. A side effect is that a direct dial opens no mapping on the listen port, which is why AutoNAT does not see a restricted-cone NAT as open (see [detection](#detection)). Direct addresses are tried before relayed ones.

A failed attempt never drops the relayed connection: the peer stays reachable through the relay and the node keeps reporting `relayed`. `GET /nodes/status` lists the most recent attempts, oldest first and bounded (`hole_punches`: peer id, `succeeded`, and an `error` on failure), and `punched_peers`, the peers a hole-punched connection is open to right now. A private node reports `nat_traversed` while `punched_peers` is not empty and falls back to `relayed` or `outbound_only` when the last punched connection closes.

Whether a punch can succeed depends on the NATs. Endpoint-independent mapping (the cone types) usually works; a symmetric NAT that picks a new external port per destination usually does not, and the connection stays relayed. A successful punch shows the other node this node's public address, which the relay already knew.

## Node-to-node requests over libp2p streams

Node-to-node HTTP can ride a libp2p stream instead of a TCP connection to a URL, so relays and hole punching carry it and a peer with no usable URL is still reachable. A stream base URL is `p2p://<libp2p peer id>`. The request and response keep their HTTP shape (method, path and query, headers, body, status); one exchange uses one stream, on a protocol id scoped to the `network_id`, so a node of another network never negotiates it. The server handles the request by dispatching it into the same router the HTTP listener serves, so authentication, validation, and rate limits behave as they do over HTTP.

**When a stream is used.** A peer is addressed by stream when it has a verified libp2p id and either its connectivity is `relayed` or `outbound_only` or its base URL is not a usable http(s) URL. Otherwise its base URL is used. The stream is also used when the entry's base URL is itself `p2p://<id>` (below). Requests can also move between the two transports after a failure; see [transport failover](#transport-failover). The announce loop, relayed trace forwarding, realtime relay, chat replication, and cosign gathering pick the address this way; mirror polling and settlement submission start from the configured http(s) URL and fail over like any other request. Probe and trace choose the address by the same rule, so a peer with no usable URL, or one that is relayed, hole-punched, or outbound-only, is probed and traced over its stream.

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

**Not done yet.** Beyond the failure record in [transport failover](#transport-failover), stream transport is not selected by measured quality or by policy. A peer known only from gossip and confirmed over libp2p is not bound, so the paths above do not address it by stream. WebSocket upgrades and user-facing routes are not carried. Clients and SDKs do not use it.

## Transport failover

A request to a peer that can be reached both ways may move to the other transport. Failover only reorders transports the peer's hint already allows; it never adds a path, relaxes verification, or vouches for anything.

**Outcome record.** For each peer and each transport this node keeps the last success and failure, the number of consecutive failures, and a moving average of the round trip (weight 1/8 on a new sample). The table holds 4096 peers; the least recently touched is dropped past that. A failure to connect demotes the transport for 10 seconds, doubling with each consecutive failure up to 300 seconds; a success clears it. Only failing to connect records a failure: a timeout, a closed stream, an error status, and a local limit do not. Any answer from the peer, whatever its status, counts as the transport working. The record is demote-only: while a transport is demoted and the other is usable and not demoted, the other is tried first; when both are demoted the peer's hint stands. A demotion never moves a request to a stream for `/nodes/relay`, `/nodes/replicate-chat`, or `/mirror/notify`.

**When a request fails over.** Only after a failure to connect, and for reads (GET) also after a timeout. It never fails over on an application answer (a 4xx or 5xx, including 403, is returned as is), on a stream that closed after the request was sent, or, for a write, after a timeout, since the peer may have applied it. A request this node could not queue, such as one with too many requests already waiting on the same peer or no address to dial, is a separate local error: it fails over like a connect failure but never demotes a transport.

**HTTP to stream.** For a peer whose libp2p id is bound to exactly one peer-table entry, when the path is one the [stream route list](#node-to-node-requests-over-libp2p-streams) allows.

**Stream to HTTP.** Only for reads, and only to the http(s) base URL of the one bound entry that holds the peer id. That URL must pass the [outbound address policy](safety-limits.md#outbound-address-policy), and the request is made through the checked client: pinned to the checked address, no redirects, no proxy. Only `Content-Type`, `Accept`, and the trace header are forwarded, and no body is sent; credential headers are dropped, and a query carried on such a read must not be secret. The result of the check, passed or refused, is reused for 30 seconds. An id held by more than one bound entry names no URL, so no failover and no outcome record applies to it. A peer that announces only a `p2p://` URL has no address to fall back to and stays on its stream.

**Waiting for a dial.** A stream request to a peer with no open connection waits behind a dial, at most 32 requests per peer. If no connection is open after `AVALON_NODE_HTTP_CONNECT_TIMEOUT_SECS` (default 15, at most 60) the request counts as never sent and a read can fall back to the peer's URL. A request whose caller already gave up is not delivered when the connection arrives.

Not built: re-selecting a transport by measured quality, a relay flag in announce, bounded probing of alternatives, a fronting gateway, a proof of key possession for binding, and credentials for the write routes.

## Nodes with no public URL

A node with no `AVALON_NODE_URL` (and a libp2p identity) announces itself as `p2p://<its peer id>`. Admission works as follows.

- **Admitted by the stream.** A `p2p://<id>` announce is admitted when it arrives on a libp2p stream whose noise-authenticated peer id equals the id in the URL and in `libp2p_peer_id`. The handshake stands in for the address and reachability checks, since there is no address to fetch. A new entry still counts against the per-source budget and the table cap.
- **Plain HTTP stores nothing.** A `p2p://` announce over HTTP, or over another peer's stream, is answered but nothing in it is stored or gossiped, and a mismatched id is rejected. An announce that went over HTTP therefore also does not feed the coordinate or promote a pooled entry.
- **Gossip.** A self-consistent `p2p://` entry (URL id equal to `libp2p_peer_id`) may enter the unverified pool through gossip. Gossip never overwrites an existing `p2p://` entry; only that peer's own announce changes it. A libp2p contact that authenticates the id promotes and binds a pooled entry, keeping only the id: roles, version, addresses, and connectivity are reset until the peer announces.
- **Not trusted for credential-less routes.** A `p2p://` entry proves only a key pair, so it never counts as bound for `/nodes/relay`, `/nodes/replicate-chat`, and `/mirror/notify` ([above](#node-to-node-requests-over-libp2p-streams)), is never a chat replication or realtime fan-out target whatever roles it reports, and gets no per-peer client address (it shares the common one). Consequence: such a node cannot call those three routes or receive chat and mirror pushes until they carry a credential (#1077).
- **Bounded and evicted first.** The main table holds at most 64 `p2p://` entries, the unverified pool 32, and the shard registry 32 `p2p://` shard URLs (8 unseen per gossip exchange). At a cap a `p2p://` entry is evicted before any HTTP entry, and a `p2p://` newcomer never displaces an HTTP peer.
- **Own URL scope.** A node's own `p2p://` URL is used for announce, topology, and trace only; it is never handed to browsers, signed grants, or interest claims and registration. Features that need the node's own http(s) URL, such as cross-node login, are unavailable to it.
- **Bootstrap.** A node reachable only by `p2p://` still needs one HTTP-reachable seed: it announces to a peer by stream once it knows that peer's libp2p id, and until then (or when the stream fails) over the peer's URL, where the announce is answered but admits nothing, which is how it learns the peer's id and addresses.

## Planned and unbuilt

- Credentials for the three write routes (`/nodes/relay`, `/nodes/replicate-chat`, `/mirror/notify`), so a node announced only as `p2p://<peer id>` can call them and receive chat and mirror pushes (#1077).
- A fronting gateway for nodes that cannot be reached.
- Replacing held relay reservations when a better relay appears, probing relays before choosing, and a flag in announce that marks a node as a relay.
- Re-selecting a transport by measured quality, bounded probing of the alternative, and a proof of key possession for peer-id binding.

## Implementation

Status: Partially implemented, as above. Detection, relays, and the status fields are in the [server crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/server) of avalon-protocol, and the connectivity type is in its [protocol crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/protocol). Lab procedures for testing NAT behavior are in the [avalon-protocol docs](https://github.com/avalon-initiative/avalon-protocol/tree/main/docs).

## Related

- [Nodes](README.md)
- [Discovery and peering](discovery-and-peering.md)
- [Topology and tracing](topology-and-tracing.md)
- [ADR 0903](../decisions/0903-node-participation-must-not-depend-on-public-reachability-nat.md)
