# ADR-1135: Recovery authorizes a new signing key with guardian signatures, verified by mirrors

**Status:** Accepted — decided 2026-10-02

Original record: [avalon-protocol#1135](https://github.com/avalon-initiative/avalon-protocol/issues/1135), titled "Decide how recovery authorises a new signing key and how mirrors verify it". The text below is preserved as recorded; `#N` references are avalon-protocol issue numbers and file paths are as they were when the decision was made. The decision is not built yet; see the implementation state at the end.

## Context

With self-certifying identity ids (#1129) and verified key changes (#1130), a mirror accepts a new signing key only if an already-active key of the identity authorized it. After guardian-approved recovery with every signing key lost, nothing can authorize a replacement, and recovery adds only a passkey, which cannot sign the event envelope.

The other recovery events are also unverifiable on a mirror today, so a hostile shard can forge them:

- `identity.recovery_configured` carries the guardian ids and threshold with no signature or commitment, and adding guardians needs only a session. A shard can name colluding guardians.
- `identity.recovery_approved` carries no guardian signature, and its counters and delay are shard-asserted.
- `identity.recovered` carries no new key, guardian set, or signatures. It is also the only event allowed to resolve a forked identity chain, so a forged one unfreezes a fork on any mirror.
- Signature checks on key events happen at write time and the signature is not stored in the event.

## Decision

Option 1, with two additions.

- Recovery follows Option 1: a signed commitment of the guardian set, signed guardian approvals over a challenge binding the identity, the new public key, the request id, an expiry, and the commitment, and one atomic `identity.recovered` v2 carrying the new key, the approvals, and the revocation of every prior key.
- A guardian must accept the responsibility. Naming someone is an invitation; only guardians whose signed acceptance (by an active key of the guardian, over the commitment) is in the ledger count towards the threshold, and the owner cannot finalize a configuration until at least the threshold have accepted. A guardian can resign with a signed event at any time. This replaces today's opt-out model, where a guardian is active the moment they are named.
- The whole flow needs a usable mechanism in the Hub: inviting guardians, a guardian inbox to accept or decline with the owner's details shown, configuration status (accepted, pending, and declined against the threshold), a guardian approval screen that shows the new device's key fingerprint to verify out of band, and a prominent notice to every existing device of the owner when a recovery is requested so the owner can veto during the delay.
- Another registered device is the first recovery path, and guardian recovery is the last resort for total key loss. Any device holding an active signing key can authorize a new device through the existing device grant approval, with no guardians involved, and the Hub should offer that path first.

## Why

Recommended: Option 1.

- Embed the signature in `identity.signing_key_added` and `identity.signing_key_revoked` (needed by #1130 regardless).
- Commit the guardian set: `identity.recovery_configured` carries a commitment over the identity, threshold, and sorted guardian ids, signed by an active owner key and bound to the chain position. Every configuration needs a fresh owner signature, including adding a guardian.
- Guardian approvals are signed over a challenge binding the identity, the new public key, the request id, an expiry, and the commitment. Recovery requires the new Ed25519 signing key to be named at request time.
- `identity.recovered` v2 is the single atomic authorization event: new key, the committed set, at least threshold guardian signatures, and revocation of every prior key. A mirror verifies the commitment from chain history, the guardians' signatures against their own verified chains, the expiry, and the delay. A second `recovered` for the same request id is rejected, `recovery_cancelled` is signed, and the id never changes (only the genesis key is checked against the derivation).

## Alternatives considered

- Option 2: signed approvals as their own chain-critical events with a smaller `recovered`. Smaller events and chain-ordered approvals, but two guardians approving on two shards at once is routine and would fork a recovering identity under the current fork rule, so it needs a new non-forking approval class.
- Leave recovery passkey-only and mirror-invalid: simplest, but a recovered identity could never sign anything on the network.

## Consequences

- Event versions bump for six recovery and key events, and the new signing bytes need conformance vectors (commitment encoding, challenge, finalize cases).
- Revoking every prior key on recovery means a malicious guardian quorum can take an identity from an owner who still holds an old key; the owner's veto during the delay is the defense.
- The delay is only as strong as timestamp clamping plus the veto path, since mirrors compare timestamps.
- Open questions: a guardian acceptance signature (today there is no accept step); the tie rule when two shards finalize different valid recoveries from the same chain head (suggested: the smaller entry hash); the maximum number of guardian signatures per event; whether guardian friendship can be relied on (friend events are unsigned, so no).

## Implementation state

This section is not part of the recorded decision. Recovery today still adds only a passkey, the guardian commitment, acceptance, and signed approvals do not exist, and `identity.recovered` carries only a request id and device label; see [recovery](../../protocol/identity/recovery.md#recovery-restores-a-passkey-not-a-signing-key).

## Related

#1129, #1130, [ADR 1129](1129-identity-ids-are-self-certifying.md), [recovery](../../protocol/identity/recovery.md).
