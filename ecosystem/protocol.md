# avalon-protocol

**Status:** Implemented — the reference implementation of the protocol and the node server; some architecture areas are Partially implemented and labeled as such in [architecture](../architecture/README.md).

`avalon-protocol` is the source of truth for every Avalon contract: the protocol's domain rules, the node server, the signed transparency log, the query indexer, the developer CLI, the published OpenAPI document, and the conformance vectors. Everything else in the ecosystem consumes what it defines.

## What it contains

| Area | Purpose |
| --- | --- |
| `crates/protocol` | Pure domain types and traits: identity, guilds, achievements, events, signing and tree-head verification. No I/O. |
| `crates/chain` | The settlement ledger implementation behind the transparency log. It is a signed, append-only log, not a blockchain. |
| `crates/indexer` | The fast-read query layer, rebuildable from durable protocol events. |
| `crates/server` | `avalon-server`, the network-facing API and node that every client talks to. |
| `crates/cli` | The `avalon` developer and operations CLI, including first-run setup. |
| `docs/generated/openapi.json` | The published wire contract that the SDKs are generated from. |
| `conformance/vectors/` | Canonical signing-byte and signature vectors asserted by the server and every SDK. |
| `docs/trusted-networks.json` | The trust-anchor list pinning each known network to its settlement key. |

## How it fits

It is the top of the dependency chain. The [SDKs](sdks.md) are generated from its OpenAPI and checked against its vectors. The [Hub](hub.md) and the [topology visualizer](topology.md) reach it only through the SDKs. Integrators reach it through the SDKs or the wire API directly. Nodes run by other operators are ordinary participants in the same network ([running a node](../developers/running-a-node.md)).

## Where to read more

- Concepts and rules: [protocol](../protocol/README.md) and [architecture](../architecture/README.md) in this repository.
- Wire API and conformance: [protocol API](../protocol/api.md).
- Building, running, and contributing to the server: the [avalon-protocol repository](https://github.com/avalon-initiative/avalon-protocol).

## Related

- [Ecosystem map](README.md)
- [SDKs](sdks.md)
- [Protocol concept map](../protocol/README.md)
