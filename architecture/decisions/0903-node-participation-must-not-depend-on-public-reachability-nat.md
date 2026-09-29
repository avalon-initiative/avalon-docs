# ADR-0903: node participation must not depend on public reachability (NAT-aware connectivity)

**Status:** Accepted — decided 2026-09-25

Original record: [avalon-protocol#903](https://github.com/avalon-initiative/avalon-protocol/issues/903). The text below is preserved as recorded; `#N` references are avalon-protocol issue numbers and file paths are as they were when the decision was made.

## Context

Nodes talk to each other over HTTP to each node's advertised address (`AVALON_NODE_URL`), plus TCP for the libp2p DHT. The node's libp2p build enables only `tcp`, `noise`, `yamux`, `kad` and `identify`: there is no AutoNAT, circuit relay or DCUtR hole punching, and the docs do not describe behavior behind NAT. Several paths bypass libp2p entirely (announce, relay fan-out, mirror polling, probe, trace, remote settlement submit), so a node with no stable, publicly reachable address is effectively a client of the network today: it can call out, but other nodes cannot call into it.

With AutoNAT, circuit relay and DCUtR, a NAT-bound node can often be reached directly after a hole punch, and can otherwise be reached through a relay or a persistent outbound connection. The open question was whether to build that or to require every operator to expose a port (port forward, VPN, reverse proxy or tunnel).

## Decision

Node participation does not depend on a publicly reachable address or on operator-side port forwarding, VPNs, reverse proxies or tunnels. Avalon is self-hostable without requiring every operator to expose a public port.

- **Reachability is a connectivity capability**, not a prerequisite for participation and not a measure of authority. A node behind NAT is a full Avalon node. Connectivity, authority, capabilities, services and trust stay separate concepts; a publicly reachable node is not more authoritative than an outbound-only one.
- **Connectivity states:** direct, NAT-traversed (hole-punched), relayed, outbound-only. Selection prefers them in that order, automatically.
- **The full set ships:** AutoNAT reachability detection, circuit relay (client and server roles), DCUtR hole punching, relay fallback and outbound-only operation. The HTTP-based node-to-node paths get a transport that works for nodes that cannot be dialed. The work is ordered, not reduced: the epic is complete only when all of it is delivered.
- **Not federation:** relays and traversal are transport. They never create separate networks, authorities or state domains; every node and relay provider participates in the same canonical network.
- **Scope:** node and server side. The SDKs and other downstream consumers are expected to be unaffected, because connecting stays a matter of `connect()`; that expectation is verified as part of the work, not assumed.
- **Sequencing:** tracked as an epic and scheduled after the topology visualizer work; not needed immediately.

The earlier options "keep the current model and document the requirement" and "outbound-only mode alone" are rejected as end states; outbound-only remains one of the connectivity states.

## Consequences

Relays and hole punching add libp2p dependencies, relay capacity that reachable nodes contribute, and an abuse surface (reservation limits, bandwidth and duration caps, identity binding) that has to be designed rather than bolted on. Announce and address semantics, `/nodes/probe` and `/nodes/trace` semantics, the topology read model and the peer-table address validation all have to account for relayed and outbound-only nodes. The work is tracked in the epic linked below.

## Related

Node topology and probe/trace work (#512, #875, #877, #878), peer table bounds and address validation (#882, #898), gossip verification (#897), the DHT epic (#580), node roles (#291), and the settlement-is-not-federation ADR (#70).
