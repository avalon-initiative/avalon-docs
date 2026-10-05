# Guilds

**Status:** Implemented — with two gaps labeled below: no history read endpoint, and roster and event visibility scopes are still evolving.

An Avalon guild is a first-class primitive of the network, not of any game. It exists before its members enter a particular integrator, has members playing many integrators at once, and survives any one integrator shutting down. An integrator is a client of a guild, never its owner: membership, roles, permissions, and history belong to the network, and an integrator may render and consume them but cannot govern them with its integrator credentials. The decision is recorded in [ADR 0074](../architecture/decisions/0074-guilds-are-network-level-primitives-not-game-owned.md).

Detail is split into focused pages:

| Page | Covers |
| --- | --- |
| [Roles, permissions, and membership](./guilds/permissions-and-roles.md) | the permission vocabulary, per-resource overrides, role rules, invites, join requests |
| [Channels, chat, and events](./guilds/chat-and-events.md) | durable channel structure, non-durable messages and retention, scheduled events and RSVPs |
| [Discovery and integrator affinity](./guilds/discovery-and-affinity.md) | guild metadata, the discovery board, the derived integrator breakdown and favorites |

## Where guilds sit

```text
Avalon Network
│
├── Identities
├── Guilds
│   ├── Members, Roles, History, Chat
├── Achievements / Attestations
├── Integrators
└── Assets / Ownership (later phase)
```

Guilds are a sibling of integrators, not a child. The same guild can be seen from inside any integrator that renders it and from the Hub with none open:

```text
Dragon Hunters

Members: 1,284
Members currently playing:
    42 in Ashen Realms
    18 in WorldZero
     7 in Integrator C
```

Nothing above is integrator-scoped. The per-integrator counts are realtime [presence](./presence.md) and binding-derived data, not something any one integrator reports about "its" guild.

## What Avalon owns

| Concern | Owner | Notes |
| --- | --- | --- |
| Guild existence, name, tag, description | Network | `Guild` in the protocol crate |
| Guild metadata (message of the day, banner, icon, links, recruiting) | Network | editable by the owner or a holder of `manage_guild` |
| Membership | Network | joins, leaves, and removals are protocol events |
| Roles and permissions | Network | assigned by members with authority |
| Guild history | Network | append-only; membership and roster events are rebuilt from the ledger (see below) |
| Guild chat channels and messages | Network | delivered to any authorized client |
| Reputation, governance | Network | later; see [future layers](../architecture/future-layers.md) |
| An integrator's in-world rendering of a guild | Integrator | banners, halls, roster UI |
| Integrator-internal clans that never touch Avalon | Integrator | stay integrator-side entirely |

An integrator that wants purely internal clans keeps them in its own database. Avalon does not try to model every integrator-internal group.

## Integrator as client

"Join Dragon Hunters" inside an integrator calls Avalon social functionality. The membership change happens in the network layer and the integrator then consumes it. The only relationship between a guild and an integrator is `GuildIntegratorAssociation`: opt-in, many-to-many, non-owning, and removable without affecting the guild.

Through the association an integrator can render the roster and member presence (subject to [visibility](./privacy.md)), render guild chat in its own UI as a client of the channel, ask whether an identity is a member of guild X with role Y, and unlock integrator-side content based on membership. It cannot rename, dissolve, transfer, or govern a guild, remove members, or grant roles; those are guild-role authorizations, not integrator credentials. See the [security model](./security-model.md).

A guild's connection to an integrator is never declared by a manager for an integrator none of its members have played. It comes only from what integrators already know through [bindings](./bindings.md); see [discovery and integrator affinity](./guilds/discovery-and-affinity.md).

## Guild chat is a network primitive

A channel belongs to the guild. It is visible through the Hub, an integrator that chooses to render it, a web client, and later other authorized clients such as a Discord bridge. Users in different integrators talk in the same channel. Guild chat is not gameplay chat: integrators keep their own local chat, and Avalon carries the cross-integrator social channel. See [channels, chat, and events](./guilds/chat-and-events.md) and [communication](../architecture/communication.md).

## History versus current state

Membership history is durable protocol history and the roster is a projection.

```text
guild.created           Dragon Hunters, founder: Identity X
guild.member_added      Identity X (Leader)
guild.member_added      Identity Y (Member)
guild.role_changed      Identity Y -> Officer
guild.member_removed    Identity Y (left)

Current projection:  Dragon Hunters, Members: Identity X (Leader)
```

The history is reconstructable from [protocol events](./protocol-events.md); the roster is rebuilt from it by the [indexer](../architecture/query-and-indexing.md). These events are public ledger entries naming the member, whatever the guild's `roster_visibility` says: that setting gates the node API's roster read only (see [privacy](./privacy.md#what-the-ledger-makes-public)). That holds for membership and the roster. A guild's name and metadata, role definitions, channels, integrator associations and favorites are server-owned rows: their events are recorded for audit and mirroring but are not replayed, so a rebuild does not restore them and mirror nodes do not hold them ([query and indexing](../architecture/query-and-indexing.md#where-social-state-lives-today); open gap [avalon-protocol#1250](https://github.com/avalon-initiative/avalon-protocol/issues/1250)). **Gap:** the events are durable, but no `GET /guilds/{id}/history` endpoint or indexer read model exposes them to clients yet, so the Hub's history card says so plainly instead of fabricating a feed from the current roster.

## A user's main guild

A user may belong to several guilds, but an integrator building a guild-chat-style UI often wants one to default to. `main_guild` is a self-chosen pointer to one of the user's own current memberships. It lives on the identity's profile, not on the guild, and it never affects guild-side data: no guild is ever "the" main guild. Setting it is checked against a real fact (current membership) and it clears automatically if the user leaves that guild. `null` means unset, not "no guild": a caller wanting a default reads `effective_main_guild` from `GET /me`, computed at read time as the earliest-joined membership and never stored. See [identity](./identity.md) and the [aggregate view](./identity-aggregate-view.md).

## Analytics phrasing

Never describe network guilds as belonging to an integrator.

- Wrong, unless the guilds are explicitly integrator-owned: "Integrator A has 18,291 guilds."
- Right: "18,291 Avalon guild members are currently associated with Integrator A. 4,217 Avalon guilds have members who play Integrator A."

Metrics the [registry](./registry.md) may derive include guild members associated with an integrator, guilds with members playing an integrator, cross-integrator guild activity, and guilds spanning multiple integrators.

## Scenario H: a network guild

Can a guild exist outside Integrator A and have members playing Integrator A, B, and C at once? Yes, by construction: the guild has no integrator parent, members hold [bindings](./bindings.md) to whichever integrators they play, and presence reports where each member currently is. If Integrator A shuts down, the guild, its roster, channels, and history are unaffected; only the association with Integrator A becomes historical.

## Open questions

Roster and event visibility scopes remain an area of ongoing design beyond the current `public`, `view`, and `view_details` model. Ownership and leadership transfer beyond the current owner-transfer flow are open questions in the [design proposal](../architecture/design-proposal.md).

## Implementation

Status: implemented. Core types (`Guild`, `JoinPolicy`, `GuildRole`, `GuildMember`, `GuildIntegratorAssociation`, `GuildChannel`, `GuildMessage`, `GuildPermission`, `GuildEvent`) are in [`crates/protocol/src/guilds.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/guilds.rs). Handlers are in [`guilds.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/guilds.rs), [`channels.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/channels.rs), [`guild_messages.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/guild_messages.rs), and [`guild_events.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/guild_events.rs). Every guild route accepts an identity session only. The SDKs expose reading the caller's guilds, rosters, channels, messages, and events plus posting messages as the identity (never as the integrator); creating guilds, inviting, changing roles, and managing channels are identity-authority actions performed in first-party clients and are not exposed on the SDKs. The wire contract is in the [OpenAPI document](https://github.com/avalon-initiative/avalon-protocol/blob/main/docs/generated/openapi.json).

## Related

- [Identity](./identity.md), [social graph](./social-graph.md), [presence](./presence.md), [bindings](./bindings.md), [registry](./registry.md), [privacy](./privacy.md)
- [Protocol events](./protocol-events.md), [communication](../architecture/communication.md)
- [ADR 0074: guilds are network-level primitives](../architecture/decisions/0074-guilds-are-network-level-primitives-not-game-owned.md)
