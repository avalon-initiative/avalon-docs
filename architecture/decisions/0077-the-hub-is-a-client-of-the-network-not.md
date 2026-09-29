# ADR-0077: The Hub Is a Client of the Network, Not the Network

**Status:** Accepted — decided 2026-09-08

Original record: [avalon-protocol#77](https://github.com/avalon-initiative/avalon-protocol/issues/77). The text below is preserved as recorded; `#N` references are avalon-protocol issue numbers and file paths are as they were when the decision was made.

## Context

`crates/server/src/main.rs` already says the Hub is frontend-only "per the
decision" that it never becomes its own backend, and `Proposal.md` §6 describes the
Hub as the first convenient client rather than the product. That decision was never
recorded. It matters because the Hub is the first thing built and the easiest place
to accidentally grow a privileged data path: a Hub-only endpoint, a Hub-only
database view, a "the Hub is trusted" shortcut. Once that exists, every other
client is second-class and Avalon has quietly become a platform.

## Decision

The Avalon Hub (`apps/hub`, `apps/mobile-hub`) is a client of the network. It is not
the network.

- The Hub talks to `avalon-server` through the same API, authentication, and
  capability model as any game or third-party client. There are no Hub-only
  endpoints, no Hub-only read paths, and no privileged Hub credential.
- The Hub never gets its own backend. Anything the Hub needs that the server
  doesn't provide is a ticket against `avalon-server`, filed and built first.
- Anything the Hub can do, another authorized client can do: a web client, a
  mobile client, a desktop client, a Discord integration, a game's native UI, or a
  third-party application.
- The Hub is the network's front door — identity creation and management, profile,
  friends, guilds and guild chat, achievements and history, game discovery,
  permissions, connected games — and it is where a player interacts with the
  network outside of any game. It is not a launcher, a store, or a game platform,
  and it does not own the games it lists.
- The Hub shows a player's authentic, valid claims with their provenance regardless
  of which games recognize them. It supports filtering, sorting, hiding, and
  featuring. It never implies Avalon has judged one issuer's claim more prestigious
  than another's.

## Consequences

- No `apps/hub/server`, no server-side rendering that reaches into Postgres, no
  Hub-scoped tables.
- Hub epics (#54, #59) depend on server epics; a Hub ticket without a corresponding
  server capability is blocked, not worked around.
- `packages/ui` stays a component library for clients; it has no knowledge of
  storage or settlement.
- A future game-discovery view in the Hub renders registry facts with their
  definitions and labels (durable-derived vs realtime vs self-reported) and shows
  no composite score.
- `docs/architecture/hub.md` is normative.

## Related

#54, #59, #90, #76
