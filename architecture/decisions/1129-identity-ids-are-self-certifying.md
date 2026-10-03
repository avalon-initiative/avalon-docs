# ADR-1129: Make identity ids self-certifying so they can never clash across shards

**Status:** Accepted — decided 2026-10-02

Original record: [avalon-protocol#1129](https://github.com/avalon-initiative/avalon-protocol/issues/1129). The decision was recorded in the comments of that issue, which also tracks the implementation and was still open when this page was written. The text below preserves the recorded decision; `#N` references are avalon-protocol issue numbers and file paths are as they were when the decision was made.

## Context

An identity id must never clash between two users, and must stay the same for a user over time. A clash is a stop-everything defect.

The id used to be a random UUID chosen by the client, and nothing made it unique beyond one node's database:

- `POST /identities/register/start` took `identity_id` from the client and applied no version, variant, or key check.
- Uniqueness was the `identities.id` primary key on one node. A second node or shard had no check at all, and mirroring is a background poll, so there was always a window.
- The id was not bound to a key. `identity.created` carried only `identity_id` and `display_name`, and the registration signature was checked and then discarded, so a mirror could not re-verify it.
- Staticity held only because no code path renamed, merged, or deleted an id.
- Self-certifying shard ids already existed (`node:<sha256(pubkey)>`); identity ids did not follow that pattern.

## Decision

Identity ids become self-certifying.

- The id is derived from the identity's initial event-signing public key with a domain-separated SHA-256, using the full 256 bits (no truncation). It commits to the inception key only, so rotation, recovery, and device changes never change it. Later key changes must be signed by an already-active key (#1130).
- Format: lowercase hex of SHA-256("avalon-identity-id-v1" || inception public key), 64 characters, no prefix (a prefix would collide with the `:`-delimited global ids and signing bytes). Parsing is strict and never normalizes.
- A server-generated id was considered and rejected: a server can only check what it and its peers currently know, replication is a background poll so two shards can mint the same id before either hears of the other, and a hostile or buggy server could hand out an id that already exists with nothing in the ledger to prove otherwise. A self-certifying id needs no registry and a clash gives an attacker nothing, because only the key holder can sign for the id.
- `register/start` carries the public key. The server recomputes the id and rejects a mismatch, and the key and its signature are carried in the ledger event so they can be verified at mirror and projection time.
- Storage: one `TEXT` column per id with a lowercase-hex `CHECK`. Only identity ids change; guild, channel, event, signing key, and passkey ids stay UUIDs.
- Encodings: the public key is hex inside signing bytes and base64 on the wire; the conformance vectors pin both.
- Signatures: strict Ed25519 verification for every identity signature, with negative vectors in all SDKs.
- WebAuthn: the user handle is the first 16 bytes of the id, since the library takes a UUID.
- No compatibility path: dev databases are wiped and every node updates together. Decoders reject v1 of `identity.created`, `identity.signing_key_added`, and `identity.signing_key_revoked`; this is the sanctioned exception to the versioning policy's "every version stays decodable".
- Key revocation is signed by an active key of the same identity, and a hostile shard cannot revoke another identity's keys.
- Display names stay best-effort unique per node; ids are what everything keys on. Across shards the earliest verified ledger position wins, ties broken by the smaller entry hash, and the loser is reported as a conflict, not silently merged. A display name that is exactly 64 lowercase hex characters is refused, so an id and a handle stay distinguishable.
- Slices: #1133 (derivation, signing bytes, vectors), #1134 (server, schema, API), #1130 (projection verification), then the SDKs, Hub, and docs.
- Left open when recorded: what authorizes a new signing key after guardian recovery when every signing key is lost, decided in [ADR 1135](1135-recovery-authorises-a-new-signing-key-with-guardian-signatures.md). Passkey registration events carrying no proof is tracked as a follow-up.

## Consequences

- The id is unique by construction and verifiable by anyone from the public ledger, and unchanged by key rotation or recovery.
- The `identity.created` signing bytes change to a v2 that includes the key, `register/start` requires the key, the event payloads and the OpenAPI schema change, and the SDK and CLI registration code must follow. Protocol first, then SDKs.
- Alternatives considered: server-generated ids (no cross-shard guarantee without a namespace) and shard-prefixed ids (ties an identity to its birth shard).

## Implementation state

This section is not part of the recorded decision. The derivation, signing bytes, vectors, server, schema, and API (#1133, #1134) are in the protocol repository's main branch; see [identity](../../protocol/identity.md#the-identity-id). Projection-time verification (#1130) and the SDK changes are not built; see [what is not built yet](../../protocol/identity.md#what-is-not-built-yet).

## Related

#1130 (verify identity events at projection time), #1133, #1134, [ADR 1135](1135-recovery-authorises-a-new-signing-key-with-guardian-signatures.md), [ADR 0786](0786-on-demand-cross-node-identity-data-resolution.md), [identity](../../protocol/identity.md).
