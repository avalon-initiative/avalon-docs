# ADR-0437: three-tier data-freshness policy — realtime push, poll, or stale-until-refetch

**Status:** Accepted — decided 2026-09-15

Original record: [avalon-protocol#437](https://github.com/avalon-initiative/avalon-protocol/issues/437). The text below is preserved as recorded; `#N` references are avalon-protocol issue numbers and file paths are as they were when the decision was made.

## Context

#119 (decided) chose WebSocket as the Hub's realtime transport specifically
because the roadmap already committed to bidirectional-push features —
guild chat (#24) and DMs (#105) — that the same transport would serve once
built, with presence riding on top of it rather than needing its own
mechanism. #136 implemented that transport, but only wired it up for
presence (`GET /ws/presence`). Guild chat (`useGuildChat.ts`) and DMs
(`useConversationThread.ts`) still poll every 15 seconds — a "milestone 1,
no WebSocket" placeholder noted in both files' own comments, never intended
to be the permanent design.

Separately, #389 and #432 have been auditing which Hub views go stale
without a manual reload and adding polling to fix each one found. That
pass never asked a prior question: does this view need to be live at all?
Not every stale view is a bug — a poll is the wrong fix for some of them,
and the wrong fix in the other direction is applying the still-unused
websocket transport to things that don't need it.

## Decision

Three tiers, applied per view/data type, replacing case-by-case judgment
calls:

1. **Must feel real-time** (a human is actively watching it change and a
   delay reads as broken — chat messages, DM messages, presence): push over
   the websocket transport #119/#136 already established. Extending it to
   chat/DM messages is tracked separately (see Related).
2. **Should update without a manual reload, but a few seconds/minutes of
   lag is fine** (list-shaped data someone isn't staring at continuously —
   friend list membership, guild roster/membership, guild list): poll on an
   interval, same pattern `useMyConnections`/`useMyGuilds`/`useGuildDetail`
   already use.
3. **Stale-until-next-visit is acceptable** (a view someone opens, reads,
   and navigates away from — another identity's profile, a discovery
   board, an achievements list, integration profile/consent): no refresh
   mechanism required. A one-shot fetch on mount, refreshed naturally the
   next time the view is opened, is correct behavior, not a bug — polling
   this tier is unnecessary client/server traffic for no perceptible
   benefit.

Tier 1 is transport (websocket); tier 2 is a poll; tier 3 is doing nothing
further. A view's tier is a product judgment call (how a person actually
uses that screen), not a technical default — when it's ambiguous, default
to tier 2 (poll) over tier 3, never default to tier 1 (push) without a
concrete reason the delay is user-visible and disruptive.

## Consequences

- Guild chat and DMs move from tier-2 polling to tier-1 push — a real gap
  against #119's original intent, tracked as its own implementation ticket
  (see Related) rather than folded into this ADR.
- #432's remaining views (discovery boards, integration profile/consent,
  other-user profiles) are tier 3, not tier 2 — they don't need the poll
  pattern #389 applied elsewhere; #432 should be re-scoped to reflect that
  rather than adding pollers to all of them.
- Friend/guild membership lists (`useMyConnections`, `useMyGuilds`,
  `useGuildDetail`) are correctly tier 2 already — no change needed there.
- Future work adding any new Hub view should classify it into one of these
  three tiers up front instead of defaulting to "fetch once" or "poll
  everything" by habit.

## Related

- #119 — original realtime-transport decision (decided: WebSocket).
- #136 — implemented the websocket transport for presence only.
- #389 — added polling to achievements/activity/friend-suggestions (tier-2
  precedent this ADR generalizes).
- #432 — Hub views still going stale; to be re-scoped against this ADR's
  tiers.
- Implementation ticket extending websocket push to guild chat/DMs (filed
  alongside this ADR).
