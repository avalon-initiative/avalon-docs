# Version Rollout

**Status:** Partially implemented — version awareness is live; signed release manifests and auto-update are not built

No party can force an operator to upgrade. Self-hosting with no central gatekeeper is deliberate, so the network has to work with permanent version skew. This page describes the version axes, the standing compatibility rule, and the node-to-node version awareness that exists.

## Three version axes

Conflating them is the real failure mode.

- **Event-schema version:** payload shape per event kind, additive only.
- **Wire and API version:** HTTP endpoint shapes and mirror-sync data types.
- **Settlement and crypto version:** hash algorithm, signature scheme, and head and Merkle format. This is the one axis where mixed versions on the same `network_id` are not safe.

## Standing rule for the wire and API axis

Additive only, and forever compatible. Never remove, rename, or repurpose a field or endpoint outright; add alongside and deprecate slowly. One exception was taken once, before the protocol repository became public: a terminology generalization renamed some request and response fields and dropped a compatibility route family, knowingly, because at the time every consumer lived in one repository and was updated in the same change. That argument no longer exists, and the additive rule now applies without exception.

## Cross-cutting invariant

A version claim is never trusted for anything cryptographic or used to grant elevated trust or capability. It is a compatibility and availability signal. The worst case of a forged claim is a self-inflicted availability change (wrongly excluded from, or wrongly kept in, gossip), never elevated trust or bypassed verification. Every settlement operation stays independently verified regardless of what either side claims.

## What exists

- The mirror-sync wire format carries an additive version field, so an older peer's response without it still decodes. An incompatible version produces a structured log line and a distinct error, never a panic or an undifferentiated decode failure.
- The version a node reports is a compile-time constant, never a runtime setting, which closes the trivial "set a config value" spoofing path. This is not cryptographic non-forgeability: a recompiled binary can hardcode anything. Genuine non-forgeability needs a signed release manifest, which does not exist.
- A minimum-supported-peer-version floor is baked into the binary. A peer below it is excluded from the peer table and gossip. An environment setting can only raise the floor, never lower it. Exclusion is reversible: a peer that upgrades is re-admitted on its next announce.
- `GET /nodes/status` reports the node's protocol version, its roles, and, when known through gossip, a `stale` flag. The flag is a self-diagnostic hint only; nothing reads it to change behavior.

## Not built or decided against

- Planned, gated on release signing: opt-in auto-update for self-hosted nodes.
- Decided against for now: capability-based request forwarding (an outdated node relaying to a capable peer), because it adds a trust hop with no accountability story.
- Reserved and undesigned: a hard-fork escape hatch (a new `network_id` while the old one keeps running) for a genuinely incompatible cryptographic change.

## Implementation

Status: Partially implemented, as above. Version handling is in the [server crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/server) of avalon-protocol.

## Related

- [Nodes](README.md)
- [Discovery and peering](discovery-and-peering.md)
- [Protocol events](../../protocol/protocol-events.md) (event-schema versioning)
