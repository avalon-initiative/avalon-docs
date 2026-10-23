# ADR-1299: [Decision] Permanence versus erasure: what the public ledger may hold and what a person can have removed

**Status:** Accepted — decided 2026-10-05

Original record: [avalon-protocol#1299](https://github.com/avalon-initiative/avalon-protocol/issues/1299). The text below is preserved as recorded; `#N` references are avalon-protocol issue numbers and file paths are as they were when the decision was made.

## Context

The ledger is append-only and mirrored by anyone, and retention only prunes payloads while skeleton rows stay forever (#1009 tiers). Content already or soon on it includes the friend graph and guild roster (decided to stay on the ledger and be public in #1223), display names in public events (#1125), identity creation and key events, attestations, and per-guild chains (#1252). A person, a guild owner or a hoster may be legally or personally entitled to have some of this removed, and there is no defined answer for what is possible once data has been mirrored.

What goes into signed ledger formats cannot change after the freeze (#1156), so this has to be decided before then.

## Decision

The ledger holds authority state in full (keys, membership, roles, links, revocations) and content as a commitment (hash, signer, chain position); the bytes of content may live off the ledger and are verified against the commitment. Identity profiles and guild metadata use one shared mechanism, a signed object with a nonce inside it so a commitment cannot be confirmed by guessing (#1313, #1314, #1315). The social graph stays public as ids only (#1223). Where free text is intrinsic (guild posts, guild descriptions, integrator-defined data) it stays inline and is removable: the entry commits to a hash of the payload (#1153), and a signed redaction by the author, or for guild content by a role holding the moderation permission, makes conforming nodes stop serving and drop the payload while the skeleton (hash, id, timestamp, signer) stays permanent (#1316). Redaction is monotonic and tombstone-first. This is best effort: a node that ignores the rule keeps a copy, crypto-erasure is a later layer if required, and no legal compliance claim is made. Setup states which parts are permanent and which are removable. Every ledger payload field is inventoried against this decision before the freeze (#1318).

## Alternatives considered

- Keep only hashes, commitments or pseudonymous ids on the ledger; hold anything personal in signed, erasable off-ledger objects.
- Encrypted payloads with a key that can be destroyed (crypto-erasure), while the skeleton remains verifiable.
- Accept permanence for defined kinds and document it clearly, with a pre-write notice and a reversal event (as for friend and membership reversal) that hides data from projections but does not remove it.

## Consequences

To be filled in once decided. Questions to settle: which kinds may carry personal data at all; how retention pruning (payload nulled, skeleton kept) interacts with erasure and with mirrors that never prune; what a "forget" request means for a peer's copy; what is stated to users before they create an identity.

## Related

#1009, #1125, #1156, #1223, #1252, #615.
