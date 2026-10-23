# Permanence and Redaction

**Status:** Planned — the permanence boundary is decided in avalon-protocol#1299; signed redaction is tracked in avalon-protocol#1316.

Avalon's append-only ledger keeps authority history and entry skeletons permanent, while content is intended to be removable. Decision [ADR 1299](../architecture/decisions/1299-decision-permanence-versus-erasure-what-the-public-ledger-may-hold-and-what-a-person-can-have-removed.md) defines that boundary and its limits: removal is best effort, with no legal compliance claim. This page describes the decided model and distinguishes it from [current pruning](./privacy.md#erasure-versus-permanence).

## What remains and what can be removed

Planned under [ADR 1299](../architecture/decisions/1299-decision-permanence-versus-erasure-what-the-public-ledger-may-hold-and-what-a-person-can-have-removed.md):

| Data | Treatment |
| --- | --- |
| Authority state: keys, membership, roles, links, revocations | Recorded in full on the ledger |
| Social graph | Public relationships expressed as ids, rather than display-name text |
| Identity profiles and guild metadata | Signed [committed objects](./committed-objects.md) off the ledger, with hash, signer, and chain position on it |
| Intrinsic free text, such as guild posts and integrator-defined data | Inline content can be dropped through signed redaction; the payload hash preserves the commitment |
| Entry skeleton | Hash, id, timestamp, and signer remain permanent after content removal |

The field-level inventory is tracked in [#1318](https://github.com/avalon-initiative/avalon-protocol/issues/1318). It classifies authority state, pseudonymous identifiers, content, and personal data, with dispositions to move content behind a commitment, keep it inline with redaction, or remove it. This boundary is not a promise that the current payload formats have already changed.

## Signed redaction

Planned in [#1316](https://github.com/avalon-initiative/avalon-protocol/issues/1316): a signed redaction references an entry or object by its commitment. The author can redact their content; a guild role holding the moderation permission can also redact guild content. The authorization is signed and recorded on the owning chain.

Conforming nodes stop serving the payload, drop its bytes, mark the entry tombstoned, and propagate the redaction through mirroring. Redaction is monotonic and tombstone-first: a redaction received before its content still wins, and the redacted commitment cannot be republished. Retention pruning and redaction are planned to share the payload-drop path, while the entry skeleton remains verifiable.

## Honest limits

Redaction is best effort. A node that ignores the rule can keep a copy, and removing bytes from conforming nodes does not remove that copy. The nonce in a committed object prevents checking a guessed short value against its hash alone; it does not retract content someone already holds. Crypto-erasure is a later layer if required, and the decision makes no legal compliance claim ([ADR 1299](../architecture/decisions/1299-decision-permanence-versus-erasure-what-the-public-ledger-may-hold-and-what-a-person-can-have-removed.md), [#1316](https://github.com/avalon-initiative/avalon-protocol/issues/1316)).

While signed redaction is not yet implemented, [payload pruning](./privacy.md#erasure-versus-permanence) is a local retention operation, not a network-wide erasure request. The public friend graph and guild memberships remain visible as authority history. Chat messages have a separate deletion path outside the ledger; see [guild chat](./guilds/chat-and-events.md#messages-are-not-durable).

## Before creating an identity

Setup should explain the boundary before a person writes data: authority history, public relationship ids, and entry skeletons remain; the planned removal path concerns content and cannot guarantee deletion from a nonconforming node. While committed objects and signed redaction are not yet implemented, profile text also appears in public ledger payloads; do not treat planned redaction as protection for a write made today ([#1125](https://github.com/avalon-initiative/avalon-protocol/issues/1125), [ADR 1299](../architecture/decisions/1299-decision-permanence-versus-erasure-what-the-public-ledger-may-hold-and-what-a-person-can-have-removed.md), [current privacy behavior](./privacy.md#what-the-ledger-makes-public)).

Losing access to an identity and removing its published data are separate questions. Read [the recovery ladder](./identity/recovery-ladder.md) for total key loss, and [identity portability](./identity.md#portability-depends-on-where-the-identitys-events-live) for the current dependence on node-held state. Neither recovery nor moving between nodes removes already mirrored history.

## Implementation

Status: Planned for [committed objects](https://github.com/avalon-initiative/avalon-protocol/issues/1313) and [signed redaction](https://github.com/avalon-initiative/avalon-protocol/issues/1316). Current ledger exposure and retention behavior are documented in [privacy](./privacy.md); this page describes the boundary set by the decision, not a built erasure service.

## Related

- [Identity](./identity.md), [names and handles](./names.md), [committed objects](./committed-objects.md)
- [Privacy](./privacy.md), [social graph](./social-graph.md), [guilds](./guilds.md)
- [Nodes and identity state](../architecture/nodes/README.md#identity-and-social-actions-and-shards), [the recovery ladder](./identity/recovery-ladder.md)
