# ADR-0074: Guilds Are Network-Level Primitives, Not Game-Owned

**Status:** Accepted — decided 2026-09-08

Original record: [avalon-protocol#74](https://github.com/avalon-initiative/avalon-protocol/issues/74). The text below is preserved as recorded; `#N` references are avalon-protocol issue numbers and file paths are as they were when the decision was made.

## Context

`crates/protocol/src/guilds.rs` already models a guild as a network entity with an
opt-in, non-owning `GuildGameAssociation`, and `docs/Proposal.md` §10 describes
guilds as existing independently of any game. Nothing records that as a decision,
and the failure mode is easy to fall into: a game integration treats "guild" as its
own table with an Avalon mirror, or a Hub feature is written as if a guild belongs
to the game its founder was playing at the time. Once a game-owned guild model gets
built against, it can't be undone without breaking every integration.

## Decision

An Avalon guild is a first-class primitive of the network, not of any game:

- A guild exists independently of every game. It can be created before any of its
  members enter a particular game, and it survives any game shutting down.
- A game is a **client** of a guild, never its owner. A game may render a guild's
  roster, show member presence, and display guild chat in its own UI, and it may
  consume membership ("is this player in Dragon Hunters?"). It cannot rename,
  dissolve, or govern a guild through its game authority; only the guild's own
  members with the appropriate roles can.
- `GuildGameAssociation` is the only relationship between a guild and a game. It is
  opt-in, many-to-many, non-owning, and removable without affecting the guild.
- Guild creation, membership changes, and role changes are durable protocol events.
  Guild history is reconstructable; current roster is a projection.
- Guild chat is a network primitive delivered to any authorized client (Hub,
  mobile-hub, a game, a future Discord bridge). A game rendering guild chat is a
  client of the channel, not its host.
- Analytics never describe network guilds as belonging to a game. "Game A has
  18,291 guilds" is wrong unless those are explicitly game-owned. The correct
  shapes are "N Avalon guild members are associated with Game A" and "N Avalon
  guilds have members who play Game A".

Games that want purely internal clans keep them game-side and don't put them on
Avalon at all. Avalon doesn't try to model every in-game group.

## Consequences

- Epic #19 (Guilds & Guild Communication, #20–#24) builds against this model: guild
  CRUD/roles/membership/channels are `avalon-server` endpoints authorized by guild
  roles, not by game credentials.
- Guild membership needs a visibility scope (guild-visible, friends, public) rather
  than being implicitly public — #87.
- The registry/network-intelligence layer reports guild metrics only in the
  association phrasing above.
- `docs/architecture/guilds.md` is the normative description; `Proposal.md` §10
  stays the narrative.

## Related

#19, #20, #21, #22, #24, #87, #75
