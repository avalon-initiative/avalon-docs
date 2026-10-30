# ADR-1251: [Decision] How a signed event gets its identity-chain position

**Status:** Accepted — decided 2026-10-04

Original record: [avalon-protocol#1251](https://github.com/avalon-initiative/avalon-protocol/issues/1251). The text below is preserved as recorded; `#N` references are avalon-protocol issue numbers and file paths are as they were when the decision was made.

## Context

Link events (friends, guild roster) stay on the ledger and become actor-signed (#1223, #1216). Today each carries a position in its identity's chain (`seq` and `prev_hash`) that the authoring node assigns at write time (`assign_local` in `crates/indexer/src/identity_chain_store.rs`, from that node's own `identity_chain_state`); the actor does not sign it. #1214 found that the position sits outside every signature, so a hostile shard can replay a valid signed event with a conflicting position and fork the victim's chain, which freezes local authoring until recovery. v3 signing bytes are meant to cover the position.

If the actor's signature covers `seq` and `prev_hash`, the position can no longer be assigned by the node after the fact: the actor's client has to know the current head before it signs. The chain is designed for concurrent authoring on different nodes and devices (two nodes may accept different edits at the same position and the deterministic rule in `crates/protocol/src/identity_chain.rs` resolves or freezes), so the flow has to stay correct under races. A social-only host adds a case: it can only assign or check positions for an identity if it holds that identity's verified chain head (see the social verification slice).

## The question

How does a link event get a position that the actor's signature covers?

## Options

- **A. Client signs the position.** The client asks the host it talks to for the identity's current chain head, signs the event including `seq` and `prev_hash`, and submits. The host verifies the position is still the head and otherwise returns the new head so the client re-signs. Closes the replay and fork gap; needs a head-read route and a retry in every SDK.
- **B. Host assigns, actor signature excludes the position.** Keeps today's flow; the replay and fork gap of #1214 stays for these kinds.
- **C. Signature covers `prev_hash` only.** Position order is then implied by the hash link; weaker than A under concurrent authoring and needs a check that `seq` is derivable.
- **D. Do not chain link events.** Tie them to the pair or guild instead (a `friend.accepted` references its request id, roster events reference the guild), accepting weaker convergence for concurrent edits.

## Recommendation

A, with the existing conflict rule unchanged. It is the only option that makes the actor's signature the whole authority over a link event, and the head-read plus retry flow is the same shape the SDKs already use for nonces and grants.

## Questions

- Multi-device races and offline signing: how long may a signed event wait before its position is stale.
- Which identity chain head a social-only host serves and how it keeps it fresh.
- Whether recovery and reversal events (authored by the node on a recovery request) follow the same flow.

## Decision

Option A (maintainer, 2026-10-04). The signer binds the event to its place: the client fetches the identity's current chain head, signs the event including `seq` and `prev_hash`, and submits. The host verifies the position is still the head and otherwise returns the new head so the client re-signs.

- **One rule for every chained kind**, not only link events: profile, passkeys, friend and guild roster events, reversals, key and recovery events.
- Retries cost the user nothing: events are signed with the local Ed25519 key, not a passkey prompt. A client may sign a run of events chained to each other while offline.
- The conflict rules for genuinely concurrent branches are unchanged (timestamp tiebreak for ordinary edits, fork for key and recovery events).
- Reversal events written after a recovery are signed by the recovered identity (the rollback route already requires a fresh signature).
- The public chain-head read route is part of this decision (#1256).
- Who signs each kind of event is a separate decision (#1255).

## Alternatives considered

The options above.

## Consequences

Fixes the shape of the v3 signed forms for every chained kind, adds the head-read route to the OpenAPI document and the head-fetch, sign and retry flow to all three SDKs, and changes the server from assigning positions to verifying them for signed kinds. Unblocks the friend and roster slices.

## Related

Epic #1222, #1223, #1214, #1216, #1153.
