# avalon-sdks

**Status:** Implemented — Rust, C#, and TypeScript SDKs are released together (latest release v0.1.4 at time of writing).

`avalon-sdks` holds the official client SDKs, one directory per language under `languages/`. They are how integrators and first-party clients talk to an Avalon network without handling wire formats, signing, or retries themselves.

## How it fits

The SDKs sit directly below the protocol. Wire types are generated from the server's OpenAPI document (vendored into this repository), and the hand-written signing logic is held to the protocol's conformance vectors. The Hub, the topology visualizer, and every integrator build on them. See [SDK design](../sdk/design.md) and [language support](../sdk/language-support.md).

## Key facts

- **One version, one release.** All three SDKs share a version and ship from a single tag. Individual SDKs are never released alone.
- **Distribution.** The TypeScript package (`@avalon-initiative/protocol-sdk`) and the C# package (`Avalon.Sdk`) are published to GitHub Packages, which needs a token with `read:packages` even for public packages. The Rust SDK is not on a registry: it is used as a git dependency on a release tag or from `.crate` files attached to the release. Publishing to crates.io is a later, deliberate step.
- **Trust anchors.** SDKs fetch the protocol's published trust-anchor list at runtime and fail rather than fall back to a stale copy.
- **Extras beyond the core client.** Node topology reads, probe and trace, self-certifying shard-head verification, witness-cosigned head verification, and shard-name resolution are available in all three.

## Where to read more

- Repository, install steps, and release procedure: [avalon-sdks](https://github.com/avalon-initiative/avalon-sdks#readme).
- Per-language guides: [Rust](https://github.com/avalon-initiative/avalon-sdks/tree/main/languages/rust), [C#](https://github.com/avalon-initiative/avalon-sdks/tree/main/languages/csharp), [TypeScript](https://github.com/avalon-initiative/avalon-sdks/tree/main/languages/typescript).

## Related

- [Ecosystem map](README.md)
- [SDKs overview](../sdk/README.md)
- [Building an integration](../integrations/building-an-integration.md)
