# Self-Hosting

**Status:** Implemented

Running your own instance of the Avalon code is fully supported. Doing so does not automatically join the Avalon network: it depends on which `network_id` the instance uses. This page separates three things people mean by "self-host" so that the distinction between extending the network and forking it is never fuzzy.

## The three meanings

1. **Mirroring the public network.** An operator runs the server (any combination of settlement, indexer, and gateway) against the same `network_id` as the reference deployment, syncing the same public, verifiable log. This is what "multiple operators" means: more infrastructure serving one network, the Certificate Transparency pattern, not federation ([mirroring](settlement/mirroring.md)). It is read-only with respect to the shared history: a mirror never has write authority over any part of it.
2. **Running as a shard operator.** Settlement authority is sharded per integrator instead of resting with one committer ([sharding](settlement/sharding.md)). A shard operator runs the server with its own shard's settlement signing key under the same `network_id` as every other shard, is cryptographically part of the network through the cross-shard root, and is the real write target for its own shard's events.
3. **Running a private, disconnected instance.** An organization runs the same code rooted under its own `network_id`: a studio piloting Avalon for internal games, an air-gapped environment, or a staging copy that should never touch production data.

Only the third forks the network. The line that matters is not whether an operator runs its own infrastructure (all three do) but whether the deployment shares the network's `network_id` and genesis or roots its own. A mirror and a shard operator share it; a private instance does not.

Mirror and shard operator are not exclusive per node: shard role is per shard, so one server can author one shard and mirror another, with authored and mirrored history kept in separate storage ([nodes](nodes/README.md#a-nodes-three-configuration-axes-are-independent)).

## Shard operator invariants

- **Genesis, not configuration, is the boundary.** A shard operator's stored genesis matches the network's `network_id` exactly. The same boot-time check that makes a fork's history incapable of being mistaken for the public log is what makes a shard operator provably part of the network. No flag turns a shard into a fork or the reverse without changing `network_id`, which is write-once.
- **Write authority is scoped, never network-wide.** A shard operator's key signs heads for its own shard only. It never commits for another shard, and the cross-shard root is computed the same way regardless of which node computes it.
- **A shard is never a fork by omission.** A shard whose operator stops publishing, or that a node cannot reach, appears as a named gap (`partial: true`) in that node's cross-shard root, never as a silent divergence that could be confused with a deliberate fork.
- **A `shard_id` alone proves nothing**, just as `network_id` alone proves nothing. A client verifies that the shard's key is authorized through issuer-key registration ([network trust anchors](../protocol/network-trust-anchors.md)).

An integrator without infrastructure of its own can use a managed host; see [managed shard hosting](self-hosting/managed-shard-hosting.md).

## Why a private instance is safe to offer, and where the line is

Every ledger entry is hashed with its `network_id` folded in ahead of the content, and `network_id` is committed once, at genesis; every later boot refuses to start if the configured value differs. Two consequences follow by construction, not policy:

- A private instance's history is cryptographically incapable of being mistaken for, merged into, or replayed against the public log. The hashes do not collide, the way two Certificate Transparency logs with different tree identities do not.
- There is no accidental path from an internal development deployment to silently being part of the public network. The mismatch fails fast, before the process binds a listener.

So supporting private instances cannot leak into or corrupt the network everyone else relies on, and no migration path quietly blurs the two.

## What a private instance gets and gives up

A private instance is the real thing (identity, guilds, achievements, attestations, the same trust model) for one organization's integrators. It does not get the reason most of this exists:

- Its identities, guilds, and achievements are meaningless outside itself. Nothing on the public network can see or recognize what it issues, and vice versa. The [trust model](../protocol/trust-model.md) still applies, but recognition can only happen among integrators pointed at the same `network_id`.
- None of the cross-integrator discovery, shared communities, or "your friends are already here" effects apply; they come from the network, not the code.
- It is a fork in substance even when zero effort in practice. Nothing merges the two later without a real migration. There is no upgrade path from private to public beyond re-registering integrators and re-issuing attestations on the public network going forward. Whether a private instance's history could ever be selectively re-issued onto the public network is Undecided; it is worth deciding explicitly if an operator actually asks.

Legitimate reasons to run one: local development, CI, and staging (development networks use `avalon-dev-<name>` ids); internal tooling and QA that must never touch real identity data; piloting Avalon internally; regulatory, contractual, or air-gap constraints that make joining any shared network impossible. None of these is the goal of the project. The value described in [why Avalon](../getting-started/why-avalon.md) compounds with the size of the public network, not with the number of private forks.

## Operating an instance

Any instance reachable beyond localhost must run behind TLS termination. A single instance can be stood up from a published container image without a Rust toolchain, and the server binary embeds its database migrations. Log level can be changed at runtime through an admin endpoint gated by a separate admin secret, and topology data can be hidden by an operator who prefers not to publish a neighbor list ([topology](nodes/topology-and-tracing.md#exposure-and-opt-out)). These procedures live in the hosting docs of the implementing repository, not here.

A node does not need to expose a public port to take part. A node with no inbound path can run with no public URL, announce itself by its libp2p peer id, and be reached over the connections it opened or through a relay; this has been verified end to end in the protocol repository's NAT lab for admission, listing, probe and trace, mirroring, and remote settlement submission. It has limits: the node still needs one reachable seed for first contact, it cannot serve clients directly, and it cannot call or receive the credential-less write routes (chat and mirror pushes), so it falls back to polling. Two nodes that both have no open port reaching each other has not been exercised. The protocol repository's [Running a node with no open port](https://github.com/avalon-initiative/avalon-protocol/blob/main/docs/projects/backend-server/for-hosters/running-without-an-open-port.md) guide has the setup and what is checked. The mechanics are in [connectivity](nodes/connectivity.md#nodes-with-no-public-url).

## Implementation

Status: Implemented. Genesis commit-and-check, `network_id` hashing into every entry and head, and the required `network_id` setting are in the [settlement crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/chain) and [server crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/server) of avalon-protocol. Hosting quickstarts, deployment, upgrade, and key-rotation procedures are in the protocol repository's [docs](https://github.com/avalon-initiative/avalon-protocol/tree/main/docs). For the concept-level view, see [running a node](../developers/running-a-node.md). There is one reference deployment target today (`avalon-mainnet-1`), and no tooling assumes several `network_id`s in one process: a private instance is a wholly separate deployment, not a mode flag.

## Related

- [Nodes](nodes/README.md)
- [Mirroring](settlement/mirroring.md), [sharding](settlement/sharding.md)
- [Managed shard hosting](self-hosting/managed-shard-hosting.md)
- [Network trust anchors](../protocol/network-trust-anchors.md)
- [Running a node](../developers/running-a-node.md)
