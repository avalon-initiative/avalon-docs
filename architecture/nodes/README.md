# Nodes

**Status:** Implemented — admitting nodes with no reachable URL, relay selection, and transport selection are Planned (see connectivity)

An Avalon node is infrastructure that transports, indexes, settles, and serves protocol data. Nodes are infrastructure providers, not authorities: a node cannot fabricate an issuer's claim or replace an actor's signature, and node capabilities are roles an operator chooses to run, not mandatory separate binaries.

This page defines the node model and its authority limits. The mechanics are split across focused pages listed at the end.

## Capabilities

```text
Settlement   validates and stores durable history (the log)
Indexer      consumes history, serves query projections
Realtime     presence and ephemeral connections
Gateway/API  the SDK and API surface integrators and clients talk to
```

An operator may run all four in one process, only Indexer plus Gateway, only Settlement, or any other combination. The three verticals in the [overview](../overview.md) map onto these roles; keeping the verticals distinct is what makes this specialization possible without a rewrite.

| Node type | Runs | Typical operator |
| --- | --- | --- |
| Settlement / full | the log, verification, mirror sync | a mirror operator, the reference deployment |
| Indexer | projections, registry, historical queries | a hosting provider serving reads |
| Realtime | presence, heartbeat, ephemeral channels | a regional presence service |
| Gateway / API | SDK endpoints, auth, routing | anyone fronting the others |
| Combined | any subset, including all | the default: one server process |

The role list is a genuine startup-mode gate, not advisory metadata. See [roles and extraction](roles-and-extraction.md).

## A node's three configuration axes are independent

These are three separate questions, and a node's answer to one says nothing about the others.

| Axis | Question | Values |
| --- | --- | --- |
| Capability | What services does this process run? | Settlement, Indexer, Realtime, Gateway, or Combined |
| Shard role (per shard) | Does this node hold the signing key and author this shard's writes, or only watch and verify another node's? | Authority, or Mirror |
| Retention tier | How much local history does this node keep? | Full (archive), or Hot (recent window) |

Shard role is per shard, not per node: one node can be the authority for one shard and a mirror of a different one, since authored history and mirrored history are stored separately by construction. A fourth, unrelated property is [connectivity](connectivity.md): how peers reach the node. It never changes any of the three axes. See [shards and authority](../settlement/sharding.md), [retention](../settlement/retention-and-growth.md), and [self-hosting](../self-hosting.md).

## Node authority

A hosted node is not protocol authority. The concrete guarantees:

- A node cannot fabricate "integrator A issued this achievement". Attestations are signed by A's registered issuer key ([issuers](../../protocol/issuers.md)); a node that stores an unsigned or wrongly signed claim has stored something every verifier rejects.
- A node cannot replace a signature, alter a settled entry, or drop one without detection. The log is hash-chained, signed, and mirrorable.
- A node cannot act as an identity. Identity mutations are authorized by the identity's own key ([identity](../../protocol/identity.md)).
- Operator actions that do exist, such as suspending an issuer at the network level, are explicit, audited protocol events with their own trail, never silent edits. The [security model](../../protocol/security-model.md) has the full authority map.

What a node can do is the ordinary work of infrastructure: accept, validate, order, store, index, serve, and mirror.

## Mirrors, not federation

Multiple operators is a goal, achieved by mirroring one public, verifiable log rather than by federation. See [mirroring](../settlement/mirroring.md). Sharded settlement authority is the complementary answer to one operator holding sole write authority; see [sharding](../settlement/sharding.md).

## Identity and social actions are not shard-locked

An identity has no home node in any ongoing operational sense. Which shard a new event commits into is a property of whichever node handles the request, never of the identity acting through it; no path requires an identity's actions to route back through the shard where its `identity.created` event landed. "Home" is a historical fact (where that first event was committed, and then replicated), not a place an identity depends on reaching.

A person can authenticate through any live node ([cross-node login](cross-node-login.md)), and their friend, guild, and profile actions commit into that node's shard. If the node they were using disappears mid-session, reconnecting through another live node and continuing is the same reconnect-elsewhere pattern used for realtime chat.

The real, narrower failure that remains is a specific integrator's own settlement shard going down. That pauses that integrator's new issuances, a contained per-integrator blast radius, and it never stops an identity from acting elsewhere. Separately, none of this helps if a shard's data was never copied anywhere; the minimum-replication gate for new registrations addresses that ([retention and growth](../settlement/retention-and-growth.md)), and extending the guarantee further remains an open question.

A pure mirror that has not yet backfilled a shard answers a "nothing here yet" 404 that says so: the body marks the node as a mirror and names the peer to ask, so it is distinguishable from a genuinely empty authority.

## Pages in this section

| Page | Covers |
| --- | --- |
| [Roles and extraction](roles-and-extraction.md) | The role gate, backing-service discovery, extracting indexer, realtime, and settlement, replica-only mode, first-boot keys |
| [Discovery and peering](discovery-and-peering.md) | How SDKs and nodes find nodes, the peer table and its bounds, latency and coordinates, DHT use, push sync |
| [Connectivity](connectivity.md) | Direct, NAT-traversed, relayed, and outbound-only nodes; detection; relays; hole punching; node-to-node requests over libp2p streams |
| [Topology and tracing](topology-and-tracing.md) | The per-node topology view with connectivity and latency path, probe, trace, operation tracing, overlay routing |
| [Safety limits](safety-limits.md) | Outbound address policy, rate and concurrency limits, request bounds, relay and stream limits, public read CORS |
| [Version rollout](version-rollout.md) | Permanent version skew, the three version axes, minimum-version floor |
| [Cross-node login](cross-node-login.md) | Logging an identity into a node it never registered on |

## Open questions

Capability negotiation and role-aware node selection on the SDK side (SDKs pick a verified server; they do not route individual calls by role); TLS requirements before any non-local deployment (hosting guidance requires TLS termination beyond localhost); a formal export format for the log; release signing, which gates opt-in auto-update for self-hosted nodes.

## Related

- [Overview](../overview.md)
- [Settlement](../settlement.md), [distributed topology](../distributed-topology.md), [self-hosting](../self-hosting.md)
- [Protocol security model](../../protocol/security-model.md)
- [ADR 0672](../decisions/0672-realtime-websocket-extraction-proxies-through-gateway-not-direct-connect.md), [ADR 0903](../decisions/0903-node-participation-must-not-depend-on-public-reachability-nat.md)
