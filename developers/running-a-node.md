# Running a node

**Status:** Implemented — a node can be run today; the network has no public mainnet yet, so nodes join development networks or run standalone.

A node is a running `avalon-server` process backed by Postgres. Anyone can run one, either to join an existing network or as a standalone node for development. This page explains the concepts you need before you start. The step-by-step hosting guides live with the server in the protocol repository.

## Why run a node

Running a node is participation, not a service you depend on someone else for. A node can mirror the public log, serve reads to its own community, and take part in the network's gossip. Independent operators are what keep the network open; see [self-hosting](../architecture/self-hosting.md) and [distributed topology](../architecture/distributed-topology.md).

## Concepts to know first

- **Network.** A node belongs to one `network_id`, whose signing key is pinned in the trust-anchor list. Running the code under your own `network_id` is supported but is a fork, cryptographically incapable of merging into another network's log later. Mirroring the same public log is supported and encouraged. See [network trust anchors](../protocol/network-trust-anchors.md).
- **Three independent choices.** A node picks its capability roles (settlement, indexer, realtime, gateway, or all combined), its shard role (author a shard, or mirror one), and its retention tier (full archive or a bounded window). See [nodes](../architecture/nodes/README.md).
- **Replica by default.** A node that only mirrors and serves reads needs no signing authority and no login configuration. A node that serves passkey logins needs a WebAuthn relying-party id and origin.
- **Keys are generated on first start.** The node creates its settlement, submit, witness, and network identity keys in its data directory and reuses them. Keys set explicitly through the environment always win.
- **Seed nodes.** A fresh node learns a network through the seed nodes listed in that network's trust entry, mirrors the core shard from them, and verifies every head against the pinned key. A seed carries no authority: it can withhold history but cannot inject any.
- **TLS.** A node reachable beyond loopback must sit behind TLS, typically a reverse proxy.
- **Reachability.** Participation should not depend on public reachability. See [ADR 0903](../architecture/decisions/0903-node-participation-must-not-depend-on-public-reachability-nat.md) for the decision and the state of the work. A node with no open port can join today with limits; see [self-hosting](../architecture/self-hosting.md#operating-an-instance) and the protocol repository's guide, *Running a node with no open port*.

## Ways to run one

| Route | Needs | Notes |
| --- | --- | --- |
| Standalone binary | A Postgres database you provide | Guided first run with `avalon setup`, also non-interactive; a variant that bundles its own database exists. |
| Docker | Docker | One command for a single node bound to loopback with safe defaults. |
| From source | A Rust toolchain | For contributors. |

Release binaries have provenance you can verify before running them.

## Where the step-by-step guides are

The hosting guides (standalone binary, Docker quickstart, deployment behind TLS, upgrading and rollback, choosing a shard, seed nodes, and release verification) live in the [avalon-protocol repository](https://github.com/avalon-initiative/avalon-protocol#readme). The same guides are embedded in the `avalon` binary: run `avalon guide` to list topics, and `avalon setup` for the guided first run.

## Related

- [Self-hosting](../architecture/self-hosting.md)
- [Nodes](../architecture/nodes/README.md)
- [Disaster recovery](../architecture/disaster-recovery.md)
- [Network trust anchors](../protocol/network-trust-anchors.md)
- [Developers](README.md)
