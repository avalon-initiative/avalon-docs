# Guild Roles, Permissions, and Membership

**Status:** Implemented

A guild's authority structure is a fixed permission vocabulary assigned through roles, optionally overridden per channel or event, with membership entering through invites, join requests, or an open join policy. This page describes those rules; the concept is in [guilds](../guilds.md).

## Permission vocabulary

`GuildPermission` is a fixed, closed vocabulary that a role's base permission list draws from. There are no custom permission names.

| Permission | Scope | Grants |
| --- | --- | --- |
| `manage_guild` | guild-wide only | edit guild settings and metadata, view the integrator breakdown, pin favorite integrators |
| `manage_roles` | guild-wide only | define and edit roles and permission overrides, remove members holding elevated roles |
| `manage_members` | guild-wide only | invite, remove ordinary members, review join requests |
| `manage_channels` | guild-wide or per channel | create, rename, archive channels, moderate messages |
| `event_manage` | guild-wide or per event | create, reschedule, and delete events |
| `channel_post` | per channel | post in an announcement-only channel |
| `view`, `view_details` | per channel or event | see that a resource exists, and see its content |

The owner has every permission structurally, through the guild's owner field and not through a role row, so ownership cannot be edited away or removed. The owner must transfer ownership before leaving.

## Per-resource overrides

A role's `permissions` list is its base grant, applying guild-wide. A `manage_roles` holder can add an override granting or denying one permission to one role, scoped to a single channel or event. Resolution: the owner's bypass is untouched; otherwise an override for the exact (role, resource, permission) triple decides the outcome outright (an explicit deny beats a base grant, an explicit grant beats a base absence); with no override, the role's base list is the answer. An override pointing at a deleted resource is inert. Guild-wide permissions (`manage_guild`, `manage_roles`, `manage_members`) have no per-instance resource to scope to and use only the flat check.

`view` and `view_details` resolve specially. The baseline for a member with no override is both true. A role denied `view` never sees the resource in a list. A role denied only `view_details` sees that it exists (an event's title and time, the channel entry) but not its content. An explicit `view_details` grant implies `view`, so the two can never be a contradictory pair. Non-members follow the resource's own `public` flag.

## Roles

A guild starts with `owner`, `officer`, and `member` roles. A role carries a `description` (up to 200 characters) and a `badge`: an icon from a closed set (`shield`, `crown`, `star`, `sword`, `wrench`, `heart`, `flag`, `bolt`) paired with a color from a closed set (`gray`, `red`, `orange`, `gold`, `green`, `blue`, `purple`). There is no user-supplied badge image hosting. Role names are unique per guild, case-insensitively. The owner role's permissions cannot be changed (only its cosmetics); the owner and base member roles cannot be deleted; a role still held by any member cannot be deleted. Removing a member with an elevated role requires `manage_roles`, so an officer can remove a plain member but not another officer.

## Membership

- **Join policy** is `invite_only` (default) or `open`, set on the guild. Open guilds accept direct joins.
- **Invites** are addressed to an identity. A pending invite is idempotent (re-inviting returns the existing one), and invitees list their own unresolved invites so accepting does not depend on the sender sharing a raw id.
- **Join requests** are the applicant-initiated counterpart, available for `recruiting` guilds. Applying to a non-recruiting guild or one the applicant already belongs to is rejected; a second pending request returns the existing one; managers with `manage_members` approve or reject; only the applicant can withdraw.
- **Durability.** Invites, declines, withdrawals, and join-request status changes are deliberately not durable history. Only the resulting membership change is, through `guild.member_added` and `guild.member_removed`, and approval uses the same add-member path as an accepted invite or open join so results cannot drift.

Durable guild events are `guild.created`, `guild.updated`, `guild.role_defined`, `guild.role_deleted`, `guild.owner_transferred`, `guild.member_added`, `guild.member_removed`, `guild.role_changed`, `guild.channel_*`, and the two integrator-related kinds; see the [event catalogue](../protocol-events-catalogue.md). Role, override, ownership-transfer, and role-change actions require a [fresh signature](../identity/authentication.md#two-authorization-tiers).

## Implementation

Status: implemented. See [`crates/server/src/guilds.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/guilds.rs) (permission resolution in `resolve_resource_permission` and `has_resource_permission`) and the guild routes in the [OpenAPI document](https://github.com/avalon-initiative/avalon-protocol/blob/main/docs/generated/openapi.json).

## Related

- [Guilds](../guilds.md), [channels, chat, and events](./chat-and-events.md), [discovery and integrator affinity](./discovery-and-affinity.md)
- [Privacy](../privacy.md), [security model](../security-model.md)
