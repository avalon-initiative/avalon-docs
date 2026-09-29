# Identity Aggregate View

**Status:** Proposed — no endpoint returns this aggregate shape today; every field in it comes from a real, separately implemented read.

An identity's aggregate view is the single current-state snapshot of one identity once every relevant event has been folded together, split into Avalon-native portable data (layer 1) and per-integrator data (layer 2, the "block space"). It explains why an integrator can write into layer 2 but never into layer 1. The event-by-event history of the same identity is shown in the [worked ledger example](./worked-ledger-example.md); this page is the read-side projection of it.

The shape is assembled conceptually from several real reads: the identity's own profile, the guild-membership list, the friends list, per-subject attestations, and integrator bindings. Building one "full identity view" read is unscoped, open work. Treat the shape below as the intended target for such a read, not a literal response. Every field is a real field from an existing type; only the assembly is illustrative. If this page and the code disagree, the code is right.

## The two layers

**Layer 1: Avalon-native, portable identity data.** Everything under the direct control of the identity's owner, with two narrow exceptions: guild role changes go through guild governance (see [guilds](./guilds.md)), and friendship requires both parties' consent (see [social graph](./social-graph.md)). This data follows the identity across every integrator, app, and service: identity, profile self-description, friends, guild memberships. See [identity](./identity.md#self-described-metadata-is-self-expression-not-fact).

**Layer 2: integrator block space.** Everything scoped to one game, app, or service: a [binding](./bindings.md) (the identity's opt-in connection to that integrator) plus whatever [attestations](./achievements-and-attestations.md) that integrator has issued about the identity under its own issuer key, plus any data the integrator chose to publish through [Integrator Space](./integrator-space.md). Game, app, and service are one unified concept (`IntegratorCategory`), and a layer-2 entry is shaped the same way regardless of category, distinguished only by its `type`.

## The shape

```json
{
  "identity": { "id": "a1b2c3d4-...-000001", "created_at": "2027-01-04T09:12:03Z" },
  "profile": {
    "display_name": "LV",
    "avatar_url": "https://...",
    "banner_url": "https://...",
    "bio": "Full-time dragon slayer.",
    "status": "Raiding tonight",
    "pronouns": "she/her",
    "favorite_genres": ["rpg", "mmo"],
    "links": ["https://..."],
    "timezone": "America/Los_Angeles",
    "theme_color": "#7c3aed",
    "location": "Pacific Northwest",
    "main_guild": "g-1",
    "effective_main_guild": "g-1"
  },
  "guilds": [
    { "guild_id": "g-1", "role": "officer", "joined_at": "2027-02-01T00:00:00Z" }
  ],
  "friends": ["a1b2c3d4-...-000002", "a1b2c3d4-...-000003"],
  "integrations": [
    {
      "type": "game",
      "integrator_id": "ashen-realms",
      "binding": { "established_at": "2027-01-04T09:20:00Z", "ended_at": null },
      "attestations": [
        {
          "achievement": "game:ashen-realms:achievement:dragon-slayer",
          "issued_at": "2027-01-10T00:00:00Z",
          "issuer_key_id": "ashen-realms-op-1"
        }
      ]
    },
    {
      "type": "app",
      "integrator_id": "some-companion-app",
      "binding": { "established_at": "2027-04-01T00:00:00Z", "ended_at": null },
      "attestations": []
    }
  ]
}
```

`main_guild` is the profile's own stored field, `null` unless explicitly set. `effective_main_guild` is not a profile field at all: it is computed at read time, falling back to the earliest-joined guild when `main_guild` is unset, and it appears only in a response shape, never in storage or in a `profile.updated` payload. Field-by-field types are in the [field reference](./identity-aggregate-view-fields.md).

## One integrator's entry, fleshed out

The `integrations` entry above is minimal. The following is one entry for a hypothetical integrator, "Emberfall Online", showing the two different mechanisms layer 2 contains.

```json
{
  "type": "game",
  "integrator_id": "emberfall-online",
  "binding": { "established_at": "2027-06-01T14:00:00Z", "ended_at": null },
  "attestations": [
    { "achievement": "game:emberfall-online:achievement:first-blood",
      "issued_at": "2027-06-01T14:32:00Z", "issuer_key_id": "emberfall-op-1" }
  ],
  "published_schemas": [
    {
      "id": "game:emberfall-online:schema:character:v1",
      "version": 1,
      "proto_source": "message Character { string name = 1; uint32 level = 2; string race = 3; string class = 4; repeated string titles = 5; }",
      "default_visibility": "private",
      "field_visibility": { "name": "public", "level": "public", "class": "public" }
    }
  ],
  "characters": {
    "instances": [
      { "schema": "game:emberfall-online:schema:character:v1",
        "published_at": "2027-06-01T14:35:00Z",
        "fields": { "name": "Vesryn", "level": 42, "class": "Ranger" } }
    ]
  }
}
```

`race` and `titles` are part of the instance the integrator published but are absent from `fields`: the schema's `default_visibility` is `private` and only `name`, `level`, and `class` are overridden to `public`, so the read endpoint drops the others entirely, not as null or redacted values.

Three pieces, three rules:

- **`attestations`** are canonical across every integrator. An integrator cannot invent its own shape for them; each is a `GlobalId` plus an attestation identical in structure to any other issuer's. That uniformity is what makes a generic "show me this user's achievements from anywhere" view possible.
- **`published_schemas`** are genuinely integrator-custom: the integrator defines its own `Character` shape because nothing outside it is expected to know what that means for it. The `.proto` text is parsed and validated, so a malformed schema is rejected.
- **`characters`** (instance data) is what `GET /identities/{id}/integrator-data` returns: every current, non-superseded instance across integrators, already filtered to the fields its schema currently makes visible. It is deliberately narrow: small, portable, fun-to-carry data such as name, level, race, class, and titles, never full mechanical state (inventory, skills, balance-relevant stats). That heavier data has no reason to leave the integrator's own database.

## Why layer 2 cannot leak into layer 1

Every attestation is signed by the issuing integrator's own key and verified before storage, not vouched for by Avalon. Issuer keys follow a two-tier model (a root key that governs the key set, and operational keys used day to day); see [issuers](./issuers.md). Avalon's server code never authors an `integrations` entry's content, and no integrator can write into another's. A node can relay, store, and index a signature but cannot produce one on the integrator's behalf, and cannot let one integrator's key author a claim that verifies as another's. This holds independently of any single node's honesty, since every durable entry is hash-chained and committed into a Signed Tree Head that any SDK or mirror can verify (see [settlement](../architecture/settlement.md)).

Layer 1 is structurally off-limits to integrators. Nothing in the durable event catalogue lets a game, app, or service author `identity.created`, `profile.updated`, `friend.*`, or `guild.*` under an issuer key. Only the identity's own key or the relevant user-session actions can. There is no code path that accepts one from elsewhere, so this holds by construction, not by a check that could be bypassed. See [security model](./security-model.md#who-controls-what).

## Read access is not one uniform rule

Write isolation in layer 2 is absolute. Read access varies by what the data is:

- **A single attestation whose id is known is public.** `GET /attestations/{id}` takes no authentication, matching the invariant that authenticity is a fact and never gated behind an issuer's permission.
- **Listing all of a subject's attestations to a different caller is undecided.** `GET /me/achievements` reads only one's own full history. No endpoint returns another identity's attestation list, and the visibility policy that would govern one (an issuer-set ceiling, a subject override, or both) is an open decision. Do not assume attestation visibility is wide open by default.
- **Explicitly published schema instance data defaults to network-readable.** Publishing is the deliberate opt-in, as with attestations. A schema can declare `default_visibility: "private"`, and any single field can flip its own visibility the other way, so a private schema can expose a few flavor fields and a public schema can hide a sensitive one. An integrator's own unpublished internal data was never reachable through Avalon and stays that way.

## Where the Hub fits

The Hub is a first-party client, not a registered integrator with an issuer key of its own, so it appears nowhere in `integrations`. Everything it manages (profile, friends, guilds) is layer-1 data. A genuinely Hub-local block space, such as per-user UI preferences with no reason to be portable, is an unbuilt idea; this page should gain a cited example only when one exists. See [ADR 0077](../architecture/decisions/0077-the-hub-is-a-client-of-the-network-not.md).

## Implementation

Status: the component reads are implemented; the aggregate read is not.

- Layer-1 types: `Identity`, `Profile`, `Friendship`, `GuildMember` in [`crates/protocol/src`](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/protocol/src). `effective_main_guild` is a response-only field in the server's profile response.
- `IntegratorCategory`, `IntegratorBinding`, `AchievementAttestation` are implemented. `GET /me/achievements` is paginated and filterable.
- Schema publication, instance data, visibility, and the integrator-data read endpoint are implemented; see [Integrator Space](./integrator-space.md).

## Related

- [Field reference](./identity-aggregate-view-fields.md), [worked ledger example](./worked-ledger-example.md)
- [Identity](./identity.md), [bindings](./bindings.md), [achievements and attestations](./achievements-and-attestations.md), [Integrator Space](./integrator-space.md)
- [Security model](./security-model.md), [presence](./presence.md) (a third, ephemeral tier outside both layers)
