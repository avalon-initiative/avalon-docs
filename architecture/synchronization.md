# Synchronization: Offline and Deferred Participation

**Status:** Partially implemented — a durable journal and a deferred-submission engine exist in the Rust SDK and are wired end to end for one operation kind; no automatic offline path exists

Avalon connectivity should be eventually available, not continuously required. A game stays playable, and able to keep recording what its user is doing, when Avalon is unreachable: a single-player integrator, a handheld with no signal, or a temporary outage. The SDK owns this complexity, not each developer.

The other half is equally load-bearing: an offline, client-generated event must never carry the same trust guarantees as an authoritative online issuer unless the protocol explicitly says so. A user who can edit a local pending-events file must never turn that into an accepted, authoritative claim. The convenience half of this page is inert without the trust half.

## A cross-cutting SDK capability

The same problem (record something locally, submit it later, do not manufacture trust while doing so) appears for achievements, guild membership requests, friend requests, and direct messages ([communication](communication.md)). Solving it once, as an SDK capability every feature reuses, is the point. A feature that invents its own offline queue is a bug.

```text
Avalon SDK
├── Identity
├── Social
├── Achievements
├── Communication
└── Synchronization
      ├── Local durable journal
      ├── Deferred submission (retry, backoff, idempotency, ordering)
      ├── Reconciliation
      └── Sync status (pending / submitted / rejected)
```

The intended developer experience is one call, online or offline, with no branch in the integrator's code for "internet available". Planned: that single-call convenience. Today the mechanism is driven explicitly (see below).

## Not every operation can defer

Some things need a live round trip by nature. This table is the authoritative classification that every operation refers to.

| Operation | Offline? | Behavior |
| --- | --- | --- |
| Read cached profile, roster, or friends list | Yes | Serve from local cache and label staleness |
| Integrator-local achievement earned | Yes, queued | Recorded locally; see below for what it is worth before submission |
| Chat or conversation message | Yes, queued | Stored `pending`; the UI shows it, never silent loss |
| Friend request or accept | Deferred, queued | Submitted on reconnect; may be rejected on reconciliation |
| Guild join or leave request | Deferred, queued | A request, not a grant; nothing is true until confirmed |
| Presence update | No | Meaningless without a live connection |
| Voice | No | Requires a live connection |
| Asset transfer (Planned, future) | No, or special | Contested shared state; needs its own design |
| Permission grant or revoke | No | Authorization changes must be authoritative immediately |

## What does an offline claim prove

An offline single-player game has no live server to attest anything while disconnected, but its client could still record "the user defeated the dragon". Treating that queued claim as equivalent to a normal issuer attestation the moment it is submitted is a real hole. It implies the integrator's live issuer signing key exists where the client can reach it, and a key reachable from a shipped client can be extracted. Whoever extracts it can forge arbitrary achievements for any user, retroactively, and rotating the key afterward does not invalidate what already verifies against its old validity window.

This is the [trust model](../protocol/trust-model.md) applied to a new axis: how a claim came to exist changes what a receiving integrator should believe even when the signature checks out. The decided answer is deferred requests, not deferred attestations. The offline period queues an unsigned local record of intent, not a valid attestation; no issuer key exists client-side at all. On reconnect the request goes to the integrator's own server, which decides whether to believe its client's record and only then issues a normal, fully authoritative attestation through the existing online path.

This adds no new key material and does not expand what a compromised client can forge. The alternative considered and rejected as the default is a distinct, lower-trust issuer variant with a separate lower-privilege key embedded client-side. Some integrators with no server of their own may still want it later, but it is a strictly larger and riskier addition. Whether to offer it is Undecided.

## Mechanism

- **Local durable journal.** A crash-safe local store behind an interface, so each SDK can back it with what suits the platform. Every entry has a client-generated stable id, the idempotency key everything downstream depends on. The Rust SDK's reference implementation is an append-only, fsynced JSON-lines file with no extra dependencies: crash safety needs only that a fsynced append fully lands or does not, and recovery replays the file and stops at the first line that does not parse. It has no concurrent-writer story and replays in O(n) on open, which does not matter for one client's local journal.
- **Deferred submission.** An engine drains pending entries grouped by kind, oldest first within each kind; ordering across kinds is neither guaranteed nor meaningful. Each entry is submitted through a transport that classifies the result as exactly one of: applied; rejected (terminal, a 4xx meaning the request itself is now invalid); retryable (network error, 5xx, or 429, rescheduled with capped exponential backoff kept in memory per entry, so a restart resets it); authentication required; or unsupported kind (left pending, untouched). The integrator calls drain from whatever loop or reconnect hook it wants, so draining never blocks gameplay.
  - A `401` is not a terminal rejection. A stale session is recoverable by re-authenticating, unlike an invalid request, so the entry stays pending with no backoff and the caller learns it must re-authenticate. Without this, messages queued offline and drained with an expired token would all be permanently discarded.
  - A `403` on conversation send stays terminal: it means not a participant or blocked, deliberately indistinguishable, and nothing about it changes on its own.
  - A `404` on the idempotent send is treated as applied: with the client entry id always set, it can only mean an earlier attempt landed and its row was later pruned by normal message-cap behavior.
- **Reconciliation.** A submission can be rejected because the world moved on while it was pending (a guild disbanded, the sender was blocked). This surfaces as an explicit rejected outcome with a reason, never silently dropped and never retried forever. A rejected entry leaves the pending set like an applied one, but is a distinct terminal state so it stays distinguishable.
- **Sync status.** Local read-only status (pending count, oldest pending, last synced, and per-entry pending, submitted, or rejected) plus a synchronous in-process callback fired once per terminal transition, so an integrator can render a "pending" message like any other state.

Idempotency on the server side means retries do not duplicate. For conversation messages the client entry id is carried through and a partial unique index on the conversation and entry id makes a conflicting insert return the already-landed row. A message sent directly online never sets an entry id and never dedupes against anything. The server's own outbox is the same durable-record-then-retry pattern applied to settlement on an always-online machine.

## What this is not

- Not a general offline mode for gameplay. Hot gameplay state was never Avalon's concern, online or offline; this is strictly about the durable, interoperable facts Avalon already handles.
- Not a way around the trust model. Deferring when something reaches Avalon never changes what it is allowed to claim about itself.
- Not yet a one-call wrapper. No client method appends to the journal on its own or drains it on the integrator's behalf. That convenience is Planned SDK work.

## Implementation

Status: Partially implemented, per SDK.

| Piece | Rust | C# | TypeScript |
| --- | --- | --- | --- |
| Local journal (file-backed reference) | Yes | Yes | No |
| Deferred-submission engine and transport | Yes | No | No |
| Sync status and transition callback | Yes | No | No |
| Wired end to end for | conversation messages only | n/a | n/a |

Friend requests and guild join requests are classified as offline-capable above but are not yet wired: the transport leaves any other kind pending, untouched, as an unsupported kind. The Rust SDK is in [avalon-sdks](https://github.com/avalon-initiative/avalon-sdks/tree/main/languages/rust) and the server-side idempotency is in [avalon-protocol](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/server). Per-language details belong with each SDK.

## Related

- [Communication](communication.md)
- [Trust model](../protocol/trust-model.md)
- [SDK design](../sdk/design.md)
- [Settlement](settlement.md) (the server-side outbox)
