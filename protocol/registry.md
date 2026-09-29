# Integrator Registry

**Status:** Partially implemented — five metrics, the directory, and recognition relationships are built; most of the metric table and realtime counts are Planned.

The registry is the network's intelligence layer about participating integrators and issuers. It exposes facts with explicit definitions and never a score, a ranking, or a trust judgment. Metrics are derived from protocol activity wherever possible, labeled by how they were obtained, and aggregated so that no per-user data is exposed. Statistics inform a consumer's trust decision; they do not determine it.

## Not a static list

```text
Avalon Integrator Registry
  ├── Integrator identity              (game:ashen-realms)
  ├── Issuer keys and key history
  ├── Status                           (active / suspended / revoked / deprecated)
  ├── Public metadata                  (name, developer; self-reported)
  ├── Published schema versions        (Integrator Space)
  ├── Durable activity metrics         (derived from events)
  ├── Recognition relationships        (who recognizes whom, for what)
  └── Aggregate network analytics      (Planned)
```

Identity, keys, and status come from [issuers](./issuers.md). Everything else is a projection built by the [indexer](../architecture/query-and-indexing.md).

## Beyond games: integrator category

Games are the first and most-developed integrator category, not the only one: websites and other applications can register too. `category` (`game`, `app`, `service`) is an additive field on registration, defaulting to `game`. The Hub's directory has category tabs, though only games have real registrants today. The registrant is an `Integrator`, and "game" now appears only where it means gaming. Three things deliberately kept their original spelling:

- **Ledger event kinds** (`game.registered`, `game.binding_established`, `game.binding_ended`, `game_schema.published`, `game_data.published`) and their payload keys, which are hash-chained into committed entries and replayed verbatim by the indexer (see [protocol events](./protocol-events.md)).
- **The `game` `GlobalId` namespace**, so ids like `game:ashen-realms:achievement:dragon_slayer` keep resolving.
- **`Issuer::Game` and `IntegratorCategory::Game`**, whose variant names are the category vocabulary alongside `App` and `Service`.

## Derive, do not trust

```text
Integrator registers -> Players establish bindings -> Protocol events
   -> Indexer -> Aggregate statistics
```

"Players" is not a number an integrator reports. It is distinct Avalon identities with an active [binding](./bindings.md), observed through protocol activity. Every published metric carries its definition and a class label.

## Metric definitions

| Metric | Definition | Class | State |
| --- | --- | --- | --- |
| players | distinct identities with an active binding | durable-derived | implemented |
| total players ever | distinct identities that ever had a binding | durable-derived | implemented |
| achievements issued / revoked | count of `achievement.issued` / `.revoked` by this issuer | durable-derived | implemented |
| unique achievement holders | distinct subjects with at least one valid attestation from this issuer | durable-derived | implemented |
| achievement popularity | holders per achievement id | durable-derived | planned |
| cross-integrator players | bound identities that also hold a binding elsewhere | durable-derived | planned |
| recognizing integrators | integrators with a public recognition relationship to this issuer | durable-derived | planned as a metric (the underlying relationships are implemented) |
| guilds with players here; guild members associated | distinct guilds or members bound to this integrator | durable-derived | planned as registry metrics (a per-guild breakdown exists, see [guilds](./guilds/discovery-and-affinity.md)) |
| integrator event participation | attestations with the game-event schema | durable-derived | planned |
| key lifecycle, status, registration history | from issuer events | durable-derived | planned |
| players online now | from presence | **realtime** | planned |
| anything supplied by the integrator | for example genre, website | **self-reported** | n/a |

Realtime numbers are never stored as durable metrics, and self-reported fields are shown as self-reported. Guild metrics use the association phrasing from [guilds](./guilds.md): "N Avalon guilds have members who play Integrator A", never "Integrator A has N guilds".

## Schema discovery

An integrator's published [Integrator Space](./integrator-space.md) schema versions are self-authored facts (integrator id, version, `.proto` source, published-at, `superseded_by` lineage), surfaced as an indexer projection derived from durable events, never a second source of truth. Today they are queryable through the indexer's `list_for_integrator` and the schema endpoints; they are not folded into the registry endpoint.

## Statistics inform trust; they do not determine it

A consuming integrator may eventually write a policy like "accept tournament results from issuers with at least X bound players and Y recognizing integrations". The registry provides inputs and does not enforce "integrators above X are trusted". An integrator with 10 players is not automatically malicious and one with 10,000,000 is not automatically trustworthy. There is no `Avalon Integrator Score: 92/100`, and there will not be one without its own explicit design and decision, kept distinguishable from objective facts. See the [trust model](./trust-model.md).

## Recognition relationships

An integrator can publish which other integrators it recognizes and for which claim types:

```text
Integrator A recognizes Integrator B    achievements, tournament results
Integrator A recognizes Integrator C    tournament results
Integrator B recognizes Integrator A    achievements
```

`POST /integrations/{slug}/recognitions` publishes or updates a directional recognition (`{ recognized_slug, scope: [...] }`, challenge-response authenticated) and `POST .../recognitions/revoke` marks it revoked without deleting the row, so "A used to recognize B" stays visible. `scope` is a free-form string list, never a fixed vocabulary or a score. `GET /integrations/{slug}/recognitions` and `GET /integrations/{slug}/recognized-by` are public, real graph edges. Durable events are `integrator.recognition_published` and `integrator.recognition_revoked`.

Over time this forms a graph of shared players, cross-integrator guilds, and recognized issuers. It is valuable intelligence but not authority: "72 integrators recognize Integrator A" is an input to someone's decision, never a conclusion Avalon draws. Recognition is not validity. Neither key history nor recognition relationships are rendered in the Hub yet.

## Sybil and metric manipulation

An integrator can create a million identities, bind them, issue itself achievements, and appear highly active. Any metric that might influence trust is attackable. Possible levers that raise the cost, **none of which is implemented or weighted**: identity quality and account age, cross-integrator participation, attestations from other issuers about the same identities, issuer history, and the cost of manipulation relative to benefit. This is recorded as an architectural concern, not solved. No metric is scored or weighted to compensate, since that would be a reputation system by another name.

## Privacy

The registry publishes aggregates ("2,481,392 unique players"), never per-identity lists. An aggregate small enough stops being anonymous: `unique_achievement_holders: 1` identifies a person as surely as a name. Every metric below a configurable minimum cohort (5 by default) is coarsened to the floor itself and marked `exact: false`, and zero is never coarsened. This is enforced once, centrally, before any metric leaves the process; see [privacy](./privacy.md).

## External read surface

The registry is meant to be read by more than the Hub (a game's tooling, a researcher). `GET /registry/{slug}` is the standalone contract, returning the same data as `GET /integrations/{slug}/registry` (which stays for existing callers). It is public and unauthenticated. There is no route-versioning scheme anywhere in the API, so stability is by discipline: a response field's meaning is permanent once shipped, new metrics are additive, a breaking change gets a new field or route, and `definition` and `class` are part of the contract for callers to render. Guaranteed stable today are the five fields (`players`, `total_players_ever`, `achievements_issued`, `achievements_revoked`, `unique_achievement_holders`), each as `{ value, definition, class, exact }`, and that no response carries per-identity data. The Rust and C# SDKs have a thin typed client for it. `GET /integrations` is the public, cursor-paginated directory list (`q`, `sort=newest|name`, no ranking or score option).

## Implementation

Status: partially implemented.

- Indexer: `compute_for_integrator` and the `coarsen` privacy floor in [`crates/indexer/src/registry.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/indexer/src/registry.rs), with projections under [`crates/indexer/src/projections`](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/indexer/src/projections). The floor is `AVALON_REGISTRY_MIN_COHORT`.
- Server: [`registry.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/registry.rs), [`integrators.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/integrators.rs), [`recognitions.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/recognitions.rs).
- The `/registry/{slug}` route is served by the node but is not in the generated OpenAPI document, which lists `/integrations/{slug}/registry` instead.

## Related

- [Issuers](./issuers.md), [bindings](./bindings.md), [trust model](./trust-model.md), [privacy](./privacy.md), [Integrator Space](./integrator-space.md)
- [Guilds](./guilds.md), [query and indexing](../architecture/query-and-indexing.md)
