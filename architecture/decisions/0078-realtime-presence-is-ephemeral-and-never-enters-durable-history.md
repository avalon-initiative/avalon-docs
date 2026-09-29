# ADR-0078: Realtime Presence Is Ephemeral and Never Enters Durable History

**Status:** Accepted — decided 2026-09-08

Original record: [avalon-protocol#78](https://github.com/avalon-initiative/avalon-protocol/issues/78). The text below is preserved as recorded; `#N` references are avalon-protocol issue numbers and file paths are as they were when the decision was made.

## Context

`crates/protocol/src/social.rs` defines `Presence` (status, current game,
`updated_at`), and #16 plans a presence-tracking endpoint. The temptation once a
durable ledger exists is to treat everything the server knows as protocol history.
Presence is the clearest case where that is wrong: "Player X is currently online in
Ashen Realms" is a different kind of fact from "Player X defeated the Dragon Lord",
and recording heartbeats in an append-only log would make the log useless for the
facts it exists to preserve.

## Decision

Realtime presence is ephemeral state. It never enters durable protocol history.

- Presence covers: online/away/offline, current game, current server or region,
  current activity, heartbeat, and temporary connection state.
- Presence is not a protocol event, is never written to the settlement store, and
  is not in rebuild scope. If presence storage is lost, players appear offline
  until their next heartbeat, and nothing is broken.
- Presence may live wherever ephemeral state belongs: in-process memory, a cache,
  or a dedicated realtime service. It is not required to be in Postgres at all.
- Presence is permissioned. A player controls who can see it (friends, guild,
  specific games via capability grant, nobody). Publishing presence to a game
  requires the relevant capability; reading a player's presence requires
  visibility.
- Realtime population numbers ("players currently online in Game A") are labeled
  as realtime wherever they are shown. They are never presented as durable protocol
  facts and never feed a durable metric.
- Realtime/presence is the third logical vertical alongside settlement and
  query/indexing. Milestone 1 runs it inside `avalon-server`; it can be split into
  its own process later without touching settlement or indexing, and this decision
  is what keeps that split possible.

## Consequences

- #16 stores presence outside `ledger_entries` and outside any table the indexer
  rebuilds. It emits no `ProtocolEvent`.
- Friends-list and guild-roster views (#18, #24, #56, #57, #61) read presence
  through a path that honors visibility scopes.
- The game registry reports "players currently online" separately from derived
  durable metrics, with the realtime label.
- What *is* durable about presence-adjacent activity — e.g. a game binding being
  established — is modeled as its own protocol event, not inferred from presence.
- `docs/architecture/presence.md` is normative.

## Related

#16, #87, #89, #14
