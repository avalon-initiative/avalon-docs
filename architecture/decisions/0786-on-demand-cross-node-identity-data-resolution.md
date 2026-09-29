# ADR-0786: On-Demand Cross-Node Identity Data Resolution

**Status:** Accepted — decided 2026-09-23

Original record: [avalon-protocol#786](https://github.com/avalon-initiative/avalon-protocol/issues/786). The text below is preserved as recorded; `#N` references are avalon-protocol issue numbers and file paths are as they were when the decision was made.

## Context

The interest DHT (#580) and its `identity_locator::resolve` lookup (#635) already exist and already do a live, verified cross-node fetch — but only for one narrow purpose: `cross_node_login.rs::resolve_signing_key_cross_shard` uses it to fetch a signing key when verifying a login grant, walking the DHT-returned candidate base_urls sequentially and stopping at the first verified success.

Every other read path never does this. A node answers general queries (profile, friends, guild membership, achievements) strictly from its own local Postgres projections. If a node has never seen an identity, it returns not-found, full stop — no live peer query is triggered. The data only shows up locally once ordinary mirror-sync (STH polling) happens to replicate it on its own schedule.

This creates a real problem: an integrator querying node A for an existing user X, where X has simply never interacted with node A before, gets an indistinguishable "not found" whether X doesn't exist on the network at all, or X exists and is fully served by other nodes but hasn't been mirrored to A yet. There is no negative cache, bloom filter, or authoritative-absence signal anywhere in this code to tell those apart, and no live search happens before giving up.

Meanwhile, a login on node A is itself a meaningful signal: an identity authenticating on a node it has no local projections for is effectively declaring "I may use this node going forward" — exactly the kind of interest the DHT interest-registration mechanism (`InterestScope::Identity`) already exists to track for other purposes.

## Decision

**General identity-data reads get the same live cross-node resolution login already has, generalized beyond signing-key lookups — and a successful remote find replicates back to the requesting node instead of waiting for ordinary mirror-sync.**

Concretely:

- When a node has no local projection for a queried identity, before answering not-found it performs the same bounded lookup login already does: query the interest DHT locator for other nodes currently advertising interest in that identity, then fetch verified ledger entries from those candidates (proof/STH-verified, reusing the existing `cross_shard_fetch` verification path) — sequentially, stopping at the first verified success. No new fanout/timeout budget is introduced beyond what already bounds the login path: an empty DHT candidate list means stop immediately, no exhaustive network scan.
- On a successful remote find, the fetched, verified ledger entries are replayed through the same ingestion path `mirror_watcher` already uses to materialize local projections — the identity becomes durably local to node A immediately, not on the next sync cycle. Node A also registers its own `InterestScope::Identity` record for that identity going forward, since it now legitimately has (and may again be asked to serve) that identity's data.
- This produces a real three-way outcome instead of a collapsed binary: (1) found locally — ordinary fast path, unchanged; (2) not local, but found via live cross-node search and backfilled — now served correctly and durably, with only the one-time lookup latency paid; (3) not found locally and not found anywhere in the DHT's interest set — treated as genuinely absent from the network (or not yet advertised anywhere), returned as not-found without hanging or retrying.
- Scope: general reads for identity-owned data an integrator or the Hub queries (profile, friends, guild membership, achievements, etc.), not writes. Writes still go through their normal authoritative-node path.

## Consequences

- `cross_shard_fetch`/the verified-fetch mechanism currently living inside `cross_node_login.rs` needs to be generalized into a reusable primitive callable from ordinary read paths, not just login verification.
- Every general read endpoint that currently queries local Postgres and returns not-found on a miss needs a "local miss → live cross-node fallback" hook wired in.
- A replicate-back/backfill path needs to exist: verified remote entries get ingested into local projections outside of `mirror_watcher`'s normal poll cycle, and the node's own DHT interest registration needs to be updated as a side effect.
- Read latency for the genuinely-new-to-this-node case goes up by one bounded cross-node round trip (already the login path's existing cost) — acceptable, since it only pays on a local miss and self-heals the node's future reads.
- Tracked for implementation as a new epic with sub-issues covering: generalizing the verified-fetch primitive, wiring the read-path fallback, the replicate-back/ingestion mechanism, and the found/not-found/not-yet-synced outcome handling + observability.

## Related

#580 (interest DHT this builds on), #635 (identity locator this generalizes), #623/#656 (cross-node login, the only existing consumer of live cross-node fetch today), #542 (the original interest-routing decision this stays consistent with).
