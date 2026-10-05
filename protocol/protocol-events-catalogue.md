# Protocol Event Catalogue

**Status:** Reference

This is the row-by-row list of every protocol event kind: who issues it, its payload, what it drives, and how it is attributed. It complements [protocol events](./protocol-events.md), which covers the envelope, pipeline, and versioning policy. The list reflects the emitters and typed payloads in the protocol repository; if it and the code disagree, the code is right.

Naming is `<domain>.<past-tense-verb>`. A kind marked **built** has an enum-backed variant and a typed payload struct that the server builds and serializes, so the payload column is kept honest by the compiler. A kind marked **not built** describes a planned kind that no emitter produces; a decoder sees it as `Other`, and it gets a real variant exactly when its emitter exists.

**Attribution** column:

- **embedded proof**: the payload carries the issuer's detached signature, so anyone can re-verify it from the ledger.
- **verified at write**: a real signature by the actor is checked before the event is built, but it is not stored in the payload.
- **node**: the node records the event on behalf of an authenticated actor (a session, or an integrator authenticated by challenge-response). No per-event signature exists for these kinds yet.

## Identity

| Kind | State | Issuer to subject | Payload | Drives | Attribution |
| --- | --- | --- | --- | --- | --- |
| `identity.created` | built | identity to identity | v2: `identity_id` (64-character hex, derived from the key), `ticket_id`, `display_name` (the unique handle), `public_key` (inception key, base64), `signature` | identities | embedded proof (inception key over the v2 signing bytes) |
| `identity.signing_key_added` | built | identity to identity | v2: `signing_key_id`, `public_key`, `device_label`, `approved_by_signing_key_id`, `identity_id`, `kind` (`inception` or `device_grant`), and for a device grant `grant_id` and `approval_signature` | signing keys (authoring node and mirror-only projections) | embedded proof for a device grant (approving device's signature); the inception key carries none and is valid when it derives the identity id |
| `identity.signing_key_revoked` | built | identity to identity | v2: `identity_id`, `signing_key_id`, `revoked_by_signing_key_id`, `signature` | signing keys | embedded proof (an active key of the same identity) |
| `identity.passkey_registered` | built | identity to identity | `passkey_id`, `identity_id`, `credential_id`, `passkey_data` (public WebAuthn material only), `label` | passkeys | node |
| `identity.passkey_revoked` | built | identity to identity | `passkey_id`, `identity_id` | passkeys | node |
| `identity.recovery_configured` | built | identity to identity | `guardian_ids`, `threshold` | recovery settings | node (session-authenticated) |
| `identity.recovery_requested` | built | identity to identity | `request_id`, `threshold` | recovery requests | node (the requester has no session) |
| `identity.recovery_approved` | built | guardian to identity | `request_id`, `guardian_id`, `approvals_count`, `threshold`, `delay_ends_at` | recovery approvals | node |
| `identity.recovery_cancelled` | built | owner or guardian to identity | `request_id`, `cancelled_by`, `reason` | recovery requests | node |
| `identity.recovered` | built | identity to identity | `request_id`, `device_label` | passkeys | node |
| `profile.updated` | built | identity to identity | sparse: only the changed fields among `display_name`, `avatar_url`, `bio`, `favorite_genres`, `pronouns`, `banner_url`, `status`, `links`, `timezone`, `theme_color`, `location`, `main_guild` | profiles | node |

The three v2 identity kinds replace v1, which decoders no longer accept (a sanctioned exception to the [versioning policy](./protocol-events.md#versioning-policy)). The recovery kinds and the passkey kinds carry no signature. The `recovery` signing-key kind is defined in the payload types and no emitter produces it. Embedded proofs are verified on mirroring nodes at projection time, and the unsigned kinds are accepted there only from the network's `core` shard and the node's own stream; see [identity](./identity.md#projection-time-verification). Finalizing a recovery also emits one `identity.passkey_revoked` for each passkey it replaces.

## Integrators, bindings, and issuers

| Kind | State | Issuer to subject | Payload | Drives | Attribution |
| --- | --- | --- | --- | --- | --- |
| `game.registered` | built | integrator to integrator | `game_id`, `slug`, `name`, `developer`, `category`, `requested_capabilities`, `initial_key` | integrators, registry | node (the registrant's key is not yet proven) |
| `game.binding_established` | built | identity to integrator | `binding_id`, `identity_id`, `game_id`, `slug` | bindings, registry | node |
| `game.binding_ended` | built | identity to integrator | `binding_id`, `identity_id`, `game_id`, `slug` | bindings | node |
| `permission.granted` | built | identity to integrator (per capability) | `binding_id`, `identity_id`, `game_id`, `capability` | permission grants | node |
| `permission.revoked` | built | identity to integrator (per capability) | same, plus optional `reason` (present when revoked as a side effect of ending the binding) | permission grants | node |
| `issuer.registered` | built | issuer to network | `issuer_ref`, `network_id`, `registered_at`: the per-network admission record, distinct from `game.registered` | issuer network registrations | node (auto-admission or explicit registration) |
| `issuer.key_added` | built | issuer to issuer | `game_id`, `slug`, `key_id`, `algorithm`, `public_key`, `role`, `valid_until` (and `purpose`) | issuer keys | node, authenticated by the root key |
| `issuer.key_revoked` | built | issuer to issuer | `game_id`, `slug`, `key_id`, `revoked_at`, `reason` | issuer keys | node, authenticated by the root key |
| `issuer.key_expired` | not built | issuer to issuer | key id | issuer keys | n/a |
| `issuer.suspended`, `.reinstated`, `.revoked`, `.deprecated` | not built | network or issuer to issuer | reason, effective at | issuer status | n/a |
| `integrator.recognition_published` | built | integrator to integrator | `recognizer_id`, `recognized_id`, `scope` | recognition graph | node |
| `integrator.recognition_revoked` | built | integrator to integrator | `recognizer_id`, `recognized_id` | recognition graph | node |

The `game.` prefix is a preserved historical spelling and applies to every integrator category; see [registry](./registry.md#beyond-games-integrator-category).

## Social graph and guilds

| Kind | State | Issuer to subject | Payload | Drives | Attribution |
| --- | --- | --- | --- | --- | --- |
| `friend.requested` | built | identity to identity | `from`, `to`, `actor` | friendships | node |
| `friend.accepted` | built | identity to identity | `from`, `to`, `actor` | friendships | node |
| `friend.removed` | built | identity to identity | `a`, `b`, `actor` | friendships | node |
| `friend.relationship_reversed` | built | identity to identity | `reverses_event_id`, `recovery_request_id`, `identity_id`, `counterparty_id`, `effect` | friendships | node. A compensating event; the reversed entry is never altered (see [recovery](./identity/recovery.md#post-compromise-rollback)) |
| `guild.created` | built | identity to guild | `guild_id`, `name`, `tag`, `description`, `owner` | guilds | node |
| `guild.updated` | built | guild to guild | full replace: `guild_id`, `name`, `tag`, `description`, `motd`, `banner`, `icon`, `links`, `recruiting`, `public`, `game_breakdown_public`, `join_policy`, `roster_visibility`, `actor` | guilds | node |
| `guild.role_defined` | built | identity to guild | `guild_id`, `name_index`, `name`, `permissions`, `description`, `badge`, `actor` | roles | node |
| `guild.role_deleted` | built | identity to guild | `guild_id`, `name_index`, `actor` | roles | node |
| `guild.member_added` | built | guild to identity | `guild_id`, `identity_id`, `role_index`, `via` (`invite`, `join_request`, `direct_join`), `actor` | rosters, history | node |
| `guild.member_removed` | built | guild to identity | `guild_id`, `identity_id`, `reason` (`left`, `removed`), `actor` | rosters, history | node |
| `guild.membership_reversed` | built | identity to guild | `reverses_event_id`, `recovery_request_id`, `guild_id`, `identity_id`, `effect`, `role_index` | rosters, history | node. A compensating event |
| `guild.role_changed` | built | guild to identity | `guild_id`, `identity_id`, `role_index`, `actor` | rosters, history | node |
| `guild.owner_transferred` | built | guild to identity | `guild_id`, `from`, `to` | guilds | node |
| `guild.game_associated` | built | guild to integrator | `guild_id`, `game_id`, `actor` | associations | node |
| `guild.favorite_games_updated` | built | guild to guild | `guild_id`, `game_ids`, `actor` | favorites | node |
| `guild.channel_created` | built | guild to channel | `guild_id`, `channel_id`, `name`, `actor` | channels | node |
| `guild.channel_renamed` | built | guild to channel | `guild_id`, `channel_id`, `name`, `announcement_only`, `topic`, `public`, `actor` | channels | node |
| `guild.channel_archived` | built | guild to channel | `guild_id`, `channel_id`, `actor` | channels | node |

**Drives** names the read model an event feeds. Only `friendships` and `rosters` are indexer projections that a rebuild replays: `friend.accepted`, `friend.removed`, `friend.relationship_reversed`, `guild.created`, `guild.member_added`, `guild.member_removed`, `guild.membership_reversed` and `guild.role_changed`. `guilds`, `roles`, `channels`, `associations` and `favorites` are server-owned tables that the handler writes directly; their events are recorded for audit and mirroring and are not replayed. `friend.requested` is recorded and has no projection. See [query and indexing](../architecture/query-and-indexing.md#where-social-state-lives-today).

## Attestations and Integrator Space

| Kind | State | Issuer to subject | Payload | Drives | Attribution |
| --- | --- | --- | --- | --- | --- |
| `achievement.defined` | built | integrator to achievement id | `id`, `game_id`, `slug`, `key`, `name`, `description`, `schema`, `icon`, `icon_url`, `version` | definitions | node |
| `achievement.definition_updated` | built | integrator to achievement id | same shape as `.defined` | definitions | node |
| `achievement.definition_retired` | built | integrator to achievement id | `id`, `game_id`, `slug`, `key` | definitions | node |
| `achievement.issued` | built | integrator to identity | `id`, `issuer`, `subject`, `achievement`, `evidence`, `proof` (`key_id`, `algorithm`, `bytes`) | attestations | embedded proof |
| `achievement.revoked` | built | integrator to attestation | `id`, `attestation_id`, `issuer`, `reason_code`, `reason` | attestation status | verified at write (issuer key) |
| `milestone.defined`, `.definition_updated`, `.definition_retired` | built | app or service to milestone id | same fields as the `achievement.*` rows | definitions | node |
| `milestone.issued`, `.revoked` | built | app or service to identity or attestation | same fields as `achievement.issued`, `.revoked` | attestations | embedded proof (issued); verified at write (revoked) |
| `attestation.superseded` | not built | integrator to attestation | old ref, new ref | attestation status | n/a |
| `game_event.result_issued` | not built as a kind | integrator to identity | is `achievement.issued` with a game-event schema; see [cross-integrator events](./cross-integrator-events.md) | attestations | embedded proof |
| `game_schema.published` | built | integrator to schema | `id`, `game_id`, `slug`, `version`, `proto_source`, `supersedes`, `default_visibility`, `field_visibility` | schema discovery | node |
| `game_schema_mapping.published` | built | integrator to mapping | `id`, `integrator_id`, `slug`, `from_schema_id`, `to_schema_id`, `description`, `field_correspondence` | mapping discovery | node |
| `game_data.published` | built | integrator to identity | `id`, `schema`, `game_id`, `subject`, `instance`, `supersedes` | integrator data instances | node |
| `game_data.deleted` | built | integrator to identity | `instance_id`, `schema`, `game_id`, `subject`, `reason_code`, `reason` | integrator data instances | node. A tombstone; the original is never mutated |

## Conventions

`issuer` and `subject` are `GlobalId`s (`<namespace>:<owner>:<kind>:<key>`), namespaced so two integrators' `dragon_slayer` never collide (see [provenance](./provenance.md)). Each kind has exactly one payload schema per version. `achievement.*` and `milestone.*` share one payload struct per row: the claim-vocabulary split is which kind string is used and never a payload difference.

Source: [`events.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/events.rs) and [`event_payloads.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/event_payloads.rs).

## Related

- [Protocol events](./protocol-events.md), [worked ledger example](./worked-ledger-example.md)
- [Identity](./identity.md), [guilds](./guilds.md), [issuers](./issuers.md), [achievements and attestations](./achievements-and-attestations.md)
