# ADR-1152: Decision: consensus rule changes ship in three steps, driven by readiness instead of a calendar

**Status:** Accepted — decided 2026-10-02

Original record: [avalon-protocol#1152](https://github.com/avalon-initiative/avalon-protocol/issues/1152). The text below is preserved as recorded; `#N` references are avalon-protocol issue numbers and file paths are as they were when the decision was made. The activation model is planned; see the implementation state below.

## Context

A change to what is valid (signing bytes, STH format, evidence caps, schema rules) cannot be switched on by each operator whenever they happen to upgrade. If upgraded and non-upgraded nodes disagree on validity, verifiers disagree about which heads and events are good.

Constraints that come from how the network is built:
- **There is no global ledger.** The ledger is a set of per-shard append-only chains, each with its own `tree_size`. There is no network-wide height to activate at.
- **No node, key or operator is required for the network to keep operating** (the stated goal of witness cosigning, #942). An activation mechanism that needs one key to publish a schedule reintroduces the single pinned authority that epic removes.
- **Verification is local.** Each verifier decides validity using its own known list of witnesses. A "fork" here is verifiers disagreeing, not a global chain split.
- **Today's version machinery is advisory.** `protocol_version` is the build version, with a compiled-in peer floor (`MIN_SUPPORTED_PEER_VERSION`). It is never used for validity, by design (#308).

## Decision

**1. Separate the rule version from the build version.** Validity is governed by an integer `rules_version`, independent of semver. A build supports a range of rules versions. Nodes advertise `rules_supported` (a range) and `rules_emitting` (the version they author with) in announce and `/info`.

**2. Validity is a function of the event, never of when it is seen.** Every signed structure declares the `rules_version` it was authored under, and is validated under that version forever. Raising the rules version never makes an existing event or head invalid. This is the property that makes a reset unnecessary.

**3. Three steps for a consensus change, each a separate release or readiness point:**
- **Understand** (release N): the build can validate `rules_version = n+1`, advertises it, and still authors with `n`. Shipping it changes nothing about validity. It carries a notice, shown in `/info` and the release notes: *update soon; no earlier than 30 days after this release, nodes still on older rules may stop being accepted by their peers or be dropped from the network.* The notice is a floor, not a date.
- **Emit** (release N+1): an author begins authoring with `n+1` once its own known list has a majority advertising support for `n+1`. This reuses the existing known-list machinery with no global state and no coordinator, and it means a change cannot go live for a shard whose witnesses cannot cosign it.
- **Require** (sunset, optional): verifiers stop accepting *new* events authored under `n`. A verifier starts requiring `n+1` once at least `max(strict majority, ceil(4/5 of the list size))` of its own known list is emitting it (4 of 5 at the default list size), and only in a release published at least 30 days after the Emit release. This is the only breaking step. Additive changes never need it, so most changes stop after Emit.

**4. No calendar dates are promised or compiled in.** The 30 days is a minimum gap between release N and the release that enforces anything (N+1), checked in the release process. If development takes 50 days, N+1 ships on day 50 and nothing breaks, because nothing was scheduled for day 30. Until N+1 ships, nothing is enforced. After it ships, enforcement is driven by readiness (known-list majorities), not by the clock. Operators who stay on older rules after that point fall behind visibly and are not accepted for new events by upgraded peers.

**5. Only validity changes use this process.** A release that does not change what is valid (new routes, new optional fields, performance, node behavior, stricter local limits) is an ordinary X.Y.Z release. It gets a "new version available" notice through the existing version-awareness signal (#368) and breaks nothing for a hoster who stays on the previous release. A change that makes the network reject something it used to accept is a validity change, even if it only tightens, and goes through Understand and Emit; Require applies only when the old way of authoring must stop. There is one process, with plain releases outside it.

**6. A node that meets rules it does not support fails closed.** It does not validate, store as verified, serve as verified, or cosign what it cannot validate. It reports `upgrade required` with the rules version, and it keeps serving everything authored under rules it does support. After upgrading it catches up from peers with no repair step.

**7. Releases carry no activation key or schedule.** Adopting a rules change is installing the release. Anyone can build different rules; that is a deliberate fork by social choice, and the protocol does not and cannot prevent it. A faster path for an urgent fix is the emergency path (#1154), with its own authorization rules.

## Why

- Per-event rules versions keep history valid forever, which is what lets the network change without a "2.0".
- Gating Emit on the author's own witnesses removes the failure where an author upgrades first and its heads stop getting cosigned.
- Driving enforcement from readiness instead of the clock means a slipped release never forces a deadline, and no key, file or service has to stay honest and online.
- Fail-closed makes a missed upgrade visible and recoverable instead of silently diverging.

## Alternatives considered

- **Activation at a ledger height.** Rejected: there is no global height, only per-shard tree sizes that authors control.
- **Activation entries in the trust-anchor file.** Rejected as the mechanism: its governance is repository review and a single publisher, which conflicts with #942. The file may still list a network's minimum rules version as an informational hint.
- **Flag day (everyone upgrades at once).** Rejected for a network with outside operators.
- **Per-node opt-in enforcement.** Rejected: guarantees verifiers disagree.
- **Fixed calendar dates in the release.** Rejected: a published date has to be met even when development slips, and a date says nothing about whether witnesses are ready.
- **Release-signing key signs activation notices.** Possible later through the signed release channel (#619, #1159), but it adds an authority and is not needed for the first version.

## Consequences

- Every signed structure needs a `rules_version` field. This must be settled in the format decision (#1153) and the format audit (#1155) before launch, because it cannot be added to frozen formats later.
- Announce, `/info`, the OpenAPI spec and all three SDKs gain `rules_supported` and `rules_emitting`. This is a contract change, so protocol, OpenAPI and conformance vectors update together (#1156).
- Witness cosigning must refuse heads it cannot validate and surface why. This needs a vector set in all three SDKs.
- A shard whose known list never reaches a supporting majority cannot Emit. That is intended; the operators concerned see the reason in `/info` and the topology visualizer (#1161).
- Cross-version CI (#1157) and the activation drill (#1158) are the proof, including a lagging node and a shard whose witnesses are split.

## Details settled

- **Emit readiness:** strict majority of the author's known list. Emit can be reversed by authoring under the previous rules, so no extra margin is needed.
- **Require readiness:** the higher bar above, plus its own 30-day minimum gap, because it is the step that cannot easily be undone.
- **The 30-day minimum gap** between releases is enforced by a CI check on the changelog in addition to the release checklist.
- **Trust-anchor entry:** carries no rules version. Rules versions come only from nodes. A hint field can be added later without a reset.

## Implementation state

This section is not part of the recorded decision. **Status:** Planned. The `rules_version` activation model is not implemented; see [version rollout](../nodes/version-rollout.md#rules-version-and-activation).

## Related

Part of the network upgrade epic (#1150). Informs #1153, #1154, #1155, #1156, #1158. Builds on #368 and #308. Aligned with #942.
