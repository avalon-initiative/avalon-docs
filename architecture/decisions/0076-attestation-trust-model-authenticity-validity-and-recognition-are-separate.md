# ADR-0076: Attestation Trust Model — Authenticity, Validity, and Recognition Are Separate

**Status:** Accepted — decided 2026-09-08

Original record: [avalon-protocol#76](https://github.com/avalon-initiative/avalon-protocol/issues/76). The text below is preserved as recorded; `#N` references are avalon-protocol issue numbers and file paths are as they were when the decision was made.

## Context

"Is this achievement real?" is three different questions, and conflating them is
how a protocol ends up either trusting everything or appointing itself the judge of
what an achievement is worth. Three games can all issue an authentic, validly-signed
`Dragon Slayer`: one after a brutal endgame raid, one after a different hard
achievement, and one by letting every player click a button. No signature scheme
can tell those apart, and Avalon shouldn't pretend to.

`crates/protocol/src/achievements.rs` already models an attestation with an issuer,
subject, proof, and a `TrustRelationship`, but nothing states which question each
part answers.

## Decision

Avalon separates three concepts and never collapses them:

**Authentic** — did the claimed issuer actually issue this? Established by the
issuer's signature over the attestation, verified against the issuer's registered
key that was legitimate at the time of issuance. Universal: the answer is the same
for every observer.

**Valid** — is the attestation currently in force? Not revoked, not superseded, not
issued by an issuer that was suspended or revoked at the relevant time, not signed
by a key that was already revoked at issuance, well-formed against its declared
schema and version, not expired. Also universal, computed from protocol history.

**Recognized** — does a particular consuming game choose to honor this claim?
Entirely contextual. Expressed as that game's own policy, scoped by issuer, claim
type, achievement schema, version, time period, specific game event, asset class, or any
other dimension the consumer cares about. Two games can look at the same authentic,
valid claim and decide differently, and both are correct.

From this:

- **A signature proves who signed a claim. It does not prove the claim is
  meaningful.** There is no cryptographic mechanism that stops an issuer from
  signing a meaningless but authentic claim, and Avalon does not claim one exists.
- **Avalon records provenance; it does not determine universal meaning.** The
  protocol never computes a network-wide "this achievement is prestigious" bit, a
  game score, or a trust ranking. Statistics and recognition relationships are
  facts that inform a consumer's policy; they never decide it.
- **Consumers choose what they recognize.** No network-wide trust list is imposed.
  A game with ten players is not automatically untrusted; a game with ten million
  is not automatically trusted.
- **Same display name, different provenance.** `game:a:achievement:dragon_slayer`
  and `game:c:achievement:dragon_slayer` are distinct claims that happen to share a
  title. Namespaced `GlobalId`s make the distinction; the Hub shows the issuer next
  to the title.

## Consequences

- #33 verifies authenticity and validity as separate steps with separate results,
  and exposes recognition as a consumer-side policy evaluation, not a boolean the
  server returns.
- `TrustRelationship` grows scoping (claim type, schema, version, time window)
  rather than staying a single unscoped issuer-level bit.
- The SDK surfaces the three results distinctly; a game must be able to say "show
  me authentic-and-valid claims I don't recognize" (for display) as well as "only
  claims I recognize" (for gameplay effects).
- The Hub (#77) displays every authentic, valid claim with
  its provenance regardless of any game's recognition policy, and lets the player
  feature, hide, or filter — it never ranks them.
- The game registry may publish derived statistics and public recognition
  relationships ("Game A recognizes Game B's game event results") as facts. It
  never publishes a composite trust score.
- `docs/architecture/trust-model.md` is normative; `Proposal.md` §9 stays the
  narrative.

## Related

#33, #32, #80, #81, #89, #77
