# ADR-0177: Embedded Ledger Storage Engine Is RocksDB

**Status:** Superseded — decided 2026-09-09

Original record: [avalon-protocol#177](https://github.com/avalon-initiative/avalon-protocol/issues/177). The text below is preserved as recorded; `#N` references are avalon-protocol issue numbers and file paths are as they were when the decision was made.

> Superseded by [ADR-0186](0186-no-blockchain-validator-consensus-transparency-log-only.md): settlement storage is Postgres, permanently, so an embedded per-node ledger engine is not used.

## Context

#40 (open) scopes the remaining settlement-layer design after ADR #68/#70/#93
decided the shape (a public, append-only, cryptographically verifiable log,
run as Avalon's own chain — not Postgres). One of the four things #40 leaves
open is narrowly the **embedded storage engine** each node/mirror uses for
its local copy of the ledger — RocksDB, `sled`, `redb`, or a comparable
engine — independent of the log/Merkle design, the validator/consensus
design, and the Postgres migration path, all three of which stay open under
#40.

Candidates considered:

- **RocksDB** (via the `rocksdb` crate, C++ core with Rust bindings). The
  most battle-tested embedded KV store in this exact problem space — an
  LSM-tree engine built for high-volume sequential writes with point/range
  reads, which is exactly an append-only, seq-ordered ledger's access
  pattern. Already `rusty-kaspa`'s choice for blocks/DAG/UTXO state, and
  already `docs/architecture/settlement.md`'s own closest reference point
  for what a comparable high-throughput commitment log needs. Real cost: a
  C++ dependency, not pure Rust — needs `cmake` (and a C++ toolchain) to
  build from source, which is not preinstalled everywhere a contributor or
  CI runner might build this from.
- **`sled`**: pure Rust, no C++ toolchain requirement, appealing for build
  simplicity. Weighed against: its own project status has been openly
  described by its maintainer as not production-hardened for new adopters,
  and it has not seen the kind of sustained, high-throughput production use
  this ledger needs to lean on. Betting the durable settlement layer on it
  would mean this project absorbing storage-engine risk instead of using
  someone else's already-paid-down maturity.
- **`redb`**: pure Rust, simpler API, single-file, newer project. Promising
  but with materially less production track record at any comparable scale
  than RocksDB has via Kaspa (and via the much wider set of production
  systems built on RocksDB itself, independent of the blockchain space).

## Decision

Avalon's embedded ledger storage engine is **RocksDB**.

## Why

- Maturity and battle-testing at real throughput dominate the other
  criteria for a component holding durable, append-only settlement history
  that (per ADR #70) has to be independently verifiable and mirrorable —
  this is exactly the place to prefer "tried and true" over "simpler to
  build," matching the reasoning `docs/architecture/settlement.md` already
  used to pick Kaspa as its reference system in the first place.
- The C++/`cmake` build cost is real but bounded and one-time per
  environment (tracked as a setup requirement, not a recurring one) — it
  does not recur per commit or per node the way a storage-engine correctness
  bug would.
- Kaspa's own choice under comparable (high block-rate) throughput
  requirements is direct evidence for this exact workload shape, not just a
  generic "RocksDB is popular" argument.

## Alternatives considered

`sled` and `redb` — see Context above. Both rejected on production maturity
at this project's durability requirements, not on API ergonomics or license.

## Consequences

- Building `avalon-chain`'s RocksDB-backed `SettlementProvider` (tracked as
  its own feature ticket, migration-path work still under #40) requires
  `cmake` and a C++ toolchain in every environment that builds this crate
  from source — local dev machines, CI, and this sandbox alike. This is a
  new environment dependency this project didn't have before.
- `#40` is updated to reflect this sub-question resolved; log/Merkle design,
  validator/consensus design, and the actual Postgres→RocksDB migration path
  remain open under it.
- Postgres's role is unaffected outside settlement storage itself — the
  indexer's projections and ephemeral state stay exactly where they are, per
  `docs/architecture/query-and-indexing.md`.

## Related

#40, #68, #70, #93, `docs/architecture/settlement.md`
