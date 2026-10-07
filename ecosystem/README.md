# Ecosystem

**Status:** Implemented — describes the repositories as they exist; each page labels planned parts.

Avalon is several repositories with a strict dependency direction. This page shows how they relate; each linked page says what a project is, how it fits, its status, and where its own documentation lives. Project repositories answer how to build, run, and contribute to that project. This repository answers what Avalon is and how the parts fit together.

## Dependency map

```text
                     avalon-protocol
       (protocol, node server, signed log, indexer, CLI,
        OpenAPI, conformance vectors)  ── source of truth
                          │
                          ▼
                     avalon-sdks
        (Rust, C#, TypeScript; one version, one release;
         generated from the server's OpenAPI)
                          │
        ┌─────────────────┼───────────────────────┐
        ▼                 ▼                       ▼
   avalon-hub     avalon-topology-visualizer   integrators
 (web, desktop,   (network observability)      (games, apps, services)
   mobile)
        │                 │
        └───── avalon-common-ui (shared Vue components) ─────┘

   avalon-bot: Discord to GitHub today; no dependency on the rest yet
   avalon-docs: this repository
```

The crate-level view, including where the contracts originate, is in [architecture as built](../architecture/as-built.md).

Rules that follow from the direction:

- A change flows downward: protocol, then SDKs, then clients and integrators. Nothing flows back up except a request for a contract change.
- The repository that implements a capability owns it. If a consumer needs something the protocol lacks, the protocol changes first; consumers do not carry workarounds.
- Contracts (signing bytes, tree-head format, trust anchors, OpenAPI) change in the protocol repository and the SDK conformance vectors together, then consumers follow.
- All three SDKs share one version and one release.

## Projects

| Project | What it is | Status | Page |
| --- | --- | --- | --- |
| avalon-protocol | Protocol, node server, signed log, indexer, CLI, docs source of truth | Implemented | [Protocol](protocol.md) |
| avalon-sdks | Rust, C#, and TypeScript client SDKs | Implemented | [SDKs](sdks.md) |
| avalon-hub | Web app and desktop/mobile app for a person's identity and social data | Web: Implemented; app: Partially implemented | [Hub](hub.md) |
| avalon-common-ui | Shared Vue component library | Implemented | [Common UI](common-ui.md) |
| avalon-topology-visualizer | Developer tool that maps and traces the node network | Implemented | [Topology visualizer](topology.md) |
| avalon-bot | Community Discord bot | Implemented for its current scope; Avalon integration is Planned | [Bot](bot.md) |

The organization-wide defaults (contribution guidelines, labels, reusable workflows) live in the [.github repository](https://github.com/avalon-initiative/.github).

## Independent projects

Games and other integrators built on Avalon are independent projects outside this set. An integrator depends on the SDKs and the network, and nothing in the ecosystem depends on any particular integrator. See [integrations](../integrations/README.md).

## Related

- [Architecture](../architecture/README.md)
- [SDK design](../sdk/design.md)
- [Developers](../developers/README.md)
