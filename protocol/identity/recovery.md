# Recovery and Rollback

**Status:** Partially implemented — guardian recovery restores a passkey only and its events are not signed by the guardians; recovery finalization is caller-triggered, and rollback covers only reversals that need no other party.

If an identity's owner loses every passkey, the only path back is social recovery: a set of the owner's friends approve a new device after a mandatory public delay. If an attacker held credentials before recovery, rollback lets the recovered owner supersede the attacker's actions with signed compensating events, without rewriting history. Both are part of [identity](../identity.md).

## Layers of recovery

The options are not mutually exclusive:

- **Multiple passkeys** registered before a loss is the cheap mitigation for losing one device. It does nothing for someone who registered only one and lost it.
- **Social recovery** with M-of-N guardians, described below, is the answer for losing every device at once. It composes with the network-owned [social graph](../social-graph.md) and needs no centralized custodian.
- **A custodial fallback** (email or SMS) is deliberately not a default. It would reintroduce the shared-secret, centralized-trust surface the design exists to eliminate, and could only ever ship as a clearly labeled, separately opted-into weaker tier. It does not exist.

The full order of fallbacks is on [the recovery ladder](./recovery-ladder.md). Onboarding must make the total-loss consequence of a single passkey loud and explicit for an owner without guardians. With no passkey and no guardians configured, the identity is permanently lost; nobody can look it up and reissue it.

## Social recovery via M-of-N guardians

An owner designates guardians drawn only from their current friends, plus a threshold M of N. Changing the set requires the identity's current session (and a fresh signature to remove a guardian or raise the threshold), so an attacker holding only a not-yet-valid new device can never reach it. Naming a guardian is unilateral and takes effect immediately (Planned: guardians must accept before they count, per [ADR 1135](../../architecture/decisions/1135-recovery-authorises-a-new-signing-key-with-guardian-signatures.md)), but a guardian can list every identity relying on them and remove themselves without the owner's cooperation. A self-removal that drops the owner below their threshold clamps the threshold to the new guardian count rather than leaving an unsatisfiable M-of-N.

**Guardian ids are public by design.** `identity.recovery_configured` carries the guardian ids and the threshold, and the ledger is public and permanent, so anyone can see which identities an account relies on to recover. Identity ids are hashes, not names, so this reveals a relationship between pseudonymous identities and nothing about the people behind them. Choosing guardians therefore discloses those links forever; an owner who cannot accept that should use a dedicated identity as the guardian. Hiding the set (for example behind a commitment) would change the signed payload and is a decision to reopen before the format freeze, not after.

Recovery is a four-stage state machine, one `recovery_requests` record per attempt:

1. **Request.** From a new device with no valid session, a caller names the identity and completes a WebAuthn registration ceremony for that device. This is the one deliberate exception to "every route requires a session". It is not an open door: the identity must exist and have guardians configured, at most one active request may exist per identity, and a rolling 24-hour window caps how many requests may be initiated against one identity. The new passkey is captured but is not a valid credential until finalization.
2. **Approval.** Each guardian approves independently, and only a current guardian (not a former one) may. When approvals reach the threshold in effect at request time, frozen so a guardian change mid-attempt cannot alter what the attempt needs, the request enters the delay phase.
3. **Mandatory public delay.** A configurable delay (48 hours by default) must elapse with no veto. The delay and its countdown are public: the recovery-status endpoint for an identity requires no authentication, because the delay is meant to be a public marker on the identity and not something only the owner happens to be told.
4. **Veto or finalize.** The original owner (any session for the identity) or any current guardian may cancel before finalization. Finalization is public and idempotent, and grants nothing beyond what approvals and the elapsed delay already authorized. In one transaction it revokes every passkey the identity had, each with its own `identity.passkey_revoked` event, inserts the pending passkey as the identity's only passkey, ends every session of the identity, and discards the identity's in-flight device pairings and cross-node login requests, which would otherwise mint a session on their next poll. Whoever held a credential or a session before recovery is locked out of the account; the signing keys are untouched (below).

No node operator has a path that bypasses guardian approval or the delay: finalize acts only on durably recorded approvals and elapsed time. Every phase transition is durable history (`identity.recovery_configured`, `.recovery_requested`, `.recovery_approved`, `.recovery_cancelled`, `identity.recovered`; see the [event catalogue](../protocol-events-catalogue.md)).

## Recovery restores a passkey, not a signing key

Finalization replaces the passkeys with the pending one and records `identity.recovered` (request id and device label). It adds no Ed25519 signing key and revokes none, so a recovered owner can log in again but cannot author anything that needs a signing key. The converse also holds: signing keys survive recovery, so a stolen signing key cannot be removed by recovery. Recovery ends the sessions that key produced, but an attacker who holds it can still author signed events, and can sign a cross-node login grant, until the owner revokes that key with another active one. A new signing key is authorized only by a device grant approved by an already-active key ([authentication](./authentication.md#cross-device-pairing-for-clients-without-webauthn)), so an identity that has lost every signing key cannot get one back through recovery today. For the same reason the last active signing key cannot be revoked.

The recovery events carry no signatures from the owner or guardians: `identity.recovery_configured` names the guardian ids and threshold, `identity.recovery_approved` carries counts the node asserts, and `identity.recovered` carries no new key or guardian evidence. A mirroring node therefore cannot verify them from the ledger. Planned: the design in [ADR 1135](../../architecture/decisions/1135-recovery-authorises-a-new-signing-key-with-guardian-signatures.md), with a signed guardian commitment, signed guardian acceptance and approvals, and one atomic `identity.recovered` v2 that carries the new key. None of it is built.

Not built: a background sweep that finalizes an eligible request the moment its delay elapses (today the recovering device's client triggers finalize), and full Rust and C# SDK surface for this flow beyond the account-level session helpers.

## Post-compromise rollback

Recovery adds a new passkey and completes the request; it does not undo what an attacker did while holding the old credentials. Rollback is the self-service way for a recovered owner to supersede those actions. It is a signed, append-only compensating event (`friend.relationship_reversed`, `guild.membership_reversed`), never a generic undo: the original ledger entry is neither rewritten nor deleted, the same posture [revocation](../revocation.md) takes. Projections apply it idempotently, so a rebuild from the ledger reproduces the same state.

**Eligibility window.** An event is eligible only if it was authored by this identity, its timestamp is strictly before `completed_at` of the identity's latest completed recovery, and it is at or after `since`, a required timestamp the owner supplies to declare when they believe the compromise began. Nothing records when a compromise began, so the window is bounded above by the recovery and below by the owner's own declaration. With no completed recovery nothing is eligible (`ROLLBACK_NO_COMPLETED_RECOVERY`); a `since` at or after the recovery time is `INVALID_ROLLBACK_WINDOW`.

**What can be reversed.** Only reversals that need no other party's action are offered.

| Original event | Reversal | Condition |
| --- | --- | --- |
| `friend.accepted` | friendship removed | the friendship still exists |
| `guild.member_added` (subject is the owner) | membership removed | still a member, and not the guild's owner (who must transfer ownership or delete the guild) |
| `guild.member_removed` with reason `left`, actor is the owner | membership restored | the guild exists, its join policy is open, and the identity is not currently a member |
| `friend.removed` | not reversible | restoring needs the counterparty; send a new friend request |
| `guild.member_removed` from an invite-only guild | not reversible | rejoining needs an invitation from a guild authority |
| any event already reversed | not reversible | a compensating event already references it |

A restored membership is granted at the default member role, since any previous role is a grant that needs a guild authority. Removing a membership also clears `main_guild` if it pointed at that guild.

`GET /me/rollback/candidates?since=<RFC 3339>` lists every eligible event with `reversible`, `reason`, and `already_reversed`. `POST /me/rollback/{event_id}/reverse` re-validates the window and current state and returns `{ reversal_event_id }`. It is in the fresh-signature tier, signing `avalon:rollback.reverse:v1:<event_id>:<identity_id>:<since>` with `since` exactly as sent. Refusals use `ROLLBACK_EVENT_NOT_ELIGIBLE`, `ROLLBACK_NOT_REVERSIBLE`, and `ROLLBACK_ALREADY_REVERSED`.

**Deferred:** reversing anything that changes another party's state (restoring a removed friendship, re-inviting into an invite-only guild, restoring previous roles), an open-ended dispute flow, and expiry of the eligibility window.

## Implementation

- Recovery state machine and pure invariant functions: [`recovery.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/recovery.rs). The delay is set by `AVALON_RECOVERY_DELAY_HOURS`.
- Rollback: [`rollback.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/rollback.rs).
- Endpoints: `/me/recovery/*`, `/recovery/requests/*`, `/identities/{id}/recovery/status`, `/me/rollback/*` in the [OpenAPI document](https://github.com/avalon-initiative/avalon-protocol/blob/main/docs/generated/openapi.json).

## Related

- [The recovery ladder](./recovery-ladder.md), [identity](../identity.md), [authentication and signing keys](./authentication.md), [per-identity event chains](./event-chains.md)
- [Social graph](../social-graph.md), [revocation](../revocation.md), [security model](../security-model.md)
