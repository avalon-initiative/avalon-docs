# A Worked Example: One User's Ledger

**Status:** Reference

This page renders one hypothetical user's ledger as a real, ordered sequence of `ProtocolEvent` JSON instances, in the envelope every event uses, and lists what never appears on it. It is for anyone who needs to see what "the ledger" concretely looks like: a contributor, a prospective integrator, a hoster. The abstract list of kinds is the [event catalogue](./protocol-events-catalogue.md).

Payload field names and nesting follow the typed payload structs in the protocol crate. Identifiers, timestamps, and signature bytes are illustrative placeholders. If a payload here and the code disagree, the code is right.

## The cast

- **Nova**: a user, identity id `a1b2c3d4-...-000001`.
- **Ashen Realms** (`ashen-realms`): a `game`-category issuer Nova plays.
- **The Wandering Blades**: a guild Nova founds.

## The sequence

### 1. Nova creates an identity

The only event in this sequence signed by the identity's own key rather than attributed by the node, since it brings that key into existence.

```json
{
  "id": "e0000000-0000-0000-0000-000000000001",
  "kind": "identity.created",
  "issuer": "identity:a1b2c3d4-...-000001:self:created",
  "subject": "identity:a1b2c3d4-...-000001:self:created",
  "payload": { "identity_id": "a1b2c3d4-...-000001", "display_name": "Nova" },
  "timestamp": "2027-01-04T09:12:03Z",
  "version": 1
}
```

No `username` field exists anywhere. `display_name` is the whole handle, globally unique and case-insensitive. See [identity](./identity.md). (Layer-1 events like the following also carry a per-identity chain position, omitted here; see [event chains](./identity/event-chains.md).)

### 2. Nova sets a bio and pronouns

Only fields that changed appear in the payload. An untouched field is absent, not `null`; `null` means an explicit clear.

```json
{
  "id": "e0000000-0000-0000-0000-000000000002",
  "kind": "profile.updated",
  "issuer": "identity:a1b2c3d4-...-000001:self:profile_updated",
  "subject": "identity:a1b2c3d4-...-000001:self:profile_updated",
  "payload": { "bio": "Full-time dragon slayer, part-time guild officer.", "pronouns": "she/her" },
  "timestamp": "2027-01-04T09:18:47Z",
  "version": 1
}
```

### 3. Nova connects to Ashen Realms

Ashen Realms already exists on the network from its own earlier `game.registered` event. Nova connecting is its own event:

```json
{
  "id": "e0000000-0000-0000-0000-000000000003",
  "kind": "game.binding_established",
  "issuer": "identity:a1b2c3d4-...-000001:self:binding_established",
  "subject": "game:ashen-realms:self:binding_established",
  "payload": {
    "binding_id": "b1000000-0000-0000-0000-000000000001",
    "identity_id": "a1b2c3d4-...-000001",
    "game_id": "9f000000-0000-0000-0000-00000000ash1",
    "slug": "ashen-realms"
  },
  "timestamp": "2027-01-10T14:02:11Z",
  "version": 1
}
```

Connecting typically grants one or more capabilities in the same request. Each is its own `permission.granted` event, one per capability and not a list inside the binding event; they are omitted here for brevity.

### 4. Ashen Realms issues an achievement

Ashen Realms first defines `dragon_slayer` (`achievement.defined`, not repeated here), then issues it to Nova. Issuance carries a real embedded signature: Ashen Realms' own key signs the attestation itself, not just the HTTP request that submitted it (see [achievements and attestations](./achievements-and-attestations.md#issuance-is-signed-not-merely-authenticated)).

```json
{
  "id": "e0000000-0000-0000-0000-000000000004",
  "kind": "achievement.issued",
  "issuer": "game:ashen-realms:self:achievement_issued",
  "subject": "identity:a1b2c3d4-...-000001:self:achievement_issued",
  "payload": {
    "id": "at100000-0000-0000-0000-000000000001",
    "issuer": "game:ashen-realms",
    "subject": "a1b2c3d4-...-000001",
    "achievement": "game:ashen-realms:achievement:dragon_slayer",
    "evidence": { "replay_id": "r-88213" },
    "proof": { "key_id": "k2000000-0000-0000-0000-000000000001", "algorithm": "ed25519", "bytes": "MEUCIQDx3f...base64...=" }
  },
  "timestamp": "2027-02-02T20:47:31Z",
  "version": 1
}
```

`evidence` is an unverified, optional pointer supplied by the issuer, carried for context and never part of what is signed. `achievement` is the definition's namespaced `GlobalId`, not a bare name; a display name is resolved by a separate lookup and is never embedded.

### 5. Nova founds a guild and a friend joins

```json
{
  "id": "e0000000-0000-0000-0000-000000000005",
  "kind": "guild.created",
  "issuer": "identity:a1b2c3d4-...-000001:self:guild_created",
  "subject": "guild:g3000000-0000-0000-0000-000000000001:self:guild_created",
  "payload": {
    "guild_id": "g3000000-0000-0000-0000-000000000001",
    "name": "The Wandering Blades",
    "tag": "WB",
    "description": "Casual raiders, EU evenings.",
    "owner": "a1b2c3d4-...-000001"
  },
  "timestamp": "2027-02-15T18:30:00Z",
  "version": 1
}
```

A friend, Kestrel, accepts an invite and joins:

```json
{
  "id": "e0000000-0000-0000-0000-000000000006",
  "kind": "guild.member_added",
  "issuer": "identity:b7000000-0000-0000-0000-00000000kes1:self:guild_member_added",
  "subject": "guild:g3000000-0000-0000-0000-000000000001:self:guild_member_added",
  "payload": {
    "guild_id": "g3000000-0000-0000-0000-000000000001",
    "identity_id": "b7000000-0000-0000-0000-00000000kes1",
    "role_index": 0,
    "via": "invite",
    "actor": "a1b2c3d4-...-000001"
  },
  "timestamp": "2027-02-16T09:05:44Z",
  "version": 1
}
```

`issuer` is Kestrel, the member who joined, while `actor` in the payload is Nova, who sent the invite. `issuer` says whose event this is on the ledger, and the payload's own fields say who caused what within it; the two are not always the same identity.

## What an integrator's own custom fact looks like

Ashen Realms can also publish its own data model, a versioned `.proto` schema, into the same ledger with the same envelope and a different kind:

```json
{
  "id": "e0000000-0000-0000-0000-000000000007",
  "kind": "game_schema.published",
  "issuer": "game:ashen-realms:self:schema_published",
  "subject": "game:ashen-realms:schema:character:v1",
  "payload": {
    "id": "game:ashen-realms:schema:character:v1",
    "game_id": "9f000000-0000-0000-0000-00000000ash1",
    "slug": "ashen-realms",
    "version": 1,
    "proto_source": "message Character { uint32 level = 1; ... }",
    "supersedes": null,
    "default_visibility": "public",
    "field_visibility": {}
  },
  "timestamp": "2027-03-01T11:00:00Z",
  "version": 1
}
```

This is shape only: "here is how our data is structured", not an instance of Nova's character. Instance data is published separately as `game_data.published` (see [Integrator Space](./integrator-space.md)). A fact about a specific user can also land through the achievement mechanism, optionally carrying a `schema` reference. Event result attestations such as tournaments are the same `achievement.issued` mechanism with a game-event schema; see [cross-integrator events](./cross-integrator-events.md).

## What never appears here

None of the following are protocol events, on this or any user's ledger, by design (see [protocol events](./protocol-events.md#hot-gameplay-versus-durable-events) and [privacy](./privacy.md)):

- **Presence** ("Nova is online, playing Ashen Realms right now"): ephemeral, served from a short-TTL in-memory store and never written to the outbox.
- **Guild chat, DMs, and channel messages**: operational-tier data explicitly kept out of the ledger and the outbox by construction, with a test that checks it.
- **Ordinary gameplay**: HP, XP ticks, movement, combat, matchmaking, Ashen Realms' own economy. Avalon sees none of it unless an integrator deliberately describes or exposes it through Integrator Space.
- **Typing indicators and connection state**: never durable, and not even stored beyond what a live connection needs.

A ledger reader (a mirror, an auditor, an indexer rebuild) sees exactly the seven events above for this part of the story: nothing about Nova's online status, nothing said in guild chat, nothing about how she fights dragons. That boundary is the point. Avalon durably remembers facts that matter across integrators and to the user's portable identity, and stays out of everything that is just one integrator being an integrator.

## Related

- [Protocol events](./protocol-events.md), [event catalogue](./protocol-events-catalogue.md)
- [Identity aggregate view](./identity-aggregate-view.md), the same identity as a current-state snapshot
- [Achievements and attestations](./achievements-and-attestations.md), [Integrator Space](./integrator-space.md), [privacy](./privacy.md)
