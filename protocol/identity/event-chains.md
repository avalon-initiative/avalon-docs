# Per-Identity Event Chains

**Status:** Partially implemented — the conflict rule, storage, emission, and the profile projection are built; convergence for the friendship, guild-roster, passkey, and signing-key projections, rollback compensations, and SDK support are not.

The global ledger orders events by whichever node committed them first, but two nodes can accept conflicting edits to the same identity before either sees the other's. Per-identity chains give every node a deterministic rule for converging on the same state regardless of arrival order, and for detecting the one case that must never be settled by timestamp: a conflict over which key controls the identity. This page is part of [identity](../identity.md).

## The problem

Two nodes can each accept a layer-1 edit (say, a profile change through one node and a different one through another) and commit them in different global orders. State must converge to the same value on every honest node, so "whichever the ledger says came first" cannot be the rule.

## The chain

Every layer-1 event belongs to its own identity's chain: a per-identity sequence number (monotonic within that identity and unrelated to the global ledger sequence) plus a hash pointer to the previous event in that chain. In the ledger the position is stored inside the entry's payload under the reserved key `_identity_chain` (`{seq, prev_hash}`), so it is covered by the entry hash and reaches every mirror without a wire-format change. Kinds that do not participate (achievement issuance, integrator registration, `identity.created` itself, and the first passkey and inception signing-key events written at registration) carry no position. The chain does not verify who authored an event; an identity's key chain (the inception key derives the id, and each later key is signed in by an active key) is described in [the identity id](../identity.md#the-identity-id).

## The deterministic rule

The rule is pure logic with no I/O, so every node computes the same outcome from the same set of events:

- Two events that extend the same predecessor (same `seq`, same `prev_hash`) are concurrent.
- For an **ordinary edit** (profile field, friend action, joining or leaving a guild), the later signer-claimed timestamp wins, clamped against the receiving node's clock so a forged far-future timestamp is rejected. Ties break on the smaller event hash, so the outcome depends only on event content, never arrival order.
- Sequence number and previous-event hash, not timestamps, define ordering within a chain. A timestamp is signer-set data and is only ever a tiebreaker between genuinely concurrent branches.
- A **monotonic** action (a revocation, or a rollback compensating event) beats any ordinary edit at the same position regardless of timestamp.
- A conflict between two **chain-critical** events (signing-key add or revoke, any recovery step) is never resolved by timestamp, since that would let a forged timestamp win control of the identity. The identity is marked **forked** instead. Operations that depend on knowing which key controls the identity freeze until the owner resolves the fork through [social recovery](./recovery.md), which already authenticates a new credential through independent guardian approval plus a public delay.

Most layer-1 events (profile edits, friend actions, guild membership changes) are attributed by the node on the identity's behalf after a session requested them, and only some are signed by the identity's own key. The rule does not need an identity signature to work, because it depends only on the chain position and the action class. What differs is the threat model: a concurrent ordinary edit is normal (one person editing from two devices), while a chain-critical conflict is the case that must never be won by the later claimed timestamp.

## What is wired

- **Storage and emission.** Chain state is derived from events and is rebuilt with the other projections. Each write assigns its chain position in the same transaction as the write and its outbox entry. Chained kinds: profile update, friend requested/accepted/removed, guild member added/removed, passkey registered/revoked, signing key added/revoked, and every recovery step. Not chained yet: the rollback compensation events.
- **Convergence.** Every chained event, local or mirrored, is recorded and the chain is re-resolved over all recorded events, so the outcome depends only on the event set. A mirrored event whose timestamp is beyond the clock-skew bound is dropped. Only the **profile** projection consumes the outcome: a `profile.updated` not on the resolved chain is not applied, and when a winner displaces an applied loser the displaced events' optional fields are cleared and accepted events replayed in chain order (`display_name` is never reverted).
- **Fork and freeze.** While an identity is forked, signing-key and passkey changes and guardian reconfiguration return `409 IDENTITY_CHAIN_FORKED`. Recovery request, approval, and completion stay available because that is how the fork is resolved. An `identity.recovered` event that extends the last unforked head at the fork position, and is the only such candidate, wins the position and clears the fork on every node.

## What is not wired

- Convergence for the friendship, guild-roster, passkey, and signing-key projections. Their events are recorded so forks are detected, but a concurrent same-position conflict in those projections is not undone.
- Chain positions for rollback compensations and for events authored on behalf of another shard.
- SDK support. The shared conformance vectors for this rule (`identity-chain.json`) exist only in the protocol repository and have no vendored copy or implementation in the SDKs yet.

## Implementation

- Pure rule: [`identity_chain.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/identity_chain.rs), with wire glue in [`identity_chain_wire.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/identity_chain_wire.rs).
- Server entry points: [`crates/server/src/identity_chain.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/identity_chain.rs), with storage in the indexer crate.
- Vectors: [`conformance/vectors/identity-chain.json`](https://github.com/avalon-initiative/avalon-protocol/blob/main/conformance/vectors/identity-chain.json).

## Related

- [Identity](../identity.md), [recovery and rollback](./recovery.md)
- [Protocol events](../protocol-events.md), [synchronization](../../architecture/synchronization.md)
- [Witness cosigning](../witness-cosigning.md) for trust in the log itself, a separate question
