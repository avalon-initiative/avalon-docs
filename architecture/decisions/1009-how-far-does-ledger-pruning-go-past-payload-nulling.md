# ADR-1009: how far does ledger pruning go past payload-nulling — checkpoint/archive tiering for skeleton rows?

**Status:** Accepted — decided 2026-09-28

Original record: [avalon-protocol#1009](https://github.com/avalon-initiative/avalon-protocol/issues/1009). The text below is preserved as recorded; `#N` references are avalon-protocol issue numbers and file paths are as they were when the decision was made.

## Context

Existing node-tiered retention (full vs. hot tier, `AVALON_RETENTION_TIER`, `AVALON_RETENTION_HOT_WINDOW_DAYS`, `AVALON_RETENTION_PRUNING_ENABLED`) already nulls `ledger_entries.payload` on hot-tier nodes past a configurable window, while keeping the hash-chain skeleton (`seq`, `entry_hash`, `prev_hash`, `kind`, `issuer`, `subject`, `event_timestamp`, `version`, `batch_id`) forever, on every node, regardless of tier — this preserves chain/Merkle verifiability.

That solves payload weight. It does not solve row-count growth: the skeleton row itself never goes away today, even on hot-tier nodes. At real long-run scale (many integrators, long-lived identities, years of operation), skeleton-row volume alone becomes the actual growth driver, independent of payload size — rough order of magnitude: a skeleton row is on the order of 150-250 bytes, and a broadly-adopted network (the stated stress target is 100M identities) could plausibly reach billions of rows over its lifetime. Not catastrophic at that scale (fits with normal partitioning), but the trajectory is genuinely unbounded over a long enough horizon, which is the actual concern driving this ticket.

This is distinct from operational/ephemeral data (guild chat, DMs), which already has its own bounded cap+archive+hard-delete lifecycle unrelated to the ledger.

## Decision

Decided 2026-09-28, refined the same day: tiered retention with an opt-in archival role. Hot nodes stay light; full archival is something an operator chooses to run.

Retention bands:
- **Hot (on the node):** a bounded recent window, about a year as the starting default and configurable, plus signed checkpoints (signed tree heads and the Merkle frontier needed to verify the current head). Past the window the node prunes payloads and skeleton rows. It keeps appending and verifying the current head regardless.
- **Archive (online, fast):** full archival nodes are an opt-in setting, not a node type. They keep every row and answer requests for pruned ranges.
- **Cold (roughly 2 to 3+ years old):** archival operators may move old batches (skeleton and hash data keyed by leaf index) to cold append-only storage of their choosing. Retrieval from cold is slower by design, and the protocol allows for that with an explicit pending / retry-after outcome rather than treating a slow answer as a failure.

Fetch-through: a hot node that needs data behind its window (an old entry or proof) asks a node that advertises the archive capability, and can return the result to the requester. Anything fetched is verified against the checkpoints the hot node already holds (an inclusion proof against a signed head), so an archival node is used but not trusted.

- Nodes advertise the archive capability in discovery.
- There is no network-wide obligation to retain history. Answerability of old data depends on at least one archival node being reachable; the docs state that limit.

Not decided here (implementation ticket): the default horizon value, whether and for how long hot nodes cache fetched old ranges, the cold-storage interface, the retry-after contract for cold ranges, and the wire format for requesting data or a proof from an archival node.

## Why

Verifiability of a hash-chained, Merkle-rooted log is a property of the current Signed Tree Head plus the ability to produce a consistency/inclusion proof — it does not strictly require every node to retain every historical leaf forever. This is the same tradeoff Certificate Transparency-style logs make: checkpoint-only nodes stay verifiable against the current root, while full leaf history (needed to actually produce a proof for an old entry on demand) can live in cheaper, slower-tiered storage, held by fewer nodes.

Per-shard partitioning already bounds this somewhat: an abandoned/dead integrator's shard stops growing and becomes a pure archival concern, not part of an unbounded single stream. Total growth is the sum of active shards, not one firehose.

## Alternatives considered

- **Status quo (current payload-only pruning, skeleton retained forever, on every node):** simplest, already shipped, but doesn't bound row-count growth over a long enough horizon.
- **Cold/object-storage tiering for old batches (skeleton + hash data moved out of hot Postgres to cheap append-only storage, keyed by leaf index):** keeps full historical proof capability somewhere, removes the growth from operational Postgres, but needs a defined "who holds the archive" commitment and a lookup path for proof requests against archived ranges.
- **True skeleton deletion past a horizon, checkpoint-only beyond it:** bounds storage most aggressively, but permanently sacrifices the ability to produce inclusion proofs for anything past the retained horizon unless some other party (an opted-in archive tier) still holds it. Not a cryptographic problem, purely a policy choice about who commits to long-term retention.

## Consequences

- This replaces the current rule that skeleton rows are kept forever on every node regardless of tier; retention and settlement docs must be updated with it.
- Checkpointing per shard is required so a hot node can drop old skeleton rows and still verify the current head.
- Verification of current heads is unaffected. Old inclusion proofs become best-effort, served by archival nodes.
- Implementation is a separate ticket; nothing changes in behavior until it lands.

## Related

Builds on the existing node-tiered retention design (full vs. hot tier, payload-only pruning) and the per-shard settlement/STH model.
