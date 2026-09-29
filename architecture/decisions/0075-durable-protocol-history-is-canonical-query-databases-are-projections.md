# ADR-0075: Durable Protocol History Is Canonical; Query Databases Are Projections

**Status:** Accepted — decided 2026-09-08

Original record: [avalon-protocol#75](https://github.com/avalon-initiative/avalon-protocol/issues/75). The text below is preserved as recorded; `#N` references are avalon-protocol issue numbers and file paths are as they were when the decision was made.

## Context

Two kinds of storage exist today: the hash-chained `ledger_entries` table owned by
`avalon-chain`, and the ordinary application tables (`identities`, `profiles`,
`credentials`, `sessions`) owned by `avalon-server`. `avalon-indexer` defines an
`Indexer` trait whose `rebuild` replays events into a read model. Without an
explicit rule, the mutable application rows quietly become the authority for facts
Avalon promises to preserve, and "rebuild from history" becomes something the code
claims rather than something it can do. `update_profile` already writes only to
Postgres with no protocol event, so a profile is not currently reconstructable.

The forcing question: **if every Postgres database in the network disappeared, what
could Avalon rebuild, and from what?**

## Decision

For every fact Avalon promises to preserve, the canonical record is a durable
protocol event in the settlement layer. Every query database is a projection of
that history.

- **Promised-durable state must be reconstructable from protocol history.** This
  includes identity existence and its promised metadata, game and issuer
  registration, key lifecycle, achievement issuance and revocation, guild
  creation/membership/role history, game event results, and, later, ownership and
  provenance.
- **Postgres is an optimized representation, not the source of truth.** A table is
  a projection that `Indexer::rebuild` can regenerate. Nothing outside the
  settlement store is authoritative for promised-durable facts.
- **History is append-only.** A correction, revocation, supersession, or suspension
  is a new entry that references the earlier one. History is never edited or
  deleted to make an earlier fact disappear. A mutable "revoked" column on the
  original record is a projection convenience, never the record itself.
- **Every write path that changes promised-durable state emits its protocol event
  in the same unit of work as the projection change.** An identity that exists in
  a table but not in history is a bug, not a simplification.
- **State Avalon does not promise durable is exempt, and must be explicitly
  classified.** Presence, sessions, typing indicators, ephemeral chat delivery
  state, and caches are not protocol events and are not in rebuild scope.
- **Not every convenience field enters durable history.** Anything derivable from
  other events is derived by the indexer, not stored twice.

## Consequences

- #71 (identity creation and its ledger entry aren't atomic) is the first instance
  of the "same unit of work" rule and needs a real outbox or equivalent, because
  every future write path (social, guilds, achievements) has the same shape.
- Profile updates need a `profile.updated` event and a decision on which profile
  fields are promised durable — #86 (Epic #2).
- Event kinds and payloads need an explicit catalogue and versioning policy before
  more of them are emitted — #82 (Epic #36).
- #43 (rebuild-from-events + idempotency) is a required integration test, not a
  nice-to-have: drop the projection tables, replay history, compare.
- `AchievementAttestation.revoked_at` as a mutable field is a violation of the
  append-only rule and is replaced by revocation entries — see the revocation
  decision under Epic #30.
- `docs/architecture/protocol-events.md`, `query-and-indexing.md`, and
  `disaster-recovery.md` carry the normative detail.

## Related

#71, #43, #86, #82, #81, #85, #68, #70
