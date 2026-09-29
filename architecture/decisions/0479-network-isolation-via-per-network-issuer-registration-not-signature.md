# ADR-0479: Network Isolation Via Per-Network Issuer Registration, Not Signature Binding

**Status:** Accepted — decided 2026-09-19

Original record: [avalon-protocol#479](https://github.com/avalon-initiative/avalon-protocol/issues/479). The text below is preserved as recorded; `#N` references are avalon-protocol issue numbers and file paths are as they were when the decision was made.

## Context

`network_id` is baked into the settlement ledger's hash chain and Signed
Tree Head, but attestation/event signatures themselves
(`attestation_signing_bytes`/`revocation_signing_bytes` in
`crates/protocol/src/achievements.rs`) carry no network scoping — a
signature verifies identically regardless of which network it's presented
to. With `dev`/`int`/`mainnet` becoming real, separate deployments, this
raised a real question: can a signature produced on a test network be
presented as authentic on mainnet, and if so, is that acceptable? Full
discussion and alternatives considered: #476.

## Decision

Attestation/event signatures stay network-agnostic — no change to what
gets signed. Network isolation is enforced instead by a per-network,
self-service issuer registration gate: each network's server maintains its
own registry of admitted issuer public keys, and rejects writes from
unregistered keys at submission time, before they reach the append-only
ledger. Registration is permissionless and SDK-driven (no review/approval
queue) but explicit and per-network — a key used on `int` is not
automatically admitted on `mainnet`. `dev` and `int` auto-approve
registration; `mainnet` does not gate on identity/review, only on the
explicit registration step having happened.

The SDK/CLI requires an explicit caller-declared target network for any
write, and cross-checks it against the connected server's actual
`network_id` (via its Signed Tree Head) before proceeding, surfacing a hard
error on mismatch rather than silently sending to the wrong network.

A deliberate mainnet-N -> mainnet-(N+1) genesis reset is handled as a bulk
state import (final ledger checkpoint + issuer registry carried over to the
new network), not per-event re-signing by original issuers.

## Consequences

- New server-side surface: a per-network issuer registration
  endpoint/table gating ledger write acceptance, needed before real
  `dev`/`int`/`mainnet` deployments carry live issuer keys.
- SDK/CLI need STH-based network verification before this is usable
  end-to-end (ties into #91, currently unbuilt for `crates/sdk`).
- Authenticity (signature-valid) and network-admission (registered on this
  network) become two distinct checks, composing with the existing
  authenticity/validity/recognition split from #76.
- `docs/architecture/network-trust-anchors.md` and
  `docs/architecture/achievements-and-attestations.md` need updates once
  implemented to document the registration-gate model.
- Third-party/integrator-run `dev`/`int` networks still need their own
  `network_id` naming/registration story — explicitly out of scope here,
  tracked as an open follow-up.

## Related

- #476 — the decision ticket this closes, with full context/alternatives
- [ADR: Issuance Is Signed, Not Merely Authenticated](https://github.com/avalon-initiative/avalon-protocol/issues/76)
- [`network_id` genesis/hashing](https://github.com/avalon-initiative/avalon-protocol/issues/173)
- [Signed Tree Heads and public read endpoints](https://github.com/avalon-initiative/avalon-protocol/issues/210)
- [SDK node discovery](https://github.com/avalon-initiative/avalon-protocol/issues/91)
- `docs/architecture/network-trust-anchors.md`, `docs/architecture/achievements-and-attestations.md`
