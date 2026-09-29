# Disaster Recovery

**Status:** Implemented — projection rebuild is proven; snapshot-based rebuild is not built

Assume every PostgreSQL database in the Avalon network disappears. Everything Avalon promises to preserve durably must have a canonical, reconstructable representation in durable protocol history. That does not mean every row lives in settlement; it means every promised fact does, and every table is rebuildable from those facts.

This page lists what must be reconstructable, the rebuild procedure, and the limits that remain.

## What must be reconstructable

| Promised durable, must rebuild from history | Source events |
| --- | --- |
| identity existence and the metadata Avalon promises (display name, avatar) | `identity.created`, `profile.updated` |
| integrator bindings | `game.binding_*` |
| integrator and issuer registrations | `game.registered`, `issuer.registered` |
| issuer key lifecycle and status | `issuer.key_*`, `issuer.suspended`, `.reinstated`, `.revoked` |
| achievement definitions, issuance, revocation, supersession | `achievement.*`, `attestation.superseded` |
| guild existence, membership history, roles, integrator associations | `guild.*` |
| integrator event results | `game_event.result_issued` |
| recognition relationships | `recognition.published` |
| ownership and provenance (Planned, later phase) | asset events, when they exist |

| Not promised, need not rebuild | Where it lives |
| --- | --- |
| typing indicators, ephemeral chat delivery state | realtime, in memory |
| connection state, heartbeats, current presence | realtime ([presence](../protocol/presence.md)) |
| sessions and login credentials | server-local tables, never the log |
| caches, derived aggregates | recomputed by the indexer |

Anything lost from the second table means, at worst, identities appear offline and have to log in again. Anything in the first table that cannot be rebuilt is a broken promise.

## The rebuild procedure

```text
1. Obtain the log        from the operator's settlement store or any mirror
2. Verify the chain      rehash every entry, check every link, every signature
                         and tree head
3. Replay                rebuild the indexer from genesis, in order
4. Compare               projections match a known-good snapshot, or, with no
                         snapshot, satisfy invariants (every identity has a
                         creation event, every attestation an issuer, ...)
```

Step 3 is why indexer `apply` must be idempotent ([query and indexing](query-and-indexing.md)). Step 4 is proven, not only designed, by an automated rebuild-and-diff test. Rebuild time is a scaling dimension in its own right ([scalability](scalability.md)): a log that takes a week to replay is technically recoverable and practically not.

## Scenario J: PostgreSQL disappears

Can durable projections be reconstructed? Yes. The rebuild command truncates every projection table and replays the entire ledger back through the indexer in one transaction, so a failure partway leaves the pre-rebuild database untouched rather than half rebuilt.

A live test drives real registration, profile-update, friend, and guild actions through the actual HTTP ceremony, rebuilds, and diffs. Profiles are compared byte for byte against their pre-rebuild state; friendship and guild-member projections are asserted to match what the actions should produce; and replaying the same history twice produces an identical snapshot. A guild's owner is folded into the members projection on `guild.created` so there is no gap between an owner and other members. A second, end-to-end test drives the identity, friends, guild, channel, and achievement slice through real HTTP and SDK calls, runs the rebuild command, and re-asserts the reads a Hub page would make, proving the guarantee holds for what a real client depends on.

Identity creation is atomic with its ledger entry: the `identity.created` event is inserted into the outbox in the same transaction as the identity, profile, and key rows, so a crash before the ledger sees it cannot orphan an identity. Profile updates follow the same path, and `identity.created` carries the initial display name, so profiles are fully reconstructable. A defensive edge case (a profile update with no matching creation event) cannot occur through the real API and is skipped with a logged warning rather than fabricating a placeholder row.

## Known limitations

- **Passkey counter and backup state are not reconstructable.** A rebuild restores the identity, its signing public key, and every event it signed, but the WebAuthn passkey's clone-detection counter lives only in Postgres. Accepted trade-off: the counter resets to a fresh baseline, a minor security regression rather than a correctness one.
- **The ledger and the app tables share one database.** Losing Postgres today loses that node's copy of the log too. Mirrors are what make "obtain the log" possible against something other than the same database ([mirroring](settlement/mirroring.md)). A formal export format is Undecided.
- **Step 1 is not full-replay-only for the commitment layer.** The latest signed tree head is a checkpoint a node can trust instead of rehashing every entry ([retention and growth](settlement/retention-and-growth.md#settlement-state-checkpoint)). This does not yet extend to steps 3 and 4: no projection snapshot format exists, so rebuilding the read model is a full replay from genesis. Planned.

## Implementation

Status: Implemented. The rebuild command, the indexer's replay, and ledger re-verification are in [avalon-protocol](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates); the live rebuild tests are in its server and CLI crates. The schema-reset tool used for local development is not a recovery tool.

## Related

- [Query and indexing](query-and-indexing.md)
- [Settlement](settlement.md), [mirroring](settlement/mirroring.md)
- [Scalability](scalability.md)
- [Protocol events](../protocol/protocol-events.md)
