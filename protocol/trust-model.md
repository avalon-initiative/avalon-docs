# Trust Model

**Status:** Partially implemented — authenticity and recognition evaluation are built; validity is a strict subset of the full design.

Avalon separates three questions about any attestation and never collapses them: is it authentic, is it valid, and is it recognized. A signature proves who signed a claim, not that the claim is meaningful. Authenticity and validity are universal facts, and recognition is contextual: consuming integrators choose what they recognize, and the network never chooses for them. The decision is recorded in [ADR 0076](../architecture/decisions/0076-attestation-trust-model-authenticity-validity-and-recognition-are-separate.md). The model applies to any issuer and consumer of attestations; examples use games because games are the first live use case.

## The three questions

**Authentic:** did the claimed issuer actually issue this? Established by the issuer's signature over the attestation, verified against the issuer's registered key that was legitimate at the time of issuance. The answer is the same for every observer.

**Valid:** is the attestation currently in force? Not revoked, not superseded, not issued by an issuer that was suspended or revoked at the relevant time, not signed by a key already revoked at issuance, well-formed against its declared schema and version, not expired. Also universal, computed from protocol history at a point in time.

**Recognized:** does a particular consuming integrator choose to honor this claim? Entirely contextual, expressed as that integrator's own policy. Two integrators can look at the same authentic, valid claim and decide differently, and both are correct.

| | Who decides | Varies by observer? | Where it lives |
| --- | --- | --- | --- |
| authentic | cryptography | no | signature and issuer key history |
| valid | protocol history | no | revocation and issuer-status entries |
| recognized | the consumer | yes | the consumer's policy |

## The limitation, stated plainly

No cryptographic mechanism can stop an integrator from issuing a meaningless but authentic claim. If Integrator C controls its issuer key and signs `Dragon Slayer` for every user who clicks a button, the signature proves C issued it. It cannot prove C made it difficult, fair, or prestigious. Avalon does not claim otherwise, and no future feature should imply it does.

## Scoped trust policies

Recognition is a consumer-side policy, scoped however the consumer needs:

```text
Integrator B: recognition policy

  issuer game:ashen-realms
      achievements               RECOGNIZED
      integrator event results   RECOGNIZED
      asset provenance           RECOGNIZED
      currency claims            NOT RECOGNIZED

  issuer game:worldzero
      achievements               RECOGNIZED  (schema achievement.v1+, since 2027-01)

  issuer game:random-mmo-47
      everything                 NOT RECOGNIZED
```

Scoping dimensions include issuer, claim type, achievement schema and version, time period, a specific integrator event, and asset class. Avalon may offer standard policy mechanisms later and never imposes a network-wide trust list.

## Under issuer suspension or revocation

When an issuer is suspended or revoked (see [revocation](./revocation.md)), the protocol exposes the facts and timestamps. The consumer chooses: reject new claims but honor historical ones, reject everything from that issuer, or something else. No default is imposed.

## Statistics inform; they never determine

The [registry](./registry.md) publishes derived facts (observed identities, attestations issued, integrators that publicly recognize an issuer). A consumer may write "accept event results from issuers with at least N observed identities and M recognizing integrators", and that is the consumer's rule. Avalon never enforces "integrators above N are trusted", never publishes a composite integrator score, and never turns the recognition graph into a verdict. A ten-player integrator is not automatically malicious and a ten-million-player one is not automatically trustworthy.

## Recognition relationships are facts

An integrator may publish its policy ("Integrator A recognizes Integrator B's achievements and event results"). Avalon records that as a fact and the registry can show it. A claim can be valid without being recognized by anyone, and recognized without being especially meaningful. Recognition is never validity.

## Trust in the log itself is a separate question

Authenticity, validity, and recognition concern claims made in the log. Whether the log's own head can be trusted, and whether a fork would be caught, has its own mechanism. Independent witnesses cosign heads they have checked for append-only growth, each verifier keeps its own bounded known list of them, and two conflicting majority-cosigned heads drawn from one list must share a witness, which is proof of equivocation from signatures alone. That is resistance to a captured or rewriting operator and not a proof, and it does not decide what any consumer recognizes. See [witness cosigning](./witness-cosigning.md) and [network trust anchors](./network-trust-anchors.md).

## Implementation

Status: partially implemented.

- **Authentic (implemented).** `verify_authenticity` in the chain crate resolves the signing key against the issuer's full key history at `issued_at` and checks the signature, returning `Authentic { key_id }` or `NotAuthentic { reason }` and never a bare boolean. It lives in the `chain` crate because it does real Ed25519 verification, which the I/O-free `protocol` crate avoids. The same function backs the issuing endpoint and the public read. A claim stays authentic after its key is later revoked; a claim "issued" after revocation is not.
- **Valid (partial).** `validity(issuer_status, attestation_status)` is `Invalid` if the attestation's own status (computed from its revocation history, never a stored flag) is `Revoked`, otherwise `Valid` if the issuer's current status is `Active`. Not yet implemented: supersession (no event kind exists), point-in-time issuer-status history (nothing records when a status changed, so an issuer suspended today reads as suspended for claims issued before the suspension too; also no code path can set a non-active status, see [issuers](./issuers.md)), and schema and version well-formedness checks.
- **Recognized (implemented as a pure function).** `TrustRelationship` carries scopes (`claim_kind`, `schema`, `min_version`, `issued_after`, where `None` matches anything) and `recognize(...)` returns `Recognized` or `NotRecognized { reason }`. It is evaluated entirely on the consumer's side and is exhaustively unit-tested.
- **Wire behavior.** `GET /attestations/{id}` is public and unauthenticated. It recomputes authenticity and validity on every read, never from storage, and returns a `history` array (issuance, plus the revocation with its reason). It has no `recognition` field, and a test asserts the field's absence, keeping recognition the consumer's computation at the wire level.
- **Published recognition policy (implemented).** An integrator can publish a directional recognition of another integrator, readable in both directions; see [registry](./registry.md#recognition-relationships).

Code: [`crates/chain/src/attestations.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/chain/src/attestations.rs), [`crates/protocol/src/achievements.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/achievements.rs), [`crates/server/src/attestations.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/attestations.rs).

## Related

- [Achievements and attestations](./achievements-and-attestations.md), [revocation](./revocation.md), [issuers](./issuers.md), [provenance](./provenance.md), [registry](./registry.md)
- [Witness cosigning](./witness-cosigning.md), [network trust anchors](./network-trust-anchors.md)
- [ADR 0076](../architecture/decisions/0076-attestation-trust-model-authenticity-validity-and-recognition-are-separate.md)
