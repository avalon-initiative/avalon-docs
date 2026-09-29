# Network Trust Anchors

**Status:** Implemented — a maintainer-reviewed trust-anchor list pinned by the SDKs and the Hub; no public mainnet exists yet.

`network_id` alone is never sufficient to trust a server. It is a plain string with no cryptographic authority: anyone can run a node, claim the `network_id` of a real deployment, and serve fabricated history under that name. The only thing that distinguishes a real network from an impostor is whether its Signed Tree Heads (STHs) verify against the specific Ed25519 public key of the real settlement operator. This page covers where that key is published and how a client pins it, the same role a browser's pinned CA roots or SSH's `known_hosts` plays. The per-shard extension, self-certifying shard ids, and domain-proven names are in [shard identity and names](./network-trust-anchors/shard-identity-and-names.md).

## The trust-anchor list

`docs/trusted-networks.json` in the protocol repository is the canonical, versioned, publicly published list. Each entry:

| Field | Meaning |
| --- | --- |
| `label` | Human-readable name. |
| `network_id` | The exact string a node sets as its network id and bakes into its ledger genesis. |
| `verify_key` | Hex Ed25519 public key: the public half of that network's settlement operator signing key. |
| `signing_key_id` | Which key generation this is, matching the STH's `signing_key_id`. A rotated key gets a new entry or a documented rotation, never a silent overwrite. |
| `environment` | `local-dev` (no real deployment; a generated key checked in to exercise the mechanism), `dev` (a real non-production deployment), `int` (a real 1-5 node interconnected test bed for verifying changes before mainnet), or `prod` (real mainnet). The Hub calls out non-`prod` entries. |
| `server_url` | Default node address for the entry. |
| `seed_nodes` | Base URLs of the network's always-on anchor nodes: the default bootstrap peers a node announces to when it has none configured, and the candidate list for an SDK's zero-URL `connect()`. Empty for a network with no anchor yet. |

Being a committed file is the integrity story: changing an entry goes through the same pull-request review and git history as any other change, with deliberately no runtime endpoint to publish a new trust anchor. Clients do not bundle the list. Every official SDK fetches it at runtime from the file's raw URL, so a client always sees the current published file. When it cannot be fetched, the SDKs report the network as unreachable and never fall back to a stale copy.

## What the list contains today

There is no public mainnet yet. The list holds two entries: `avalon-dev-local`, a `local-dev` template entry whose key belongs to no real server, and `avalon-dev-lan`, a `dev` entry for the maintainers' private-network test bed (several nodes on one LAN, not reachable from the internet, no availability or retention promises). Three deployment tiers are supported, one `network_id` prefix each: `avalon-dev-<name>`, `avalon-int-<name>`, and `avalon-mainnet-N`.

`avalon-mainnet-N` is not a namespace for multiple concurrent networks: there is exactly one canonical mainnet at a time, and `N` increments only for a deliberate genesis reset decided and merged by the maintainers. Nothing stops a third party running a node that claims `avalon-mainnet-2`, but unless that exact id and its real key are merged into the list, a pinned client shows it as unknown or unverified.

## Client enforcement

Clients verify a server with the SDKs' network verification (`verifyNetwork()` in TypeScript, and equivalents in Rust and C#). It fetches `GET /ledger/sth/latest`, matches the STH's `network_id` against the list, and independently re-verifies the STH's Ed25519 signature against that entry's `verify_key`, over the message `(tree_size, root_hash, network_id, timestamp)`. The result is one of four states:

- **Verified**: `network_id` is pinned and the signature checks out.
- **Key mismatch**: `network_id` is pinned but the signature does not verify against the pinned key. This is the impostor case, flagged and never silently trusted.
- **Unknown network**: the claimed `network_id` is not in the list. Labeled unverified or custom, never trusted by default.
- **Unreachable**: the STH request or the list fetch failed.

The Hub does not implement verification itself; it uses the TypeScript SDK and shows the network status in its shell, always visible. Switching networks is explicit: the Hub lists every pinned entry with a server URL, offers a labeled "custom network" option, persists the choice, and reloads, since an existing session token has no meaning against a different server. A custom network is never silently treated as verified. The conformance vectors [`signed-tree-head.json`](https://github.com/avalon-initiative/avalon-protocol/blob/main/conformance/vectors/signed-tree-head.json) fix the signed-message format across languages.

## Witness cosigning alongside the pinned key

The pinned `verify_key` is still the log's own signer, and a client that checks only that signature behaves as before. [Witness cosigning](./witness-cosigning.md) is additive: independent nodes cosign heads they have checked for append-only growth, and a verifier that wants more than one key's word accepts a head once a majority of its own known witnesses has cosigned it. With zero or one known witness the rule reduces to the plain author-signature check, so no network is special-cased. The trust-anchor entry format is unchanged and carries no witness list; each verifier builds its own known list from discovery, with the seed nodes as anchors. The three SDKs implement cosigned verification and known-list building (the shared vectors are `witness-cosigned-tree-head.json`, `known-list-selection.json`, and `witness-announce.json`). The Hub itself does not verify cosignatures. A network can move onto witness cosigning without a reset and back off again.

## What this does not solve

Client-side pinning stops a server from impersonating a network it does not hold the key for. It does not stop a maintainer with commit access from merging a bad `verify_key`, or a compromised key from being republished as if still good. That is a governance problem (who can approve a change to the list, and how a key compromise is detected and rotated), not something client code can fix. A pull request touching the list deserves that scrutiny.

It also does not solve the reverse direction: whether a given issuer's key may write on a network. That is the per-network issuer registration gate ([achievements and attestations](./achievements-and-attestations.md#network-admission), [ADR 0479](../architecture/decisions/0479-network-isolation-via-per-network-issuer-registration-not-signature.md)). Node discovery (finding a node) is likewise separate from trust anchors (trusting one once found).

## Genesis reset and migration

A deliberate `avalon-mainnet-N` to `avalon-mainnet-(N+1)` reset is rare and maintainer-decided, and does not start from nothing or ask any issuer to re-sign. Signatures are network-agnostic, so a signature valid on one network verifies identically on the next. A migration carries forward only the outgoing network's final ledger checkpoint (so the new history is a documented continuation, not an unexplained fresh start) and its issuer admission registry (so no issuer, even an unreachable one, has to act to remain admitted). The migration command reads the source, establishes the target's own genesis (failing if the target database already belongs to another network), records the checkpoint in an append-only audit table, and bulk-carries the admission rows idempotently, so a retried run is safe. It never modifies the source.

## Invariants

- The trust-anchor list is the root of trust for network identity; `network_id` alone is never sufficient anywhere in the Hub or SDKs.
- A network not in the list is never silently treated as trusted.
- The list changes only through normal repository review, and there is no path to alter it outside version control.

## Implementation

Status: implemented.

- The list: [`docs/trusted-networks.json`](https://github.com/avalon-initiative/avalon-protocol/blob/main/docs/trusted-networks.json), with the protocol repository's README rendering the same file as a table (a check script fails if the table drifts).
- Server-side parsing (no verification): [`network_trust.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/network_trust.rs). Unlike the SDKs, the server compiles the list in for its own bootstrap-peer and anchor-node checks.
- SDK verification: each language's `network` module in [avalon-sdks](https://github.com/avalon-initiative/avalon-sdks/tree/main/languages), unit-tested against generated Ed25519 keypairs (valid, forged, wrong-key, and unpinned cases).
- Genesis migration: [`crates/chain/src/migration.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/chain/src/migration.rs) and the `avalon migrate-network` CLI command.
- Not built: a "manually add a custom trust anchor" flow in the Hub; the Hub's invariant is met by flagging an unpinned network as unverified.

## Related

- [Shard identity and names](./network-trust-anchors/shard-identity-and-names.md), [witness cosigning](./witness-cosigning.md), [trust model](./trust-model.md), [security model](./security-model.md)
- [Settlement](../architecture/settlement.md), [sharding](../architecture/settlement/sharding.md), [ADR 0070](../architecture/decisions/0070-settlement-is-a-public-transparency-log.md)
