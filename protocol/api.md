# API Specification

**Status:** Partially implemented — the SDK-facing API is specified by a generated OpenAPI document; the node, ledger, and mirror routes have no machine-readable specification.

The Avalon wire API is specified in two different ways depending on who calls it. The SDK-facing API (identity, social, guilds, integrators, attestations, registry) is described by a generated OpenAPI document that the SDKs are generated from. Node-to-node and ledger routes are specified only by their handler code and by the architecture pages, plus a set of conformance vectors for the client-side behavior that generated code cannot express. This page says where each thing is defined. It links to the protocol repository and does not restate the routes.

## The SDK-facing API: OpenAPI

The source of truth is [`docs/generated/openapi.json`](https://github.com/avalon-initiative/avalon-protocol/blob/main/docs/generated/openapi.json) in `avalon-protocol`, titled "Avalon Protocol API" and versioned with semver (0.11.0 at the time of writing). Its scope, in its own words, is identity and auth, profile and presence, social graph, chat, devices, passkeys and recovery, guilds, and the integrator, achievements, and registry surface, about 134 paths. Identity ids appear in it as strings matching `^[0-9a-f]{64}$`, and `POST /identities/register/start` requires `identity_id`, `event_signing_public_key`, and `display_name`; see [the identity id](./identity.md#the-identity-id).

- **Generated, not hand-written.** The document is produced from annotations on the real handler signatures and types by `make openapi`. `make openapi-check` fails CI if the file is stale relative to the annotations, and `make openapi-version-check` fails CI if the schema's shape changed relative to `main` without a version bump. Each SDK embeds the schema version it targets.
- **Contract flow.** A change to this API updates the protocol repository first, then the SDK conformance vectors, then consumers. SDKs are generated from the same document and share one version; see [SDK design](../sdk/design.md) and [ecosystem: SDKs](../ecosystem/sdks.md).
- **Known gaps.** The document deliberately omits node-to-node, ledger, and internal routes. Some of those, such as tree-head reads and node discovery, are called by the SDKs with hand-written code pinned by conformance vectors, so they have no generated types and no route-coverage check. It also does not yet cover every public route: for example `GET /registry/{slug}` is served by nodes (with the registry data also available at `GET /integrations/{slug}/registry`, which is documented). An automated route-table-versus-schema coverage check is tracked separately in the protocol repository.

## Node, ledger, and mirror routes

The following route families are intentionally outside the OpenAPI document, and mostly have no machine-readable spec:

| Family | What it does | Where it is specified |
| --- | --- | --- |
| `/ledger/*` (`sth/latest`, `sth/{tree_size}`, `proof/inclusion`, `proof/consistency`, `entries`, `submit`, `prepare-batch`, `finalize-batch`, `cross-shard-root`, `mirror-progress`) | the signed transparency log: tree heads, proofs, entries, batch submission | the route table in [`crates/server/src/lib.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/lib.rs) and the handlers in [`settlement.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/settlement.rs); behavior described in [settlement](../architecture/settlement.md) and [mirroring](../architecture/settlement/mirroring.md) |
| `/nodes/*` (`announce`, `peers`, `status`, `discover`, `relay`, `replicate-chat`, `log-level`), `/mirror/notify` | node discovery, gossip, presence relay, chat replication, operator controls; `relay`, `replicate-chat`, and `/mirror/notify` require a node credential even though they are outside the OpenAPI document | [`nodes.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/nodes.rs) and the route table; behavior in [nodes](../architecture/nodes/README.md), [write route credentials](../architecture/nodes/write-route-credentials.md), and [discovery and peering](../architecture/nodes/discovery-and-peering.md) |
| `/nodes/topology`, `/nodes/probe`, `/nodes/trace` | topology, latency probes, packet tracing for client apps | **in** the OpenAPI document (an explicit exception, because client apps call them); see [topology and tracing](../architecture/nodes/topology-and-tracing.md) |
| `/shards/*` (name claims) | domain-proven shard names | **in** the OpenAPI document; see [shard identity and names](./network-trust-anchors/shard-identity-and-names.md) |
| `/internal/*` | indexer apply and rebuild, internal to a node | code only; not a public contract |

The two `/ledger/sth/*` routes, `proof/*`, and `entries` are consumed by SDK network verification and mirroring, so their client-visible shapes are pinned by conformance vectors rather than by OpenAPI: see below. Cosignatures are returned alongside an STH with `?witnesses=1`; the default response body is unchanged.

## Conformance vectors

Generated code covers wire shapes. Client-side behavior that must be identical in every language (signing bytes, tree-head verification, cosigned-head acceptance, known-list selection) is fixed by shared JSON vectors.

- The protocol repository holds the canonical set in [`conformance/vectors`](https://github.com/avalon-initiative/avalon-protocol/tree/main/conformance/vectors), with the format described in its `SCHEMA.md`. It includes vectors the server itself is tested against: `attestation-signing.json`, `signed-tree-head.json`, `witness-cosigned-tree-head.json`, `known-list-selection.json`, `witness-announce.json`, `self-certifying-tree-head.json`, `cross-node-login.json`, `session-continuation.json`, `bip39-mnemonic.json`, `websocket-interest-claim.json`, `identity-chain.json`, and the identity-id set: `identity-id.json`, `identity-created-signing.json`, `device-grant-approval.json`, and `signing-key-revoked.json`.
- The SDK repository holds vendored copies in [`conformance/vectors`](https://github.com/avalon-initiative/avalon-sdks/tree/main/conformance/vectors), run by a thin test runner in each language, plus wire fixtures for the topology routes in [`conformance/fixtures/nodes`](https://github.com/avalon-initiative/avalon-sdks/tree/main/conformance/fixtures/nodes).
- Each vector file declares `supportedIn` and `notSupported`, so a language that lacks a behavior records an explicit, visible skip and never a fabricated pass. As of this writing `session-continuation.json`, `bip39-mnemonic.json`, and `websocket-interest-claim.json` are exercised by the TypeScript SDK only. `identity-chain.json` exists only in the protocol repository, with no SDK copy yet. The four identity-id vector files (`identity-id.json`, `identity-created-signing.json`, `device-grant-approval.json`, `signing-key-revoked.json`) are vendored and run in all three SDKs.
- A contract change to signing bytes, the STH format, trust anchors, or the OpenAPI document updates the protocol repository and the SDK vectors together, then consumers.

## Where to find things

| You want to know | Look at |
| --- | --- |
| the request and response shape of an SDK-facing route | the [OpenAPI document](https://github.com/avalon-initiative/avalon-protocol/blob/main/docs/generated/openapi.json) |
| the exact bytes an issuer or identity signs | the concept page ([attestations](./achievements-and-attestations.md), [authentication](./identity/authentication.md)) plus the signing vectors |
| the shape of a durable event | the [event catalogue](./protocol-events-catalogue.md) |
| how a tree head is verified | [network trust anchors](./network-trust-anchors.md) and [witness cosigning](./witness-cosigning.md) |
| node and ledger route behavior | [nodes](../architecture/nodes/README.md), [settlement](../architecture/settlement.md), and the server source |

## Implementation

Status: partially implemented, as described above. Generation is in [`crates/server/src/openapi.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/openapi.rs), and the SDKs' generated bindings are in [avalon-sdks](https://github.com/avalon-initiative/avalon-sdks/tree/main/languages).

## Related

- [Protocol concept map](./README.md), [SDK overview](../sdk/README.md), [SDK design](../sdk/design.md)
- [Protocol events](./protocol-events.md), [security model](./security-model.md)
