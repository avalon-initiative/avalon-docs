# Protocol Events

**Status:** Implemented — with one labeled gap: most events are attributed by the node on an actor's behalf and are not yet individually signed by that actor.

A protocol event is a durable fact Avalon considers part of its history. Not every integrator action is a protocol event, and ordinary gameplay never becomes one. Events are the canonical record and every table is a projection of them; history is append-only, so a correction is a new event and never an edit. This page describes the event envelope, the pipeline from event to settled history, and the versioning policy. The row-by-row list of kinds is the [event catalogue](./protocol-events-catalogue.md); a concrete ordered example is the [worked ledger example](./worked-ledger-example.md).

## Hot gameplay versus durable events

| Stays integrator-side (never an event) | May enter durable history |
| --- | --- |
| movement, combat, physics, AI | achievement issued or revoked |
| HP, XP ticks, NPC state, player position | integrator event result |
| matchmaking, ordinary chat | guild created, membership or role changed |
| game-specific inventory and economy | integrator registered, binding established |
| typing indicators, connection state, presence | issuer registered, key added or revoked |
| | ownership transferred (later phase) |

The test: would this fact matter outside the integrator that produced it, and does Avalon promise to preserve it? If either answer is no, it is not a protocol event. Presence is never one (see [presence](./presence.md)). The principle is recorded in [ADR 0075](../architecture/decisions/0075-durable-protocol-history-is-canonical-query-databases-are-projections.md).

## The envelope

Every event has the same shape:

```text
ProtocolEvent
    id            Uuid
    kind          string, namespaced, e.g. "achievement.issued"
    issuer        GlobalId   who asserts this fact
    subject       GlobalId   what or whom it is about
    payload       JSON       one schema per kind and version
    timestamp     RFC 3339
    version       u32        payload schema version for this kind
    identity_chain  optional per-identity chain position (layer-1 events only)
```

`kind` stays a plain string on the wire. In code, a `ProtocolEventKind` enum maps every known kind to a permanent wire string and has an `Other(String)` escape hatch, so a new kind never needs a protocol version bump while every known kind gets compile-time safety. Payloads are built from one typed struct per kind, never ad-hoc JSON. `EventBatch` is the settlement layer's unit of commitment over a group of events and is not itself an event, and `Commitment.proof` is opaque to the protocol crate (a ledger hash, a signed tree head, or a Merkle root).

Layer-1 events (profile, friends, guild membership, keys, recovery) additionally carry a per-identity sequence number and previous-event hash, independent of the global ledger order, stored in the ledger entry payload under a reserved `_identity_chain` key, so it is covered by the entry hash through the payload hash; see [per-identity event chains](./identity/event-chains.md). The chain hash is taken over the event's own payload without that key, in [canonical form](#canonical-payloads-and-signing-bytes), with the timestamp at microsecond precision.

## Canonical payloads and signing bytes

Implemented in the protocol repository and all three SDKs for the formats named below as migrated; the remaining signed formats are Planned, as listed at the end of this section.

Every signed or hashed message shares three rules, so independent implementations produce identical bytes.

- **Structured signing bytes.** A message is a domain tag (ASCII, with no length prefix), a `u16` big-endian layout version, then fields in a fixed order. Strings and byte strings carry a `u32` big-endian length, keys and hashes are raw fixed-width bytes, and integers are fixed-width big-endian. Nothing is self-describing: a new field means a new layout version, and no field can shift the boundary of another. Every signed kind has its own tag in a registry, tags are never reused, and none is a prefix of another. The registry and the byte layouts are pinned by the conformance vectors `domain-tags.json` and `structured-signing-bytes.json`.
- **Canonical payload.** A free-form event payload is hashed in a restricted form of RFC 8785 (JSON canonicalization): object keys sort by UTF-16 code units, strings escape only what the RFC requires, duplicate keys are rejected, and nesting is limited to 128 levels. A number is valid only if its decimal text survives a round trip through an IEEE double unchanged: integers within ±2^53, and other numbers with at most 15 significant digits written exactly as ECMAScript prints them. Anything else, such as `1.0`, `1e2`, or a large integer, must be sent as a string. A payload with no canonical form is refused when the event is recorded, with 400 `INVALID_PAYLOAD`; an event version above 65535, which the entry layout cannot carry, is refused with 400 `UNSUPPORTED_ENTRY_VERSION`. Pinned by `canonical-payload.json`.
- **Ledger entry hash.** The hash that chains ledger entries is itself a structured layout (tag `avalon.ledger.entry`; see [settlement](../architecture/settlement.md#log-structure)). It covers the network id, shard id, sequence number, previous entry hash, event id, kind, issuer, subject, the event time in microseconds, and the SHA-256 of the canonical payload. Because it commits to the payload hash, a row with a pruned payload still verifies. The version slot of this layout carries the event's own `version`, so a changed field set needs a new tag rather than a new version. Pinned by `ledger-entry-hash.json`. The change shipped with no compatibility path: a database holding entries from before it is wiped, not migrated.

**Migrated so far:** `identity.created`, the device-grant approval, and the signing-key revocation (see [identity](./identity.md#the-identity-id)), and the ledger entry hash. **Not migrated yet (Planned):** cross-node login grants, session continuation tokens, interest claims, achievement and revocation signing, issuer registration, the signature-required action gate, and the integrator nonce challenge still sign the older colon-delimited text layouts. Their tags are already reserved in the registry. The tree-head, witness, shard-identity, and node-request layouts, and the identity chain hash, keep their own binary formats.

Which ledger payload fields are authority state, pseudonymous identifiers, free-text content, or personal data is classified field by field in the [ledger payload field inventory](https://github.com/avalon-initiative/avalon-protocol/blob/main/docs/maintainers/ledger-payload-field-inventory.md); the dispositions there are proposals feeding the format freeze and change no wire format yet.

## The pipeline

```text
Protocol Event
      |
      +----> Query Projection          (indexer; rebuildable)
      |
      +----> Outbox / event buffer
                  |
                  v
              Batching                  (EventBatch)
                  |
                  v
          Commitment / Merkle root      (RFC 6962 tree, Signed Tree Head)
                  |
                  v
              Settlement                (transparency log on Postgres)
```

An event fans out to the read model and to the settlement path. The projection is the optimized copy and the settled history is the record. One event is never one settlement transaction. Events are enqueued in an outbox in the same transaction as the row change they accompany, and the settlement worker commits whatever batch its current drain tick assembles (a single-event batch is legal). The settlement model is described in [settlement](../architecture/settlement.md); Avalon's ledger is a signed, append-only transparency log and not a blockchain, per [ADR 0070](../architecture/decisions/0070-settlement-is-a-public-transparency-log.md) and [ADR 0186](../architecture/decisions/0186-no-blockchain-validator-consensus-transparency-log-only.md).

## Design properties

Every durable event can be signed, verified, indexed idempotently, replayed in order from genesis to rebuild any projection, committed behind a durable commitment, corrected only by a later event, versioned so it stays decodable for as long as the log exists, and audited (issuer, subject, timestamp, and log position are independently checkable). Events carry enough canonical information to reconstruct required state and no more; anything derivable from other events is computed by the indexer and not stored twice.

## Signing posture

Two postures recur. **Signature-verified** events are built only after a real signature by the actor with authority verifies: `identity.created`, `identity.signing_key_added` for a device grant, and `identity.signing_key_revoked` (by the identity's own keys), and `achievement.issued`, `achievement.revoked`, and their milestone equivalents (a detached issuer signature in the request). Of these, `identity.created`, device-grant `identity.signing_key_added`, `identity.signing_key_revoked`, `achievement.issued`, and `milestone.issued` embed the proof in the durable payload, so a third party can re-verify them from the ledger alone; for the others the signature is checked at write time and is not stored in the payload. Mirroring nodes verify the embedded identity signatures before projecting them ([identity](./identity.md#projection-time-verification)). **Node-attributed** events are recorded by the node on behalf of an authenticated actor, the current stand-in where no per-event signing ceremony exists yet. Almost every other emitter uses this posture: profile edits, friend actions, guild changes, bindings and grants, recovery steps, integrator registration, key-set changes, schema and data publication. The integrator is authenticated by challenge-response, but the event itself carries no embedded signature. Registration and recovery are necessarily node-attributed, since the requester holds no proven key yet. This is a known gap between the design property "every event can be signed" and the current emitters; the [event catalogue](./protocol-events-catalogue.md) records the actual posture per kind.

## Versioning policy

History may outlive every current maintainer, so:

- Adding an optional field does not change `version`.
- Removing, renaming, or changing the meaning of a field bumps `version`.
- Every version ever emitted stays decodable forever. Decoders are added, never deleted. One recorded exception: version 1 of `identity.created`, `identity.signing_key_added`, and `identity.signing_key_revoked` is no longer decoded, because identity ids changed shape before any network held real history ([ADR 1129](../architecture/decisions/1129-identity-ids-are-self-certifying.md)).
- An unknown kind is preserved and skipped by an indexer that does not understand it, and is never dropped from the log.
- Attestations additionally carry an issuer-declared schema reference so a consumer can recognize "integrator event result, schema v1" independently of the issuer's naming.

"We can change the schema later" is true of a projection table and false of the log.

## History versus current state

Both are kept, and kept distinct:

```text
Guild membership history (events)        Current projection (indexer)
2027-01-01  X joins Guild A              User X
2027-04-14  X becomes Officer                Guild: none
2028-02-10  X leaves Guild A
```

History is reconstructable; current state is optimized for reads and can always be thrown away and rebuilt. A "current status" column on a projection row is a cache of the latest relevant event and never the record. See [revocation](./revocation.md) and [disaster recovery](../architecture/disaster-recovery.md).

## Implementation

Status: implemented. The kind catalogue, typed payloads, and versioning policy are real: every emitter in the server builds its kind and payload through the typed structs, and round-trip and fixture tests exist for every payload.

- Envelope and kinds: [`events.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/events.rs). Payload structs: [`event_payloads.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/event_payloads.rs).
- There is no single dispatcher. Each domain module enqueues its own kinds into `protocol_outbox` ([`outbox.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/outbox.rs)) in the same transaction as the row change.
- Ledger storage: [`crates/chain/src/postgres.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/chain/src/postgres.rs), with the schema in the server's migrations. The entry hash: [`ledger_entry.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/ledger_entry.rs). Signing bytes and the tag registry: [`signing_bytes.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/signing_bytes.rs). Canonical payloads: [`canonical_payload.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/canonical_payload.rs).

## Related

- [Event catalogue](./protocol-events-catalogue.md), [worked ledger example](./worked-ledger-example.md)
- [Per-identity event chains](./identity/event-chains.md), [revocation](./revocation.md), [provenance](./provenance.md)
- [Settlement](../architecture/settlement.md), [query and indexing](../architecture/query-and-indexing.md), [disaster recovery](../architecture/disaster-recovery.md)
- [ADR 0075](../architecture/decisions/0075-durable-protocol-history-is-canonical-query-databases-are-projections.md)
