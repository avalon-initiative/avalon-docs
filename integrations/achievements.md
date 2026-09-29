# Issuing and verifying achievements

**Status:** Implemented — definition, issuance (single and bulk), reading, verification, and revocation are available in the SDKs; the exact call names differ per language.

An achievement is a signed attestation: a claim by the integrator, signed with its own key, that an identity earned something. Any other integrator can verify who issued it and whether it is still valid, then decide for itself whether it matters. This page covers the lifecycle from an integrator's point of view; the model behind it is in [achievements and attestations](../protocol/achievements-and-attestations.md) and the [trust model](../protocol/trust-model.md).

## 1. Register the integrator

Create the integrator and hold its private signing key. See [building an integration](building-an-integration.md).

## 2. Register as an issuer on the target network

Before issuing on a real network, the integrator's signing key must be admitted to write on that network. A signature valid against the key history is not enough by itself; this is per-network isolation ([ADR 0479](../architecture/decisions/0479-network-isolation-via-per-network-issuer-registration-not-signature.md), [network trust anchors](../protocol/network-trust-anchors.md)).

Issuer registration requires the integrator to declare which network it means, either the exact `network_id` or a deployment tier (dev, int, mainnet). The SDK refuses client-side, before sending anything, if the server's own signed tree head verifies as a different network. A mismatch error therefore means the server is a genuine Avalon network, just not the intended one, most often because configuration points at the wrong environment. An unverified error means the server's claimed network could not be confirmed at all, and registration is refused regardless of what was declared.

## 3. Define the achievement

An achievement definition (a key, name, and description) is created under the integrator, proven by the integrator's key through a challenge-response exchange. Definition create, update, and list are covered by the SDKs, as are milestones for apps and services.

## 4. Obtain consent

The person must grant `achievements.issue`, and `achievements.read` if the integrator also wants to read their history. See [capabilities](capabilities.md).

## 5. Issue

Issuance signs the attestation locally with the integrator's key; the server never sees the private key, only a detached signature. Two independent proofs go on the wire: a challenge-response proving the integrator's key is making this call now, and a signature over the attestation's canonical bytes proving that key authorized this specific attestation. Signing bytes are pinned by conformance vectors so every SDK and the server agree ([SDK design](../sdk/design.md#cross-sdk-conformance)).

Issuance always targets the session's own identity, matching the consent model: the person granted this for themselves. It carries an `Idempotency-Key`, so a transient failure never produces a duplicate attestation. Bulk issuance submits N ordinary, independent attestations, not one claim set.

## 6. Read a person's history

With `achievements.read`, the integrator receives the identity's attestation history across all issuers. Each entry carries authenticity, validity, and history as the server computed them, as separate fields. There is deliberately no recognition field. Authentic (the signature verifies), valid (not revoked), and recognized are three questions, and recognition is a judgment only the consuming integrator can make: does it trust this issuer, and does the claim matter to it? Evaluate it against your own policy and never assume the SDK decided.

## 7. Verify one attestation

`GET /attestations/{id}` is public and unauthenticated. It returns the same authenticity, validity, and history for a single attestation, to anyone, not only its subject.

## 8. Revoke

Only the issuer that issued an attestation can revoke it. History is append-only: a revocation is recorded and never erased, and a later read shows the attestation as invalid with a second history entry. Revoking an already-revoked attestation is a conflict, not a silent no-op. Revoking someone else's attestation is refused. A bulk-issued attestation revokes exactly like any other, by its own id. See [revocation](../protocol/revocation.md).

## Related

- [Achievements and attestations](../protocol/achievements-and-attestations.md)
- [Trust model](../protocol/trust-model.md)
- [Revocation](../protocol/revocation.md)
- [Issuers](../protocol/issuers.md)
- [Capabilities](capabilities.md)
