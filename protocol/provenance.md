# Provenance

**Status:** Implemented — for attestations; ownership and asset provenance are Planned for a later phase.

Provenance is the record of who said something, when, under which key, and whether it still stands. Avalon records provenance; it does not determine universal meaning. Interoperability is only useful if a receiving integrator can answer those questions without asking the original integrator, which may no longer exist, so provenance is a first-class property of every durable claim and survives the death of the integrator that produced it.

## The questions provenance answers

| Question | Answered by |
| --- | --- |
| who issued it? | issuer identity and signing key ([issuers](./issuers.md)) |
| where did it originate? | source integrator or issuer, namespaced id |
| when was it issued? | `issued_at`, plus its position in the log ([settlement](../architecture/settlement.md)) |
| who currently holds it? | the subject, or ownership history for assets (later phase) |
| has it been revoked or superseded? | later entries referencing it ([revocation](./revocation.md)) |
| is it still valid? | point-in-time validity over history ([trust model](./trust-model.md)) |
| does a consuming integrator recognize it? | that integrator's own policy. Not provenance, but it depends on it |

The first six are universal facts. The seventh is contextual and is deliberately kept out of the record.

## Examples

An achievement (implemented):

```text
Achievement
    id:            game:ashen-realms:achievement:dragon_slayer
    issuer:        game:ashen-realms   (key k1, valid at issuance)
    subject:       identity:...X
    issued_at:     2027-03-14T21:07:00Z
    evidence:      opaque reference chosen by the issuer
    status:        ACTIVE   (derived from history)
```

An asset (**Planned**, later phase; no ownership or asset types exist yet, see [future layers](../architecture/future-layers.md)):

```text
Asset
    id:                   game:ashen-realms:asset:sword-of-aether:0421
    original issuer:      game:ashen-realms
    originally issued to: identity:...Y
    transfers:            Y -> Z, Z -> X
    current owner:        identity:...X
```

## Provenance survives integrator death

If Ashen Realms shuts down, its issuer identity, key history, achievement definitions, and every attestation it issued stay in durable history with their signatures. A consuming integrator can still verify that a claim was authentic and valid as of any point in time. What disappears is integrator-side character state; see the survival table in the [architecture overview](../architecture/README.md#what-survives-an-integrators-death).

## Why the display name is not enough

"Dragon Slayer" from three integrators is three different claims. Only the namespaced id plus the issuer record distinguish them. Any UI that shows an achievement without its issuer misrepresents provenance, so the Hub always shows the issuer next to the title (see [Hub](../ecosystem/hub.md)).

## Provenance and the registry

Aggregate facts derived from provenance (how many attestations an issuer has produced, which integrators publicly recognize it) are published as labeled statistics in the [registry](./registry.md). They inform a consumer's decision and never replace it.

## Implementation

Status: implemented for attestations.

- `AchievementAttestation` carries issuer, subject, `issued_at`, and an opaque `proof`. The namespaced `GlobalId` is in [`ids.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/ids.rs). Every committed ledger entry has a position (`seq`) and a hash chained to its predecessor, the log-side half of "when" and "where in history" ([`crates/chain/src/postgres.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/chain/src/postgres.rs)).
- The attestation's `proof` names the `key_id` that signed it, so "which key signed this claim" is answerable from the attestation alone. The key's validity window and status come from the issuer's key history ([issuers](./issuers.md)).

## Related

- [Trust model](./trust-model.md), [achievements and attestations](./achievements-and-attestations.md), [revocation](./revocation.md), [issuers](./issuers.md)
- [Registry](./registry.md), [future layers](../architecture/future-layers.md)
- [Settlement](../architecture/settlement.md)
