# Privacy and Visibility

**Status:** Partially implemented — visibility is built for presence and guild rosters; the general per-resource scope model is Proposed for the other resources.

Nothing about an identity is exposed because the protocol can technically expose it. Every read path names the visibility scope it checks, and network analytics are aggregates, never per-identity data. A portable identity makes surveillance portable too, and the answer is intentional scoping. This page covers who can see what an identity has done within Avalon. That is a separate and prior question from whether an Avalon identity ties back to a real person, which it does not; see [identity](./identity.md#what-identity-is-not).

## Scopes

| Scope | Who can see | State |
| --- | --- | --- |
| public | anyone, including unauthenticated readers of a mirror | implemented |
| authenticated-only | any Avalon identity | implemented |
| friend-visible | identities in the subject's friends list | implemented |
| guild-visible | members of a given guild | implemented |
| integrator-visible | an integrator holding the relevant capability under an active binding | Planned for reads; see [security model](./security-model.md#authorization-one-capability-one-check) |
| private | the subject only | implemented |
| operator-only | node operators, for diagnostics; never surfaced through the API | not modeled as a scope |

A scope applies per resource: profile fields, presence, friends list, guild membership list, achievement history (with per-claim hide or feature on top). Guilds also set a policy on their own roster (public, members-only, private).

## Composition

An integrator's capability grant never widens what non-integrator viewers can see, and a public visibility setting never grants an integrator a capability it was not given. For a read by an integrator the order is: active [binding](./bindings.md), active `PermissionGrant` for the specific capability, then visibility scope. For a read by a person: relationship to the subject, then visibility scope. One shared authorization helper answers (viewer, subject, resource), and no endpoint does its own ad-hoc check.

## Defaults

Settings are user-controlled and changeable through the API and, for some, the Hub.

| Resource | Default | State |
| --- | --- | --- |
| display name | public | implemented |
| avatar | public | implemented |
| presence | friends | implemented, changeable by the identity |
| guild roster | guild members | implemented, changeable by the guild |
| friends list | private | Proposed: no third-party read endpoint exists yet |
| achievement history | public, individually hideable | Proposed |
| integrator bindings (which integrators a user plays) | private | Proposed |
| open name search | off | implemented (the `discoverable` preference, off for every identity) |

Visibility settings are identity state, not durable protocol history, unless a later decision promotes them.

## Presence and guilds

Presence is the most sensitive realtime signal and defaults to friends; see [presence](./presence.md). A block always wins over any visibility setting and is checked first. Guild membership visibility is policy-controlled by both the identity and the guild, so a guild that wants a hidden roster gets one; see [guilds](./guilds.md).

## Analytics

The [registry](./registry.md) publishes counts and aggregates ("2,481,392 unique players"), never a list of who they are. Individual events are subject to the same scopes when read. A public transparency log ([settlement](../architecture/settlement.md)) is public, which is exactly why what goes into it is limited to promised-durable facts and never includes presence, credentials, or anything an identity did not choose to make durable.

An aggregate small enough stops being anonymous: a count of 1 identifies a specific person as surely as a name. Every registry metric below a configurable minimum cohort size (5 by default) is coarsened to the floor itself and marked inexact, and zero is never coarsened, since "nobody" identifies no one. It is enforced once, centrally, before a metric leaves the process.

## Erasure versus permanence

Visibility answers who can see a fact. It does not answer whether a fact can ever stop existing.

**Ledger-authored facts (identity, friends, guild membership, achievement issuance) cannot be erased, by construction.** The settlement log is append-only and hash-chained, and payload pruning on a hot-tier node is allowed only once an archive-tier node has independently confirmed a durable copy, a mechanism that exists to guarantee nothing is lost. Pruning never touches an entry's metadata (issuer, subject, kind, timestamp) on any tier, so a fully pruned entry still says who did what to whom and when. How far pruning may go past payload nulling is a recorded decision: [ADR 1009](../architecture/decisions/1009-how-far-does-ledger-pruning-go-past-payload-nulling.md), and see [settlement](../architecture/settlement.md).

The practical lever for "I want this identity to go dark" is **pseudonymization**: revoke every signing key, author no further events, and let existing history remain as durable and attributable as it was. That is the same posture as issuer keys and attestation revocation: never rewrite history, change what is trusted going forward.

**Chat content is a different, already-solved case.** Guild channel and DM message bodies were built never to touch the ledger. They live in ordinary tables with an archive tier and a real deletion path, so erasing message content is realistic and works today; it was never part of the durable-history promise. See [guild chat](./guilds/chat-and-events.md) and [communication](../architecture/communication.md).

## Blocks and discovery

A block is visible only to the identity that created it, and no endpoint reveals to the blocked party that they have been blocked; a blocked pair's friend request looks identical to one naming a nonexistent identity, and a blocked identity's presence reads as `Offline`. `presence_preferences.hide_active_in` is an identity-controlled setting that is not a visibility scope at all: it removes the "active in" integrator from view entirely, whoever is asking. `discovery_preferences.discoverable` gates whether an identity can be found by open search at all, and is read live on every call so turning it off takes effect immediately. See [social graph](./social-graph.md).

## Open questions

How much social information should be portable across integrators, and whether cross-integrator blocking (a block applying anywhere the blocked party might otherwise reach the blocker) should exist as more than what is built.

## Implementation

Status: partially implemented.

- `Visibility` (`Public`, `AuthenticatedOnly`, `Friends`, `GuildMembers`, `Private`) is a fixed closed vocabulary in [`permissions.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/permissions.rs). Integrator read access is entirely the separate capability-grant mechanism, orthogonal to `Visibility`.
- `is_visible(state, visibility, viewer, subject, guild_id)` in [`visibility.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/visibility.rs) is the one shared helper: the subject always sees their own data, `Friends` checks friendships, and `GuildMembers` checks membership. An unrecognized stored value falls back to `Public` and never hard-fails a read.
- Presence reads are gated by each subject's `profiles.presence_visibility` (default `friends`, set through `PATCH /me`); guild rosters by `guilds.roster_visibility` (default `guild_members`, set through `PATCH /guilds/{id}`), and the guild owner always sees the roster.
- Not yet built: a per-resource scope for profile fields, another identity's friends list (no such endpoint exists), and achievement-history hide or feature.

## Related

- [Identity](./identity.md), [presence](./presence.md), [guilds](./guilds.md), [social graph](./social-graph.md), [registry](./registry.md)
- [Security model](./security-model.md), [settlement](../architecture/settlement.md)
