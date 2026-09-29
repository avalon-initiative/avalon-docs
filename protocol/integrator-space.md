# Integrator Space

**Status:** Implemented — schema publication, data exposure, and mapping are built; universal capability mapping is Undecided and deliberately unbuilt.

An Integrator Space is what an integrator has chosen to describe to Avalon about its own data model, and how much of it is exposed. It lets an integrator make its data structurally describable, versioned, discoverable, and attributable to itself without Avalon standardizing what that data means. A [binding](./bindings.md) says an identity participates in an integrator; Avalon holds no opinion about what a "level" or a "class" is.

An integrator can publish a versioned, immutable `.proto` description of its data model, discoverable through the [registry](./registry.md). It can also expose instances of that data under a visibility policy, and publish a documented mapping between two schema versions (explicitly not an execution engine).

## Not a new participation record

A binding deliberately has no integrator-data field. An Integrator Space belongs to the integrator, not to an identity-integrator pair. It does not replace the integrator's own database or extend `IntegratorBinding`:

```text
Integrator
  │
  ├── (integrator-side) full internal model: combat, quests, world state,
  │                matchmaking, complete character state. Avalon never
  │                sees this by default.
  │
  └── Integrator Space (Avalon-facing, optional, incremental)
        ├── declared schemas          "here is how our data is structured"
        ├── schema versions           "here is how that structure evolved"
        ├── exposed entities          "here are instances we choose to expose"
        └── mappings between versions "here is how v1 corresponds to v2"
```

An integrator with zero Integrator Space content is a fully valid Avalon integration: identity, friends, guilds, and achievements do not require one.

## Minimal versus deep integration

A small integrator can stay at "character ID and name, achievements, selected assets" with no declared schema; the achievement `schema` field is already sufficient. An integrator wanting richer interoperability declares more (character, items, achievements, titles), each a declared, versioned schema, enabling migration, portability, and cross-integrator recognition. Deep integration is opt-in per entity, the same way [portable assets are opt-in per item](../architecture/future-layers.md). Avalon never requires an integrator to expose its full model.

## Schema versus data exposure

These are two separate write paths with independent authorization.

```text
Schema publication  =  "Here is how our data is structured."
Data exposure       =  "Here are the instances we choose to expose."
```

An integrator can publish a `character/v3` schema publicly without exposing a single character. Nothing lets data exposure imply schema publication or the reverse. Neither is about meaning: `character.level` means whatever the integrator says it means. Data exposure defaults to network-readable, as attestations do: publishing is the opt-in.

## Schema versus mapping

A schema describes a data model (`game:ashen-realms/character/v1`). A mapping describes a relationship between two models (`v1 -> v2`). Not every schema needs a mapping, and not every mapping needs to be executable; it may only document field correspondence (renames, merges, splits, dropped fields, defaults) for a human or another developer. **The integrator owns the semantic transformation.** Avalon describes, stores, discovers, and structurally validates a mapping where one exists, and never decides what an integrator's migration means. Validation stops at structural sanity: both referenced schema versions exist and belong to the publisher.

```json
// game:ashen-realms/character/v1
{ "level": "u32", "xp": "u64", "skills.fishing.level": "u32" }
// game:ashen-realms/character/v2
{ "progression.rank": "u32", "progression.experience": "u64", "professions.fishing": "u32" }
// mapping v1 -> v2
{ "level": "progression.rank", "xp": "progression.experience",
  "skills.fishing.level": "professions.fishing" }
```

A second integrator is free to model the same idea however it wants and need not converge on these names. An emitted instance is not bare JSON but an instance of a declared, versioned schema attributable to its owner: `{ "schema": "game:ashen-realms/character/v1", "entity": "character", "id": "character:12345", "data": { "level": 87, "xp": 18293821 } }`.

## Representation and versioning

A published schema is protobuf IDL (`.proto`), chosen for mature field-numbering and evolution rules and broad developer familiarity. It is stored and served back verbatim. Avalon parses it (pure Rust, no `protoc` binary, since it parses untrusted third-party text at request time) to resolve its root message, validate `field_visibility` names, and validate submitted instance data. The network surface stays JSON-only: protobuf's canonical JSON mapping is the bridge, and codegen to language bindings is out of scope.

- A schema must declare exactly one top-level `message`, which becomes its root type. Zero or several is rejected.
- Shape governance: a top-level message with more than 100 fields, or nested deeper than 10 levels, is rejected at publish time. An instance's serialized JSON is capped at 64 KiB. These are fixed protocol constants and not per-hoster settings, because they decide whether a schema or write is valid at all, so every node must apply the identical bound or mirrors would diverge.
- Version identity is a monotonic `version: u32` per integrator, plus a `superseded_by` pointer set once a later version supersedes it, so lineage is traceable without rewriting published text. A published version is immutable: evolving a schema means publishing a new version.

## Historical interpretation

A schema version is immutable once data is recorded against it. Old data is read according to the schema version it was created under, and a new version never silently reinterprets it. This reuses the [event versioning policy](./protocol-events.md#versioning-policy): every version stays decodable forever, and a rename or meaning change is a new version.

## Visibility and reads

`default_visibility` (`public` or `private`) is declared per schema and `field_visibility` overrides it per field in either direction. Both default to fully open, and `field_visibility` keys are validated against the root message's real field names (a nonexistent name is rejected). A field is included in a read only if the default is public and the field is not marked private, or the default is private and the field is marked public. Matching is on literal top-level JSON keys; nested-field visibility is a documented limitation.

`GET /identities/{id}/integrator-data` is public and unauthenticated (the same posture as `GET /attestations/{id}`), reads the indexer projection and never raw ledger data, and applies visibility per instance. A profile with nothing published and one with published data none of which is visible to the caller render identically, by design. Instance publication needs three things together: the caller is the owning integrator, the subject has an active binding to it (the user's consent), and the schema belongs to the caller. Deleting an instance writes a tombstone (`game_data.deleted`); see [revocation](./revocation.md#implementation).

## Universal versus integrator-specific semantics: Undecided

Avalon may eventually define optional interoperable capabilities that an integrator can choose to map its own fields onto (for example, a protocol-level `character.progression.level`). This is explicitly not decided or scoped, must not be built ahead of real demand, and is listed as an open question in the [design proposal](../architecture/design-proposal.md). The architecture allows it later without anyone designing a universal progression or class taxonomy now.

## Provenance and discoverability

Integrator Space data reuses the existing [provenance](./provenance.md) model: an exposed entity has an owning integrator, a schema and version it was recorded under, and, where a mapping was used, the mapping and source version. No new provenance primitive is needed. Publication metadata (schema id, version, owner, lineage) is the kind of durable-derived fact the [registry](./registry.md) surfaces. Full schema bodies and instances are not settlement-layer material by default; the settlement layer commits selectively, following the same discipline as assets.

## What this does not do

- It does not require any integrator to expose its internal model beyond what it chooses.
- It does not make Avalon the arbiter of what an integrator's fields mean.
- It does not make a character portable; portability stays opt-in and per entity.
- It does not extend `IntegratorBinding` or the achievement `schema` field to carry general integrator data.

## Implementation

Status: implemented.

- Types: `IntegratorSchemaVersion` in [`integrator_schemas.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/integrator_schemas.rs) and the mapping type in [`integrator_schema_mappings.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/integrator_schema_mappings.rs). Schema ids are `game:<slug>:schema:<version>`.
- Server: [`integrator_schemas.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/integrator_schemas.rs) (`POST /integrations/{slug}/schemas`, public `GET` list and by version), [`integrator_data.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/integrator_data.rs) (`POST /integrations/{slug}/schemas/{version}/data`, `DELETE .../data/{subject}`, `GET /identities/{id}/integrator-data`), [`integrator_schema_mappings.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/integrator_schema_mappings.rs) (`POST` and public `GET` under `/integrations/{slug}/mappings`), and [`proto_schema.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/proto_schema.rs) for parsing and validation, with a per-process cache of parsed root messages.
- The Rust SDK's `#[derive(AvalonSchema)]` macro generates a struct's `.proto` text and visibility maps so an integrator does not hand-write them; see the [SDK design](../sdk/design.md).

## Related

- [Bindings](./bindings.md), [achievements and attestations](./achievements-and-attestations.md), [registry](./registry.md), [provenance](./provenance.md), [revocation](./revocation.md)
- [Identity aggregate view](./identity-aggregate-view.md), [protocol events](./protocol-events.md)
- [Future layers](../architecture/future-layers.md)
