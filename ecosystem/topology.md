# avalon-topology-visualizer

**Status:** Implemented — the v1 scope (network walk, latency layout, probe, viewer measurement, and packet-path trace) is in place.

The topology visualizer is a developer-facing, read-only app that maps the live network of Avalon nodes and how they connect. It walks the network outward from a seed node, merges each node's partial view into one graph, and lays it out by measured round-trip time, so distance on screen means response time rather than geography.

## How it fits

It is a standalone client that consumes the [SDKs](sdks.md) for the node topology, probe, and trace routes, and shares its look with the Hub through [common UI](common-ui.md). It talks to no central service, because the network has none by design. It uses only the public topology routes a node serves (which an operator can turn off) and works inside a private network with no third-party runtime dependency. Hop and latency data are self-reported by the nodes on a path and are advisory, not verified. It supports the observability side of [distributed topology](../architecture/distributed-topology.md).

## What it shows

- The node graph, laid out by measured latency, with node shape by role and links marked for mirroring.
- On-demand probes between two nodes, and measurements from the viewer's own browser.
- The path a real request took across nodes (packet trace).

## Where to read more

- [avalon-topology-visualizer repository](https://github.com/avalon-initiative/avalon-topology-visualizer) for setup, controls, and hosting.

## Related

- [Ecosystem map](README.md)
- [Distributed topology](../architecture/distributed-topology.md)
- [Nodes](../architecture/nodes/README.md)
- [SDKs](sdks.md)
