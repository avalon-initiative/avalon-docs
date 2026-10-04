# Identity Aggregate View: Field Reference

**Status:** Reference

This is the field-by-field lookup table for the [identity aggregate view](./identity-aggregate-view.md), naming the real Rust type behind each field so it can be checked against source. It is the page to return to once the two layers are understood. If it and the code disagree, the code is right.

## Layer 1: identity, profile, friends, guild membership

Backed by `Identity`, `Profile`, `GuildMember`, and `Friendship` in [`crates/protocol/src`](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/protocol/src).

| Field | Type | Used for |
| --- | --- | --- |
| `identity.id` | `IdentityId` (64-character lowercase hex string) | The stable, opaque handle everything hangs off. Derived from the identity's first signing key, never from a name. See [the identity id](./identity.md#the-identity-id). |
| `identity.created_at` | timestamp | When the identity came into existence (`identity.created`). |
| `profile.display_name` | string | Human-facing name, and the globally unique, case-insensitive handle itself (no discriminator suffix on this node; a name taken by another identity on a mirrored shard is stored as `name~<id prefix>`, see [names across nodes](./identity.md#names-across-nodes)). |
| `profile.avatar_url` | `Option<string>` | Self-chosen image, validated as an `http`/`https` URL. |
| `profile.banner_url` | `Option<string>` | A second image slot for a profile header, same validation. |
| `profile.bio` | `Option<string>` | Free-text self-description, up to 500 characters. |
| `profile.status` | `Option<string>` | A short tagline, up to 100 characters. |
| `profile.pronouns` | `Option<string>` | Free text, up to 40 characters. |
| `profile.favorite_genres` | `Vec<Genre>` | A fixed, small controlled vocabulary, kept useful for matching and filtering. |
| `profile.links` | `Vec<string>` | Up to 5 self-reported `http`/`https` URLs. |
| `profile.timezone` | `Option<string>` | Self-reported, useful for guild event scheduling. Not validated against the IANA database (documented gap). |
| `profile.theme_color` | `Option<string>` | A six-digit hex accent color. Cosmetic only. |
| `profile.location` | `Option<string>` | Free text only. Never IP-derived or geocoded; this is a load-bearing constraint. |
| `profile.main_guild` | `Option<GuildId>` | A self-chosen pointer to one of the identity's current guild memberships. Clears automatically if that membership ends. |
| `profile.effective_main_guild` | derived, response only | Read-time fallback to the earliest-joined guild when `main_guild` is unset. Not stored and never in a `profile.updated` payload. |
| `guilds[]` | `GuildMember { guild_id, role, joined_at }` | Every current guild membership with the identity's role. |
| `friends[]` | derived from `Friendship { a, b, since }` | Accepted friend connections (symmetric; either side can be `a` or `b`). |

## Layer 2: one entry per integrator binding

Backed by `IntegratorBinding`, `IntegratorCategory`, and `AchievementAttestation`.

| Field | Type | Used for |
| --- | --- | --- |
| `type` | `IntegratorCategory` (`game`, `app`, `service`) | The category the integrator registered as. A label, not a different mechanism. |
| `integrator_id` | string or slug | Which integrator the entry describes. |
| `binding.established_at` | timestamp | When the identity opted in (identity-initiated; see [bindings](./bindings.md)). |
| `binding.ended_at` | `Option<timestamp>` | When the binding ended, if ever. History stays intact either way. |
| `attestations[].achievement` | `GlobalId` | Which claim the attestation is about: `game:<slug>:achievement:<key>`, or `app:<slug>:milestone:<key>` or `service:<slug>:milestone:<key>`. See [achievements](./achievements-and-attestations.md). |
| `attestations[].issued_at` | timestamp | When the issuer signed the claim. |
| `attestations[].issuer_key_id` | string | Which of the issuer's operational keys signed it, so a compromised key can be pinpointed without implicating the whole integrator. |
| `published_schemas[]` | `game_schema.published` payload | The integrator's own declared shape for its custom data. Schema only. |
| instance data (for example `characters`) | published instance data | Per-user instances against a published schema, read via `GET /identities/{id}/integrator-data`. Public by default once published, with a schema-level `private` opt-out and a field-level override, enforced server-side. See [Integrator Space](./integrator-space.md). |

Presence (`status`, last seen, the integrator the identity is currently active in) is a third, deliberately ephemeral tier. It is never a protocol event and belongs in neither table; see [presence](./presence.md).

## Related

- [Identity aggregate view](./identity-aggregate-view.md)
- [Identity](./identity.md), [bindings](./bindings.md), [Integrator Space](./integrator-space.md)
- [Worked ledger example](./worked-ledger-example.md)
