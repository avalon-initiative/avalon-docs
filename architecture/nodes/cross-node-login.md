# Cross-Node Login

**Status:** Implemented

A person can log in through a node they never registered a passkey on, with no shared login domain, using a signed, human-approved, destination-bound assertion. It extends the [cross-device pairing](../../protocol/identity.md) pattern to a different node rather than a different device.

## The grant

A cross-node login grant is a self-signed assertion that a human, shown real information about the requesting node, approved logging an identity into one specific destination node. The server-side lifecycle is start, poll, submit, and deny endpoints under `/auth/cross-node/`. It resembles the device-pairing create, poll, and approve flow but is genuinely cross-node: approval never needs a live session on the requesting node. Verification checks the grant's signature against the identity's signing keys, binds the grant's claimed URL to this node's own URL, and rejects replay through a consumed-nonce table.

## Finding the identity's keys

- **Identity locator.** A DHT registration and lookup, the same shape interest scopes use, resolves which nodes currently hold an identity's signing keys. `GET /identities/{id}/locations` is deliberately unauthenticated because it must work before login completes, and it returns the full known set, never a single winner.
- **Verified cross-shard fetch.** Given a shard and a node URL, the verifier fetches every ledger entry for a subject and checks each end to end: a signature-checked tree head, an RFC 6962 inclusion proof against that head, and the entry hash recomputed from the fetched content and compared with both the claimed hash and the proof's leaf. Without the last check a remote node could return a genuine proof for some real entry alongside a forged payload. If the grant's key is not in the destination's local tables, verification chains the locator with this fetch against each candidate node, matching the key history by key id and checking revocation the same way local lookup does.
- A verified signing key alone does not mint a session. The destination also best-effort provisions a minimal local identity and profile stub by fetching the identity's own creation entry, silently skipped (never a login failure) on a display-name collision, since a node's uniqueness index cannot be enforced globally.

## Approval

There is no hard allowlist on the requesting integrator, because that would block a brand-new integrator's very first login, the case this exists to unlock. Instead the approval screen always renders but distinguishes a verified requester from an unverified one. An owned shard is verified when its owner resolves to a real integrator holding an unrevoked `shard_settlement` key for exactly that shard; the unowned `core` shard is verified when the requesting node's URL is one of the network's pinned seed nodes. A mobile deep link never auto-approves from a scan; an explicit confirm step is always required.

The Hub and the desktop and mobile app each have an approval screen (the desktop app with a custom-scheme deep link; platform universal links are not yet set up). Each mints and signs a grant locally and submits it to the requesting node's own address, never the approving client's configured server.

Rate limiting is inherited from the shared per-IP and per-principal limiters.

## Known race

The outbox writes each event durably in the same transaction as the request, but a background worker folds it into the ledger later. For roughly one poll interval an event is durable but not yet ledger-visible or fetchable cross-shard, so a login attempted within seconds of an identity's very first registration on its owning node can fail. It resolves on retry.

## Implementation

Status: Implemented. The grant type is in the [protocol crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/protocol) and the lifecycle, locator, and verified fetch are in the [server crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/server) of avalon-protocol. Approval screens are in the [Hub repository](https://github.com/avalon-initiative/avalon-hub).

## Related

- [Nodes](README.md)
- [Identity](../../protocol/identity.md)
- [Discovery and peering](discovery-and-peering.md)
- [Sharding](../settlement/sharding.md)
