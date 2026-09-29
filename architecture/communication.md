# Communication: Direct Messages, Voice, and Notifications

**Status:** Partially implemented — direct messages and guild chat delivery are implemented; voice is Undecided (deferred); server-pushed notifications are Planned

Avalon connects communities and does not replace the tools they already use. Guild chat is a network primitive: a channel belongs to the guild, not to any integrator, and is rendered by whichever client a member has open ([guilds](../protocol/guilds.md)). This page covers the remaining communication surfaces (direct and small-group conversations, voice, notifications) and the one rule across all of them: communication is realtime and query infrastructure, the same vertical presence occupies ([presence](../protocol/presence.md)), never settlement infrastructure.

## Decided elsewhere

- **Guild chat.** A channel and its messages belong to the guild; message bodies are explicitly not protocol history ([guilds](../protocol/guilds.md)).
- **Blocking.** Private, unilateral, server-side, and enforced against conversation sends ([social graph](../protocol/social-graph.md)).
- **Presence.** Ephemeral, never ledgered.

## Direct messages and small-group conversations

Implemented. A conversation is the identity-to-identity sibling of a guild channel: it exists between two or more identities with no guild in between, and no integrator owns it. The reasoning that makes a friendship and a guild network-level applies here: a conversation between two identities is a fact about their relationship, not about whichever integrator either was in when they started talking.

The hot and cold split that guild chat established carries over.

- A conversation and its messages are ordinary server state, not protocol events. They are high volume and non-interoperable, and no receiving integrator ever needs to verify them. Messages live in their own table outside settlement, and no message event kind exists.
- Retention is a configurable per-conversation cap (default 10,000 messages), keeping the newest and hard-deleting the rest. Conversation history is not permanent.
- Creating a conversation is idempotent on its exact participant set: asking again for the same identities, in any order, returns the existing conversation.
- **Relationship gate.** Every named participant must already be a friend or mutual guild member of the caller. This also closes an identity-existence oracle: a nonexistent id fails the check exactly as an existing, unrelated id does.
- **Blocking is enforced on send and on read**, across the whole participant set: a block between any two participants, not only the sender, rejects the operation. The rejection is identical to what a genuine non-participant gets, and the same two lookups always run, so a blocked party cannot distinguish being blocked and cannot use read/write asymmetry to confirm it.
- An integrator may render a conversation as a client of it, exactly as it may render a guild channel, and never becomes its host.
- Sending while offline is not this domain's problem: a message composed offline queues through the SDK's journal and submission engine like any deferrable operation ([synchronization](synchronization.md)). The UI pattern is a pending state until confirmed, never silent loss and never a false "delivered".

## Live delivery and replication

- **Live push.** A message WebSocket delivers new guild channel messages, deletions, and new conversation messages, authenticated with the session token. A single in-process broadcast is filtered per connection by what the client subscribed to. It is lossy on a slow consumer, and the paginated read is always there to reconcile against.
- **Cross-node relay.** Without relay, a guildmate on a different node never gets the live push. After the local publish, a node also posts once to every same-network peer advertising a realtime, gateway, or combined role. The receiving node feeds only its local fan-out, never its message tables, and never relays again, so no origin bookkeeping is needed; this relies on a small, fully interconnected mesh, which the DHT interest lookup narrows as the mesh grows ([distributed topology](distributed-topology.md)).
- **At-rest replication.** A separate concern, so that chat history survives a node's loss. After a send or delete, a node posts once to one deterministic target, the lexicographically smallest same-network peer advertising an indexer or combined role (a different eligibility from relay, since this is storage capacity). The target writes into its own replica tables, deliberately not the live tables, whose foreign keys reference data a replica may not hold. A deletion marks the replica row rather than removing it. Outcomes and lag are logged. A node with no eligible peer is unaffected.

## Voice

Undecided; deferred indefinitely. Text (guild chat, DMs) already covers the core cross-integrator communication goal, and voice is a materially larger, expensive-to-unwind infrastructure commitment (a self-hosted media server, or a third-party dependency the rest of the protocol has avoided). Revisit only when a concrete integration demands it. What is already clear:

- A voice session is realtime state, not durable history, never settlement.
- Sessions attach to the same two surfaces as conversations and guild channels: a guild voice room and a direct call.
- Authorization follows the same membership and capability checks as chat, with no separate authority model.
- Provider and protocol choice (a self-hosted media server, a third-party API, or WebRTC directly) is explicitly not decided and should not be inferred from any example elsewhere.

No voice module, session type, or transport exists.

## Notifications

A thin delivery concern, not a new domain: telling a connected client that a message arrived, a friend came online, or a guild event happened. It is not durable history in its own right; it is a signal about state that already lives in chat, presence, or guild history.

Implemented client-side slices:

- **Guild announcement alerts.** A read-only aggregate returns the most recent posts to announcement-only channels in guilds the caller currently belongs to, scoped by construction through a join on current membership, so nothing has to be torn down when someone leaves. Read and unread state is entirely client-local (a per-channel last-seen timestamp in the client's own storage), never server state, because nothing here is durable enough to track server-side.
- **A notification summary** in the Hub aggregates seven pending-action sources into one badge: incoming friend requests, guild join requests awaiting review, guild invites, device-grant approvals, recovery requests a guardian can approve, new guardian designations, and unread direct messages. It is a read-only aggregator over each source's own endpoint, not a server-side notification store. Sources with no accept or decline of their own use client-local seen tracking; the rest clear only when the item is resolved.

Planned: a true delivery mechanism (server-pushed, not client-polled), which should be a delivery layer on top of the realtime vertical, not a store of its own. Undecided and not built: alerts when a guild's message of the day changes, which risk being noisy rather than useful.

## Avalon is not Discord

Avalon's job is to make guild chat, DMs, and voice work the same way regardless of which integrator, if any, an identity has open. It is not to build a destination that identities go to instead of the tools they already use. A future Discord bridge is one more authorized client rendering the same network-owned channel, no different in kind from an integrator or the Hub rendering it. Nothing here scopes that bridge; it is named only so a future conversation or voice design does not paint itself into a Hub-only or integrator-only corner.

## Implementation

Status: as above. Conversations, message push, relay, and replication are implemented in the [server crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/server) of avalon-protocol, with source-scanning tests that guild and conversation messages never touch the ledger. SDK handles for message subscription are in [avalon-sdks](https://github.com/avalon-initiative/avalon-sdks), and the client-side notification code is in the [Hub repository](https://github.com/avalon-initiative/avalon-hub).

## Related

- [Synchronization](synchronization.md)
- [Guilds](../protocol/guilds.md), [social graph](../protocol/social-graph.md), [presence](../protocol/presence.md)
- [Distributed topology](distributed-topology.md)
- [ADR 0437](decisions/0437-three-tier-data-freshness-policy-realtime-push-poll-or.md) (data freshness tiers)
