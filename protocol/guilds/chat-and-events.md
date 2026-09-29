# Guild Channels, Chat, and Events

**Status:** Implemented

A guild has chat channels and scheduled events. Channel structure is durable protocol history, but the messages inside channels and the guild events themselves are deliberately "hot state" that never touches the ledger. This page states what is durable, what is not, and the retention rules. The concept is in [guilds](../guilds.md).

## Channels

Channel structure (create, rename, archive) is durable history: `guild.channel_created`, `guild.channel_renamed`, and `guild.channel_archived` are written in the same transaction as the row change, gated on `manage_channels`. Every guild is seeded with a `general` channel. A channel can be:

- **announcement-only**: posting then requires the `channel_post` permission for that channel (through the override layer) instead of "any current member may post". No role holds `channel_post` in its base list by default.
- given a **topic**: a short line up to 200 characters, never stored empty.
- **public**: non-members of a public guild can read a public channel, following the same rules as events.

## Messages are not durable

Individual chat messages never touch the outbox or the ledger, the same treatment given to [presence](../presence.md). This is enforced by construction (the messages module does not import the outbox or settlement code, and a test checks it). Erasing message content is therefore realistic and works today, unlike ledger-authored facts (see [privacy](../privacy.md#erasure-versus-permanence)).

**Retention.** Messages are kept up to a per-channel cap (10,000 by default, configurable); beyond it the oldest move to an archive table instead of being deleted. The archive is held for a separately configurable window (730 days by default), after which a background worker hard-deletes it, with nothing recoverable afterward. No client should assume guild chat history is permanent. Reading the archive requires current guild membership, not membership at the time of sending, because the roster is a live projection with no point-in-time history. Moderators (`manage_channels`) can hard-delete a message outright, in the live table or the archive, so a takedown for cause is not defeated by cap-based archiving.

**Survives a node's loss.** Channel messages are asynchronously replicated to at least one additional node beyond the one that received the write, into a separate replica table; see [communication](../../architecture/communication.md).

## Events and RSVPs

A guild plans things (raid nights, meetups, tournament prep) regardless of which integrator members have open. A guild event is scheduling something upcoming, which is distinct from an integrator event result attestation, a durable claim issued after the fact (see [cross-integrator events](../cross-integrator-events.md)).

- **Durability.** Guild events and RSVPs get no protocol event kind at all. Rescheduling and cancelling is churn not worth preserving forever, the same reasoning as chat. Deleting an event is a hard delete that cascades to its RSVPs.
- **Authority.** Creating, rescheduling, and deleting require `event_manage`. RSVPing is self-service and idempotent: a member can only set their own status, which replaces any prior one.
- **Reads.** Listing and RSVPing require current membership. The event list carries aggregate `rsvp_counts` and the caller's own `my_rsvp`; a separate roster endpoint returns each member's status to members only.
- **Visibility.** Each event has a `public` flag (default false). A non-member of a public guild sees only that guild's public events. Among members, a `view` or `view_details` override can hide an event or strip its content: a stripped event returns `details_visible: false` with placeholder description, channel, and RSVP data while its title and time stay real.

## Implementation

Status: implemented. [`channels.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/channels.rs), [`guild_messages.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/guild_messages.rs), and [`guild_events.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/guild_events.rs). The retention settings are hoster configuration, documented with the server.

## Related

- [Guilds](../guilds.md), [roles, permissions, and membership](./permissions-and-roles.md)
- [Communication](../../architecture/communication.md), [presence](../presence.md), [protocol events](../protocol-events.md)
