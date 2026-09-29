# Guild Discovery and Integrator Affinity

**Status:** Implemented

Guild metadata, a browsable discovery board, and a derived view of which integrators a guild's members actually play are all read-side features built on public guild data and existing bindings. None of them makes a guild belong to an integrator. The concept is in [guilds](../guilds.md).

## Metadata

A guild carries `motd`, `banner` (an `http`/`https` URL), `icon` (a small identity mark, distinct from the wide banner, same validation), an ordered capped list of `links` (`{label, url}`, replaced in full on update), and `recruiting` (default false). All are editable by the owner or a `manage_guild` holder and readable by any authenticated identity. Updates use three-state semantics for string fields (omitted is untouched, empty clears, non-empty sets). Metadata edits ride in `guild.updated`, which is always a full replace.

`recruiting` and `public` are independent settings. `recruiting` governs the discovery board and join-request eligibility. `public` governs whether the roster and public events are visible to any authenticated identity. A guild can be public without recruiting, or recruiting without a public roster. A guild's roster visibility (`public`, `guild_members`, or `private`) is also configurable; the owner always sees it (see [privacy](../privacy.md)).

## Discovery board

`GET /guilds/discover` is a paged, filterable, session-authenticated browse over already-public metadata, with no membership requirement and no new visibility tier.

- **Filters:** `q` (case-insensitive substring over name, tag, description), `tag` (exact, case-insensitive), `integrator`, and `recruiting`.
- **Visibility rule:** a non-recruiting guild never appears in a stranger's results under any filter combination; only an exact id or tag lookup reaches it. `recruiting=true` is a plain filter. Omitting it returns recruiting guilds plus any guild the caller belongs to. `recruiting=false` is still membership-gated, returning only the caller's own non-recruiting guilds, so it cannot be used to enumerate them.
- **Sort:** `newest` (default), `alphabetical`, or `most_members`. There is no trending or engagement ranking.
- **Pagination:** cursor-based, with the last guild id as the cursor.

## Integrator affinity

`GET /guilds/{id}/integrator-breakdown` reports, for a guild, how many current members hold an active [binding](../bindings.md) to each integrator, computed on every read. It is derived data with no protocol event or durable table behind it, the same "hot state, not history" tier as presence and the discovery board. There is no minimum-member threshold, and there is no "add" action: an integrator appears only because a member actually holds an active binding. Response entries carry the integrator id, slug, name, and member count, ordered by count, alongside `total_members` as the denominator for "N of M members play X".

Access: a `manage_guild` holder (or the owner) can always see it; anyone else only if the guild set `game_breakdown_public` (default false). A rejected caller gets 403.

**Favorite integrators.** A `manage_guild` holder can pin up to 5 integrators, in order, as the guild's curated favorites for public display, but only integrators already in the breakdown. `PUT /guilds/{id}/favorite-integrators` sends the full desired list and rejects more than five, duplicates, and any integrator without a live bound member, checked at write time. The write emits `guild.favorite_games_updated`. If a pinned integrator later loses its last bound member, the pin is not removed (that would churn the public display on one member's change); each read instead marks it `stale`, so managers can unpin it. Favorites are always part of the public guild profile, unlike the full breakdown.

A manual "associate an integrator" endpoint (`POST /guilds/{id}/integrations/{integrator_id}`) still works but is superseded by the binding-derived view as the intended way to express a guild-integrator connection.

## Implementation

Status: implemented in [`crates/server/src/guilds.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/guilds.rs) (`discover_guilds`, `game_breakdown`). The "game" spelling in some routes, event kinds, and fields is a preserved historical name (see [registry](../registry.md#beyond-games-integrator-category)).

## Related

- [Guilds](../guilds.md), [roles, permissions, and membership](./permissions-and-roles.md)
- [Bindings](../bindings.md), [registry](../registry.md), [presence](../presence.md)
