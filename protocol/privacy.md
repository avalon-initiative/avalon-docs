# Privacy and Visibility

**Status:** Partially implemented — visibility settings are built for presence and guild rosters and govern only what a node's API returns. The ledger is public: friend, guild-membership, binding, grant, profile, and achievement events are committed with their payloads and are readable without authentication. The general per-resource scope model is Proposed for the other resources.

Every node API read path names the visibility scope it checks, and network analytics are aggregates, never per-identity data. Those scopes do not reach the ledger: Avalon's ledger is a public transparency log, and several durable facts about an identity, including its friendships and guild memberships, are committed to it with their payloads. This page covers who can see what an identity has done within Avalon, and states what a visibility setting does and does not control. That is a separate and prior question from whether an Avalon identity ties back to a real person, which it does not; see [identity](./identity.md#what-identity-is-not).

## What the ledger makes public

The settlement ledger is public by design ([settlement](../architecture/settlement.md)). `GET /ledger/entries` is unauthenticated on every node that serves the ledger, including mirrors. It pages every entry after `since_seq` (up to 1000 per call) and can filter on the exact `subject` string, which includes the event verb, for example `identity:<id>:self:friend_requested` or `guild:<id>:self:guild_member_added`. Each entry returns its kind, issuer, subject, timestamp, and the full payload. Nothing in that path consults a visibility setting, and the filter is a convenience: an unfiltered read returns the same entries.

Events about friends and guild membership that are committed with these payload fields:

| Event | Payload fields on the ledger |
| --- | --- |
| `friend.requested` | `from`, `to`, `actor` (issuer is the requester, subject is the recipient) |
| `friend.accepted` | `from`, `to`, `actor` |
| `friend.removed` | `a`, `b`, `actor` |
| `friend.relationship_reversed` | `reverses_event_id`, `recovery_request_id`, `identity_id`, `counterparty_id`, `effect` |
| `guild.created` | `guild_id`, `name`, `tag`, `description`, `owner` |
| `guild.updated` | every guild setting, including `public`, `recruiting`, `join_policy`, `roster_visibility`, and `actor` |
| `guild.member_added` | `guild_id`, `identity_id` (the member), `role_index`, `via`, `actor` |
| `guild.member_removed` | `guild_id`, `identity_id`, `reason`, `actor` |
| `guild.role_changed` | `guild_id`, `identity_id`, `role_index`, `actor` |
| `guild.owner_transferred` | `guild_id`, `from`, `to` |
| `guild.membership_reversed` | `reverses_event_id`, `recovery_request_id`, `guild_id`, `identity_id`, `effect`, `role_index` |

Other public events concern the same identity: `profile.updated` (including `display_name`, `bio`, `pronouns`, `status`, `location`, `timezone`, `links`, and `main_guild`), `game.binding_established` and `game.binding_ended` (`identity_id`, `game_id`, `slug`), `permission.granted` and `permission.revoked` (including the `capability`), and `achievement.issued` and `milestone.issued` (including the issuer's `evidence`). The [event catalogue](./protocol-events-catalogue.md) lists every kind. Blocks, presence, and chat message bodies have no event kind and never reach the ledger.

What this means for a person:

- **A friends list and a guild roster are reconstructable from the public ledger.** The friend and membership events above name both identities, so anyone can rebuild who is friends with whom and who is in which guild, whatever the node API would return to them. A guild's `roster_visibility` setting and an identity's presence setting change what the node API returns, not what is on the ledger or on any mirror.
- **Visibility settings govern node API responses only.** They apply to the node that serves the request and are identity state, not durable history.
- **Committed data is permanent.** No API route removes or edits a committed entry, and mirrors keep their own verified copies. See [erasure versus permanence](#erasure-versus-permanence).
- **A pending friend request is also on the ledger.** `friend.requested` is committed when a request is sent, before anyone accepts it.

Planned: nothing has been decided yet about keeping friend and membership payloads off the public ledger (for example by committing a commitment instead of the payload). Until a decision lands, treat these facts as public.

## Scopes

These scopes decide what the node API returns to a viewer. They do not apply to the ledger entries above.

| Scope | Who can see | State |
| --- | --- | --- |
| public | anyone, including unauthenticated readers of a mirror | implemented |
| authenticated-only | any Avalon identity | implemented |
| friend-visible | identities in the subject's friends list | implemented |
| guild-visible | members of a given guild | implemented |
| integrator-visible | an integrator holding the relevant capability under an active binding | Planned for reads; see [security model](./security-model.md#authorization-one-capability-one-check) |
| private | the subject only | implemented |
| operator-only | node operators, for diagnostics; never surfaced through the API | not modeled as a scope |

A scope is meant to apply per resource: profile fields, presence, friends list, guild membership list, achievement history (with per-claim hide or feature on top). Guilds also set a policy on their own roster (public, members-only, private). Only presence and guild rosters have a built scope today.

## Composition

An integrator's capability grant never widens what non-integrator viewers can see, and a public visibility setting never grants an integrator a capability it was not given. For a read by an integrator the order is: active [binding](./bindings.md), active `PermissionGrant` for the specific capability, then visibility scope. For a read by a person: relationship to the subject, then visibility scope. One shared authorization helper answers (viewer, subject, resource), and no endpoint does its own ad-hoc check.

## Defaults

Settings are user-controlled and changeable through the API and, for some, the Hub.

| Resource | Default | State |
| --- | --- | --- |
| display name | public | implemented |
| avatar | public | implemented |
| presence | friends | implemented, changeable by the identity |
| guild roster | node API: guild members (a `public` guild is readable by any authenticated identity). Ledger: member events are public | node API scope implemented and changeable by the guild; ledger exposure implemented |
| friends list | node API: no endpoint returns another identity's list. Ledger: public (see above) | Proposed as a scope; the ledger exposure is implemented |
| achievement history | public on the ledger and through the public `GET /attestations/{id}`; individually hideable is Proposed | public implemented, hide Proposed |
| integrator bindings (which integrators a user plays) | node API: scoped to the identity and its integrator. Ledger: `game.binding_established` and `permission.granted` are public | ledger exposure implemented, a private scope Proposed |
| open name search | off | implemented (the `discoverable` preference, off for every identity) |

Visibility settings are identity state, not durable protocol history, unless a later decision promotes them. The defaults above describe the node API; they do not describe the ledger. A guild's `roster_visibility` value does appear on the ledger, in `guild.updated`.

## Presence and guilds

Presence is the most sensitive realtime signal and defaults to friends; see [presence](./presence.md). A block always wins over any visibility setting and is checked first. Guild roster reads through the node API are policy-controlled by the guild, so a guild can have the API withhold its roster from non-members; the membership events stay on the public ledger regardless, see [what the ledger makes public](#what-the-ledger-makes-public) and [guilds](./guilds.md).

## Analytics

The [registry](./registry.md) publishes counts and aggregates ("2,481,392 unique players"), never a list of who they are. Individual events read through the node API are subject to the same scopes; the same events read from the ledger are not. A public transparency log ([settlement](../architecture/settlement.md)) is public, which is why what goes into it is limited to promised-durable facts and never includes presence, credentials, chat, or blocks. Those durable facts include friend and guild-membership events with their payloads, so "limited" is not "private".

An aggregate small enough stops being anonymous: a count of 1 identifies a specific person as surely as a name. Every registry metric below a configurable minimum cohort size (5 by default) is coarsened to the floor itself and marked inexact, and zero is never coarsened, since "nobody" identifies no one. It is enforced once, centrally, before a metric leaves the process.

## Erasure versus permanence

Visibility answers who can see a fact. It does not answer whether a fact can ever stop existing.

**Ledger-authored facts (identity, friends, guild membership, achievement issuance) cannot be erased, by construction.** The settlement log is append-only and hash-chained, and the server has no API route that deletes or edits a committed entry. The only reduction an operator can configure is payload pruning: a node on the hot tier, with pruning explicitly enabled (both are off by default), nulls the payload of entries older than its window, only in its own authored rows. When archive peers are configured it prunes only past what they have confirmed mirroring; with none configured there is no such check. Pruning never touches an entry's metadata (issuer, subject, kind, timestamp, version, hashes), so a pruned entry still names who did what and when, and for events whose subject or issuer is an identity it still names that identity. It does not reach any other node's copy: mirrors keep the payloads they verified and stored, and a mirror refuses to store an entry whose payload is pruned, so a payload a mirror already holds stays readable from that mirror. Removing a payload from one node therefore does not remove the fact. How far pruning may go past payload nulling is a recorded decision: [ADR 1009](../architecture/decisions/1009-how-far-does-ledger-pruning-go-past-payload-nulling.md), and see [settlement](../architecture/settlement.md).

The practical lever for "I want this identity to go dark" is **pseudonymization**: revoke every signing key, author no further events, and let existing history remain as durable and attributable as it was. That is the same posture as issuer keys and attestation revocation: never rewrite history, change what is trusted going forward.

**Chat content is a different, already-solved case.** Guild channel and DM message bodies were built never to touch the ledger. They live in ordinary tables with an archive tier and a real deletion path, so erasing message content is realistic and works today; it was never part of the durable-history promise. See [guild chat](./guilds/chat-and-events.md) and [communication](../architecture/communication.md).

## Blocks and discovery

A block is visible only to the identity that created it, and no endpoint reveals to the blocked party that they have been blocked; a blocked pair's friend request looks identical to one naming a nonexistent identity, and a blocked identity's presence reads as `Offline`. `presence_preferences.hide_active_in` is an identity-controlled setting that is not a visibility scope at all: it removes the "active in" integrator from view entirely, whoever is asking. `discovery_preferences.discoverable` gates whether an identity can be found by open search at all, and is read live on every call so turning it off takes effect immediately. See [social graph](./social-graph.md).

## Open questions

How much social information should be portable across integrators, and whether cross-integrator blocking (a block applying anywhere the blocked party might otherwise reach the blocker) should exist as more than what is built.

Undecided: the privacy design for ledger payloads. Friend and guild-membership events are public with their payloads today; whether they should be committed in a form that does not reveal who is friends with whom, and what a visibility setting should mean for ledger data, has not been decided.

## Implementation

Status: partially implemented.

- `Visibility` (`Public`, `AuthenticatedOnly`, `Friends`, `GuildMembers`, `Private`) is a fixed closed vocabulary in [`permissions.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/permissions.rs). Integrator read access is entirely the separate capability-grant mechanism, orthogonal to `Visibility`.
- `is_visible(state, visibility, viewer, subject, guild_id)` in [`visibility.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/visibility.rs) is the one shared helper: the subject always sees their own data, `Friends` checks friendships, and `GuildMembers` checks membership. An unrecognized stored value falls back to `Public` and never hard-fails a read.
- Presence reads are gated by each subject's `profiles.presence_visibility` (default `friends`, set through `PATCH /me`); guild rosters by `guilds.roster_visibility` (default `guild_members`, set through `PATCH /guilds/{id}`), and the guild owner always sees the roster.
- The ledger read path is `GET /ledger/entries` in [`settlement.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/settlement.rs), registered without authentication in the route table in [`lib.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/lib.rs). It consults no visibility setting. The event payloads are in [`event_payloads.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/event_payloads.rs), and pruning is in [`retention.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/chain/src/retention.rs).
- Not yet built: a per-resource scope for profile fields, another identity's friends list (no such endpoint exists), and achievement-history hide or feature.

## Related

- [Identity](./identity.md), [presence](./presence.md), [guilds](./guilds.md), [social graph](./social-graph.md), [registry](./registry.md)
- [Security model](./security-model.md), [settlement](../architecture/settlement.md)
