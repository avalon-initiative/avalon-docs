# Managed Shard Hosting

**Status:** Partially implemented — the mechanism is implemented and tested; no live managed shard exists

Not every integrator that wants shard authority wants to run a server. A managed host, first-party or third-party, can run the storage, batching, and Merkle computation for an integrator's shard while the integrator keeps its own settlement signing key exactly as if it were self-hosting. This page describes the two-phase signing that makes that safe and the integrator's recourse if the host misbehaves.

It builds on [sharding](../settlement/sharding.md) and the shard-operator model in [self-hosting](../self-hosting.md).

## Why not the node-to-node submit path

The node-to-node submit endpoint has the receiving node sign with its own local settlement key. That is correct when a remote node genuinely owns full settlement authority and wrong here, since a managed host must never hold the integrator's key.

## Two-phase remote signing

1. **Prepare.** The integrator submits pending events to the host. The host does storage, batching, and Merkle computation over its accumulated shard log exactly as a normal commit does, but stops before signing. It returns the unsigned candidate tree-head fields (`tree_size`, `root_hash`, `network_id`, `timestamp`) and a batch id, and writes nothing authoritative. The preview never touches the ledger tables or shared Merkle cache, and does not burn real sequence numbers.
2. **Sign locally.** The integrator signs that digest with its own settlement key. The key is never transmitted to the host.
3. **Finalize.** The integrator posts back the batch id and signature. The host does not trust the earlier preview: it recomputes the batch's insertion and resulting tree size and root fresh, inside a transaction, and only then verifies the signature against those freshly computed values and the shard's registered verify key. A stale finalize (the tip moved) or a forged signature fails that one check and the transaction rolls back, burning nothing. A batch that was prepared but never validly finalized stays visibly stuck, never silently accepted.

**Trust boundary, enforced mechanically.** A managed host is structurally incapable of producing a valid head for a shard whose signing key it does not hold, the same guarantee the issuer key-custody model gives issuer keys ([issuers](../../protocol/issuers.md)). Hosting is infrastructure only and carries no elevated trust over the integrator's history.

A managed-hosting operator wants a settlement-only node: without role extraction the host would still mount every Gateway-facing module, which is attack surface with no legitimate caller ([roles and extraction](../nodes/roles-and-extraction.md)). An interim rule presumes a managed-hosting node is dedicated to one hosted integrator's shard and names that integrator's public settlement key directly, rather than resolving it from the general per-shard trust anchor at scale. Both endpoints refuse every request until it is configured.

## Censorship recourse

Two-phase signing means a host cannot forge history, but it can refuse to prepare a batch, or go dark, withholding service from one integrator (an explicit liveness limitation named in the [security model](../../protocol/security-model.md)). The recourse is that an integrator is never cryptographically bound to one host.

- **The shard's identity is the integrator's own key**, authorized through its registered `shard_settlement` key event, not through anything the host controls. A host can decline to help; it cannot reassign or freeze the authorization.
- **Switching hosts, or self-hosting, has no continuity break.** The shard's log is a normal mirrorable log. A new host or a self-hosted node syncs the existing history from any mirror and resumes from where the stalled host left off.
- **Automatic multi-host failover.** An SDK client can be given several candidate hosts. It fans the read-only prepare step out to every candidate concurrently, uses whichever answers first, and finalizes against that one host only. A concurrent finalize fan-out would fork the shard's log (each host holds its own ledger, so committing the same batch to two appends it after two different tips), so prepare-race and finalize-once avoids that by construction, not by locking. If the chosen host's finalize fails, the client races the remaining candidates. Finalize is idempotent on a replayed batch id, which de-duplicates retries against the same host but not across two.
- **Manual switch readiness.** A read-only command compares an old and a new host for a shard: it fetches the old host's latest head, then the new host's head at that exact tree size, and reports ready (roots agree), not ready (new host behind), mismatch (both claim a value at the same size but disagree, a serious finding), or unknown (old host unreachable). A verify-key option additionally checks signatures; without it, "ready" only means the two hosts agree with each other, not that either is honest. It changes nothing; cutting over stays a deliberate operator action.

## Implementation

Status: The two-phase endpoints, idempotent finalize, and switch-readiness command are implemented in [avalon-protocol](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates); the multi-host client is in the Rust SDK in [avalon-sdks](https://github.com/avalon-initiative/avalon-sdks/tree/main/languages/rust). They are live-verified against real processes. Planned: a managed shard operated for a real integrator.

## Related

- [Self-hosting](../self-hosting.md)
- [Sharding and cross-shard commitment](../settlement/sharding.md)
- [Issuers](../../protocol/issuers.md), [security model](../../protocol/security-model.md)
