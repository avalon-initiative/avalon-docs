# ADR-0093: Avalon Operates Its Own Chain — No Native Currency at Launch

**Status:** Accepted — decided 2026-09-08 (superseded in part)

Original record: [avalon-protocol#93](https://github.com/avalon-initiative/avalon-protocol/issues/93). The text below is preserved as recorded; `#N` references are avalon-protocol issue numbers and file paths are as they were when the decision was made.

> Superseded in part by [ADR-0186](0186-no-blockchain-validator-consensus-transparency-log-only.md): the validator/BFT-consensus conclusion below was withdrawn and settlement is a transparency log. The decision that there is no native currency at launch stands.

## Context

ADR #70 decided the *shape* of durable settlement — a public, append-only,
cryptographically verifiable transparency log, not federation and not
mining-based consensus — but left open which of three backends actually
carries that log long term: anchoring checkpoints to an existing public chain,
a deeper partnership with one, or Avalon running its own. That question was
tracked as [#79](https://github.com/avalon-initiative/avalon-protocol/issues/79).

A chain Avalon doesn't operate ties every durable guarantee the protocol makes
— identity, attestations, guild history, provenance, all of it explicitly
promised to survive any single game or operator — to a third party's roadmap,
fee market, tokenomics, and continued existence. That is the wrong dependency
for infrastructure whose entire premise is outlasting any one participant.

## Decision

**Avalon operates its own chain.** Not an anchored log whose checkpoints are
published to someone else's chain, and not a deep integration built on top of
an existing chain's token or consensus. External anchoring stays available
later, purely as an optional second witness on top of an already-canonical
Avalon chain — never as the primary mechanism.

**No native currency or token at launch.** The chain settles protocol facts,
not value. Consensus among Avalon's own validators does not require a
stake-weighted or mined token — a permissioned set of registered, known node
operators reaching agreement via a Byzantine-fault-tolerant round is
sufficient, with no scarce asset underneath it. A native crypto-asset for
cross-game currency carryover remains an explicitly later, optional phase
(`Proposal.md` §15, §27), evaluated on its own against that section's risk
list (speculation, volatility, regulatory/AML/KYC exposure, minors) if and
when it's proposed — never a prerequisite for the chain existing, and not
pre-approved by this decision.

This does not reopen anything #70 already decided:

- **Not a reopening of the mining/consensus rejection.** #70 rejected mining
  and stake-weighted consensus because Avalon's writes are already
  unambiguous (each actor signs its own claim) and there's no scarce resource
  to referee. A permissioned validator set reaching BFT agreement on block
  order is not mining and needs no token — it's a different, no-currency
  answer to "who proposes the next block," not a walk-back of why mining was
  rejected.
- **Not a reopening of the federation rejection.** Every validator proposes
  into, and every mirror reads from, the same canonical chain. Visibility
  never depends on which validator or mirror a game happens to trust — the
  exact property that made federation wrong stays enforced here.

The concrete consensus mechanism and validator-admission model are not decided
here — that engineering work belongs to
[#40](https://github.com/avalon-initiative/avalon-protocol/issues/40), which still
needs its own research spike before it closes.

## Consequences

- `docs/architecture/settlement.md` states the backend as decided (a
  self-operated chain, no launch currency) rather than open.
- #40's scope grows to include validator/consensus design alongside the
  hash-chaining, Merkle, and signed-tree-head work it already owned.
- Milestone 1 is unaffected: `SettlementProvider` (`crates/chain`) stays the
  only boundary, and the current hash-chained Postgres ledger stays the
  implementation until the chain itself exists.
- Any future native-currency proposal is a separate decision, evaluated
  against `Proposal.md` §15 on its own merits.

## Related

Supersedes the open question in #79 (closed). Builds directly on #70. #40,
#38, #39, #68.
