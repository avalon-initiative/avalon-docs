# Integrator Bindings

**Status:** Implemented

A binding records that an Avalon identity participates in a particular integrator (a game, app, or service), and nothing more. Everything an integrator knows about the identity beyond that, such as characters, class, level, appearance, and inventory, belongs to the integrator and lives in its own database. Integrator authority is scoped to the integrator's own binding.

## The tree

```text
Avalon Identity X
    │
    ├── Binding: Ashen Realms
    │       └── (integrator-side) Character: Avion Ranger, level 72
    │
    └── Binding: Ocean World
            └── (integrator-side) Character: Sea Lion Navigator, level 14
```

Avalon holds the two bindings. It does not know what an Avion or a Sea Lion is and never will, unless the integrator explicitly promotes a fact into durable history as an [attestation](./achievements-and-attestations.md), or explicitly publishes it as instance data against a schema it published itself (see [Integrator Space](./integrator-space.md)), subject to that schema's declared visibility. Absent one of those two acts, character rows stay on the integrator's side, referencing the binding or the identity id, and Avalon stores none of their attributes. Published instance data is meant to be small, portable, fun-to-carry flavor data (name, level, race, class, titles), never a character's full mechanical state. The reasoning is recorded in [ADR 0067](../architecture/decisions/0067-identity-is-separate-from-game-characters.md).

## What a binding is

| Field | Meaning |
| --- | --- |
| `identity_id` | the identity |
| `integrator_id` | the integrator |
| `established_at` | when the identity consented |
| `ended_at` | when the identity ended it, if ever |

- A binding is established by the **identity**, through a consent flow, when it first connects to an integrator. An integrator cannot create one unilaterally. Connecting is in the [fresh-signature tier](./identity/authentication.md#two-authorization-tiers).
- Capability grants hang off the binding. No active binding means no grants, and ending the binding ends every grant under it.
- Ending a binding does not delete history. Attestations the integrator issued while the binding was active remain in history with their provenance.
- Bindings are durable protocol events (`game.binding_established`, `game.binding_ended`), so "which integrators has this identity participated in" is reconstructable and the [registry](./registry.md) can count players honestly. The `game.` prefix is a preserved historical spelling; the event applies to every integrator category (see [registry](./registry.md#beyond-games-integrator-category)).

## Scoped authority

```text
Integrator A
    can:
        establish an Integrator A profile for a consenting identity
        manage its own integrator-side character data
        issue Integrator A attestations about that identity
        read whatever Integrator B has explicitly published (attestations,
            or instance data Integrator B opted into being visible)

    cannot:
        read or write Integrator B's own internal, unpublished profile of the
            same identity
        write to Integrator B's published data under any circumstance
        issue attestations under Integrator B's issuer identity
        alter the identity itself, its friends, or its guild history
```

This is enforced by the permission model (every grant is scoped to an integrator and a capability) and by issuer keys (every attestation is signed by the issuing integrator's own key). See [security model](./security-model.md) and [issuers](./issuers.md).

## Bindings and the registry

"Players of Integrator A" means distinct identities holding an active binding to Integrator A, observed through protocol activity, not a number the integrator reports about itself. See [registry](./registry.md).

## Scenario A: an identity enters a second integrator

Identity X has a binding to Integrator A and connects to Integrator B. Integrator B sees an identity with a display name, whatever capabilities X granted, and X's authentic attestations from Integrator A (which B may or may not recognize; see [trust model](./trust-model.md)). B creates its own character for X in its own database. It never sees A's character, and A never learns about B's unless X's permissions expose it.

## Implementation

Status: implemented.

- `IntegratorBinding { identity_id, integrator_id, established_at, ended_at }` in [`integrators.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/integrators.rs). No game-specific field exists on it by design.
- The consent flow is `POST /integrations/{slug}/connect` in [`connections.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/connections.rs). It validates each approved capability against what the integrator declared at registration, creates the binding only if none is active (reconnecting is idempotent), and inserts one grant per capability in one transaction via the outbox. `DELETE /integrations/{slug}/grants/{capability}` revokes one grant; `DELETE /integrations/{slug}/connect` ends the binding and every grant under it; `GET /me/connections` lists active bindings with their grants.
- `bindings` and `permission_grants` are projections. `game.binding_established`, `game.binding_ended`, `permission.granted`, and `permission.revoked` are the durable history and are network-attributed for now, not identity-signed.
- The SDKs' `authenticate()` calls `GET /me/grants` and populates the session's granted capabilities from the caller's real active grants for that integrator.

## Related

- [Identity](./identity.md), [Integrator Space](./integrator-space.md), [issuers](./issuers.md), [registry](./registry.md)
- [Privacy](./privacy.md) for how grants compose with visibility
- [Security model](./security-model.md)
- [Cross-integrator events](./cross-integrator-events.md)
