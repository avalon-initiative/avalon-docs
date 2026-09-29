# Revocation

**Status:** Partially implemented — individual attestation revocation and instance deletion are built; supersession, reinstatement, and issuer-level suspension are Planned.

Revocation adds history and never erases it. An attestation that was issued and later revoked leaves two facts in durable history, "Integrator A issued it" and "Integrator A later revoked it", and both stay visible. The same applies at the issuer level: suspending or revoking an issuer is an appended entry, not a deletion of everything it ever signed.

## Individual revocation

```text
achievement.issued          (Integrator A, key k1, 2027-03-14)
    Dragon Slayer -> User X
        │
        ▼
achievement.revoked         (Integrator A, key k1, 2027-05-02)
    references the attestation above
    reason_code: cheating
```

Current state, as a projection:

```text
User X: Dragon Slayer (Ashen Realms)
    status:  REVOKED
    issued:  2027-03-14
    revoked: 2027-05-02, cheating
```

The original issuance remains observable, and the Hub shows both rather than an empty slot.

## Reason codes and visibility

Not every reason means the same thing for what should stay visible. `reason_code` is a real, extensible vocabulary (`RevocationReasonCode`) where each known code carries a default visibility policy.

| Reason code | Meaning | Stays visible after revocation? |
| --- | --- | --- |
| `cheating` | A real fact about the subject: they earned it, then had it pulled for cause. | Yes. Both `issued` and `revoked` stay in current-state views. |
| `policy_change` | Not about the subject: a ruleset or definition changed after the fact. Having earned it under the old policy still matters. | Yes. |
| `mistake` | An operator error. Showing "subject had X, then had it revoked" would be misleading. | No. It disappears from current-state views, as if never issued. |
| `duplicate` | A duplicate of another still-valid claim. | No. |

A developer who accidentally publishes a `Beta Tester Badge` to production issues and then revokes it with `mistake`. A direct lookup by id, `GET /attestations/{id}`, still shows both entries, because raw history is never filtered regardless of reason code. A listing-shaped current-state read such as `GET /me/achievements` omits the attestation entirely.

An unrecognized code defaults to visible. The vocabulary mirrors the event-kind `Known`/`Other` open-enum shape, so a code this build does not recognize (including every revocation recorded before the vocabulary existed) decodes to `Other` rather than an error, and `Other` never hides. Failing toward visibility is the safe default, since silently hiding history because a code was not recognized would be the wrong failure. Adding a known code later is additive and never changes what an already-recorded code means.

## Issuer-level suspension and revocation

```text
issuer.suspended   (network, 2027-06-01)  ->  issuer.reinstated (2027-06-20)
issuer.revoked     (network, 2028-01-10)
```

Neither deletes historical claims. A consuming integrator reads the timestamps and applies its own policy ([trust model](./trust-model.md)). **Planned:** the issuer status values exist (`Active`, `Suspended`, `Revoked`, `Deprecated`) and validity reads whichever is set, but no event kind exists for these transitions and nothing can set a non-active status yet. The network-level authorization model for doing so is still open (see [issuers](./issuers.md)).

## Point-in-time validity

Validity is a function of history and a timestamp, not a flag on a row:

```text
valid(attestation, history, at) =
    attestation not revoked or superseded as of `at`
  AND issuer not suspended/revoked as of `at`   (per consumer policy)
  AND signing key valid as of attestation.issued_at
  AND attestation well-formed for its schema/version
  AND attestation not expired as of `at`
```

"Valid at issuance" and "valid now" are different questions and both must be answerable. See [issuers](./issuers.md) for the key half. The implemented subset is described in the [trust model](./trust-model.md#implementation).

## Who may revoke

Only the original issuer, signing with a key valid at revocation time (or a legitimate successor key). Never the node operator and never the subject. An issuer-level suspension is a separate, explicitly authorized network operation with its own audit trail; see the [security model](./security-model.md).

## Scenarios

**C: Integrator A revokes Dragon Slayer.** History shows issued and revoked, the Hub shows both, Integrator B's validity check flips at the revocation timestamp, and rebuilding the projection from history reproduces the same status.

**F: Integrator A's signing key is compromised.** A or the network revokes the key as of time T. Claims signed at T-1 stay authentic and valid, claims signed at T+1 are rejected, and nothing historical is destroyed.

## Mechanics

The design is a signed revocation entry (reason code, timestamp, signed by an issuer key valid at revocation time); **supersession**, an issuer replacing an attestation instead of revoking and reissuing; **reinstatement**, a later entry reversing a revocation with validity computed by walking history; and issuer-level suspend and revoke as their own events. Only the first is built.

## Implementation

Status: individual revocation and instance deletion implemented; the rest is planned.

- **Individual revocation.** `AttestationStatus { Active, Revoked }` is computed by `attestation_status_at`, never stored on the attestation. `POST /attestations/{id}/revoke` inserts an append-only row into a separate revocations table (the attestation table is never touched), requires the caller to authenticate as the original issuer, and verifies an embedded signature over the canonical revocation bytes against the issuer's key history at revocation time. It shares the cryptographic core of issuance verification, and emits `achievement.revoked` or `milestone.revoked`. Revoking twice is a conflict error and not a silent no-op. The revocations table is capped at one row per attestation because no reinstatement path exists to need more; building reinstatement means lifting that constraint. The SDKs wrap this call for issuers.
- **Not built:** supersession (`attestation.superseded`, no emitter), reinstatement (no event kind), issuer-level transitions.
- **Entity and instance deletion.** The same "append, never erase" standard applies to [Integrator Space](./integrator-space.md) instance data. A deleted instance gets a `game_data.deleted` tombstone event referencing the original by id, never a physical delete, and the instance's content is never mutated. The read endpoint filters deleted instances, while raw ledger history keeps them. A rebuild from the ledger alone reproduces the tombstoned state. The tombstone's `reason_code` is deliberately free text and not the revocation vocabulary: that vocabulary describes why an issuer revoked something it issued (a validity judgment), while instance deletion is the subject retiring their own published data, which is not a validity judgment.
- `PermissionGrant.revoked_at` still uses a mutable-field shape; grants are not promised-durable history and are a projection concern.

Code: [`crates/server/src/attestations.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/attestations.rs), [`crates/protocol/src/revocation.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/revocation.rs), [`crates/server/src/integrator_data.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/integrator_data.rs).

## Related

- [Trust model](./trust-model.md), [achievements and attestations](./achievements-and-attestations.md), [issuers](./issuers.md), [provenance](./provenance.md)
- [Identity recovery and rollback](./identity/recovery.md#post-compromise-rollback) applies the same compensating-event posture
- [Protocol events](./protocol-events.md), [Integrator Space](./integrator-space.md)
