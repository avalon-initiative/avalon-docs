# ADR-1153: Decision: every signed and ledger format is versioned and forward-compatible before launch

**Status:** Accepted — decided 2026-10-05

Original record: [avalon-protocol#1153](https://github.com/avalon-initiative/avalon-protocol/issues/1153). The text below is preserved as recorded; `#N` references are avalon-protocol issue numbers and file paths are as they were when the decision was made.

## Context

Formats that cannot change after launch force a reset if they are wrong. Decide the rules that make them extensible now: an explicit version in every signed structure, reserved fields, how unknown fields are treated when hashing and signing, canonical encoding, and the set of formats this covers (signing bytes, STH, evidence, identity events, schema/instance, node announce).

## Decision

Every signed and ledger format is versioned and forward-compatible before launch, under these rules.

- **Protocol kinds** (identity, guild, social, node requests) use fixed binary layouts from the structured signing primitive (#1225): a domain tag, then a `u16` layout version, then fields in a fixed order with length-prefixed strings and raw byte keys and hashes.
- **Free-form payloads** (integrator schemas, game data, attestation metadata) use RFC 8785 canonical JSON with two restrictions: a number is valid only if it survives a round trip through an IEEE double without changing its decimal text (at most 15 significant digits, integers within +/-2^53; anything needing more precision is a string), and duplicate keys are rejected. Invalid numbers and duplicate keys are rejected at submit time.
- **The ledger entry commits to a hash of the payload**, not the payload bytes, so a skeleton row verifies without its payload and a pruned or erased payload never breaks a leaf. The entry hash itself moves to the structured layout (length prefixes, raw bytes instead of hex text, domain tag, shard id, `seq`, full timestamp precision), tracked in #1226.
- **Version fields:** the layout version sits in the signed prefix immediately after the domain tag (for ledger entries, the existing `version` field); each payload also carries its own kind version `v`. Both are covered by the hash and the signature.
- **Unknown fields** are hashed and signed exactly as received and never stripped. In fixed layouts a new field means a new version.
- **Unknown kinds and versions:** on the write path they are rejected at submit with a typed error naming the supported versions. On the replication path they are preserved, mirrored and relayed but not projected, and the node makes this visible: node status counts unprocessed entries by kind and version with a needs-upgrade flag, API reads from projections known to be incomplete carry a marker, and SDKs surface a typed warning.

## Why

Ledger bytes outlive API versions, so a wrong or unversioned format forces a reset. The two hand-rolled `canonical_json` copies (`identity_chain_wire.rs`, `chain/postgres.rs`) leave floats, string escaping, key order for non-BMP characters and duplicate keys implementation-defined, and the entry hash concatenates variable-length fields without length prefixes. A bounded, standard canonical form is something three SDKs can implement identically. Committing to a payload hash keeps retention pruning and the erasure options (#1299) compatible with verification. Silent ignoring of unknown versions would hide missing data from integrators and their users, so the write path rejects and the replication path flags.

## Alternatives considered

- Version only at the API layer. Rejected: ledger bytes outlive API versions.
- Freeze today's formats unversioned. Rejected: any later fix becomes a reset.

## Consequences

Replaces both `canonical_json` copies with one shared implementation and vectors in protocol and all three SDKs; changes `hash_entry` (no real history exists on any network, so no migration); unblocks #1225 and the migration slices #1226 and #1214. Follow-up slices: the shared canonical payload encoding, write-path validation of kinds, versions and numbers, and visibility of unprocessed entries.

## Related

Part of the network upgrade epic (#1150).
