# Nodes

**Status:** Implemented — a fronting gateway, relay probing, and a relay flag in announce are Planned (see connectivity)

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
- A node cannot push data into another node anonymously. The routes nodes use to push live events, chat copies, and mirror notifications require the sender's node identity key and a known peer table entry, and each route limits what that sender may do ([node-to-node write routes](write-route-credentials.md)).
- Operator actions that do exist, such as suspending an issuer at the network level, are explicit, audited protocol events with their own trail, never silent edits. The [security model](../../protocol/security-model.md) has the full authority map.

What a node can do is the ordinary work of infrastructure: accept, validate, order, store, index, serve, and mirror.

## Mirrors, not federation

Multiple operators is a goal, achieved by mirroring one public, verifiable log rather than by federation. See [mirroring](../settlement/mirroring.md). Sharded settlement authority is the complementary answer to one operator holding sole write authority; see [sharding](../settlement/sharding.md).

## Identity and social actions and shards

**Status:** Partially implemented. An identity is not tied to one node's operations, but whether an account is usable from another node depends on which shard its identity events were written to and whether the other node projects that shard.

**Where events land.** The outbox labels identity, social, and guild events `core`. A node with a remote `core` authority configured submits them there; every other node commits them to its own ledger, so they land in the shard that node authors. A node that generates its own settlement key at first boot, with no shard id and no remote authority configured, authors a self-certifying `node:<hash>` shard, so on a default fresh node the identity events of a new account (`identity.created`, the passkey event, and the inception `identity.signing_key_added`) go to that node's own `node:` shard and not to `core`. Only the core authority itself, or a node with a remote `core` authority, writes identity events into `core`. A named shard (`game:<slug>`) likewise holds the identity events of the accounts registered through the node that authors it.

**Which other nodes can see the account.** A node that authors no `core` mirrors the `core` shard of the network's seed nodes by default and projects what it mirrors. It mirrors other shards only when named in `AVALON_MIRROR_PEERS` or, with `AVALON_MIRROR_ALL_DISCOVERED_SHARDS` (off by default), discovered through gossip. Entries of a `node:` shard are never projected into a node's identity tables, however they were mirrored, so the account of a default fresh node does not exist on other nodes (see [sharding](../settlement/sharding.md#automatic-shard-discovery)). A named shard that the destination mirrors is projected.

| Where the account's identity events are | Visible on another node, and cross-node login with the device-held signing key |
| --- | --- |
| `core` | Yes, on every node that mirrors and projects `core` (the default for a node that authors none). |
| A named shard the other node mirrors | Yes, on a node that mirrors and projects that shard. |
| A `node:` shard (the default fresh node) | No. Not projected on other nodes, so the account is not visible there and the login grant cannot verify. |

**Cross-node login** finds the identity's signing key in the destination's own projected tables, and otherwise fetches it from the `core` shard only ([cross-node login](cross-node-login.md)), and **passkey login** reads credentials from the node's own table, so a passkey works only on the node that holds the credential. The signed, human-approved login grant uses the device-held signing key, not the passkey. An account whose events are only in a `node:` shard therefore has no key the destination can find, cannot log in on another node, and does not survive its registering node being decommissioned.

**After the registering node disappears.** Another node that had mirrored the shard keeps the raw mirrored entries, but nothing projects them, so the account is not recoverable from them. A session already held on a node that disappears can be continued elsewhere only on a node that has projected the identity's signing key, which has the same dependency.

Planned: any node accepts and projects verified identity events from any shard it mirrors, with per-source caps, and cross-node login resolves the identity's entries from the shard they live in, as decided in [ADR 1177](../decisions/1177-an-account-stays-usable-anywhere-when-its-registering-node-goes-away.md). The work is tracked in [avalon-protocol#1178](https://github.com/avalon-initiative/avalon-protocol/issues/1178), and none of it is built.

The real, narrower failure that remains for integrators is a specific integrator's own settlement shard going down. That pauses that integrator's new issuances, a contained per-integrator blast radius, and it never stops an identity from acting elsewhere. Separately, none of this helps if a shard's data was never copied anywhere; the minimum-replication gate for new registrations addresses that ([retention and growth](../settlement/retention-and-growth.md)), and extending the guarantee further remains an open question.

A pure mirror that has not yet backfilled a shard answers a "nothing here yet" 404 that says so: the body marks the node as a mirror and names the peer to ask, so it is distinguishable from a genuinely empty authority.

## Pages in this section

| Page | Covers |
| --- | --- |
| [Roles and extraction](roles-and-extraction.md) | The role gate, backing-service discovery, extracting indexer, realtime, and settlement, replica-only mode, first-boot keys |
| [Discovery and peering](discovery-and-peering.md) | How SDKs and nodes find nodes, the peer table and its bounds, latency and coordinates, DHT use, push sync |
| [Connectivity](connectivity.md) | Direct, NAT-traversed, relayed, and outbound-only nodes; detection; relays, how a relay is selected and re-selected, and how a serving relay is kept up; hole punching; node-to-node requests over libp2p streams and failover between HTTP and streams |
| [Topology and tracing](topology-and-tracing.md) | The per-node topology view with connectivity and latency path, probe, trace, operation tracing, overlay routing |
| [Node-to-node write routes](write-route-credentials.md) | The credential on relay, chat replication, and mirror notify, standing, replay protection, refusal codes, the per-route scope checks, and known residuals |
| [Safety limits](safety-limits.md) | Outbound address policy, rate and concurrency limits, request bounds, relay, stream, and failover limits, public read CORS |
| [Version rollout](version-rollout.md) | Permanent version skew, the three version axes, minimum-version floor |
| [Cross-node login](cross-node-login.md) | Logging an identity into a node it never registered on |

## Open questions

Capability negotiation and role-aware node selection on the SDK side (SDKs pick a verified server; they do not route individual calls by role); TLS requirements before any non-local deployment (hosting guidance requires TLS termination beyond localhost); a formal export format for the log; release signing, which gates opt-in auto-update for self-hosted nodes.

## Related

- [Overview](../overview.md)
- [Settlement](../settlement.md), [distributed topology](../distributed-topology.md), [self-hosting](../self-hosting.md)
- [Protocol security model](../../protocol/security-model.md)
- [ADR 0672](../decisions/0672-realtime-websocket-extraction-proxies-through-gateway-not-direct-connect.md), [ADR 0903](../decisions/0903-node-participation-must-not-depend-on-public-reachability-nat.md)
