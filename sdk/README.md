# SDKs

**Status:** Implemented — Rust, C#, and TypeScript SDKs exist and are released together; more languages are not planned.

An SDK is the client library an integrator (a game, app, or service) uses to talk to an Avalon network. It handles network calls, cryptographic signing, retries, and capability checks, so the developer works with identity, guilds, achievements, and presence rather than with nodes, databases, or wire formats. This section explains how the SDKs relate to the protocol; per-language install and usage documentation lives in the SDK repository.

## How the SDKs relate to the protocol

```text
avalon-protocol (server)                     avalon-sdks
  OpenAPI: docs/generated/openapi.json  ───►  vendored copy ──► generated wire types (Rust, C#, TypeScript)
  conformance/vectors/                  ───►  vendored copy ──► each SDK's conformance runner
                                              hand-written: client layer, signing, retries, sessions
```

- The **protocol repository owns every contract**. The server publishes an OpenAPI document and a set of conformance vectors (canonical signing bytes and signatures).
- Each SDK **generates its wire types** from that OpenAPI document and **hand-writes** the client layer: sessions, signing, retry, discovery, verification.
- Because signing logic cannot be expressed as a schema, **conformance vectors** keep client and server byte-identical. A format change that is not mirrored everywhere fails a test on whichever side moved.
- A route-coverage check fails when any SDK never calls a route the server exposes. All three SDKs currently cover the published API.
- **All three SDKs share one version and ship in one release.** A single SDK is never released on its own.
- The SDKs do not depend on the protocol repository's crates. Third-party network implementations and non-Rust SDKs need only the wire protocol.

If an integrator needs something the wire API does not offer, the protocol changes first and the SDKs follow; an SDK never carries a workaround for a missing protocol capability.

## Pages

| Page | What it covers |
| --- | --- |
| [Design](design.md) | Language-agnostic design: capabilities not infrastructure, two session types, verification, errors and retries, codegen, conformance. |
| [Language support](language-support.md) | Which languages have an SDK, and which do not. |

## Where the per-language documentation lives

| Language | Package | Documentation |
| --- | --- | --- |
| Rust | `avalon-sdk` (git dependency or release `.crate` files; not on crates.io) | [languages/rust](https://github.com/avalon-initiative/avalon-sdks/tree/main/languages/rust) |
| C# | `Avalon.Sdk` (GitHub Packages NuGet feed; targets netstandard2.1 for Unity) | [languages/csharp](https://github.com/avalon-initiative/avalon-sdks/tree/main/languages/csharp) |
| TypeScript | `@avalon-initiative/protocol-sdk` (GitHub Packages npm) | [languages/typescript](https://github.com/avalon-initiative/avalon-sdks/tree/main/languages/typescript) |

Installation, release procedure, and per-language method lists are in the [avalon-sdks README](https://github.com/avalon-initiative/avalon-sdks#readme). For the language-agnostic flow of building an integration, see [building an integration](../integrations/building-an-integration.md).

## Related

- [Design](design.md)
- [Language support](language-support.md)
- [Integrations](../integrations/README.md)
- [Ecosystem: SDKs](../ecosystem/sdks.md)
- [Protocol API](../protocol/api.md)
