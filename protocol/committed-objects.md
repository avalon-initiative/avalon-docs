# Committed Objects

**Status:** Planned — the shared object mechanism is tracked in avalon-protocol#1313; current profile fields still appear inline in ledger events.

A committed object is signed content held off the ledger and verified against a hash recorded on it. Decisions [#1125](https://github.com/avalon-initiative/avalon-protocol/issues/1125) and [ADR 1299](../architecture/decisions/1299-decision-permanence-versus-erasure-what-the-public-ledger-may-hold-and-what-a-person-can-have-removed.md) separate authority state, recorded in full, from content, recorded as a commitment. This page describes that decided direction; the current profile representation is documented in [identity](./identity.md#what-is-promised-durable).

## Authority and content

Planned: keys, membership, roles, links, and revocations remain ledger authority state. Display names, avatars, bios, and guild names and descriptions move into committed objects. Identity profiles and guild metadata share the mechanism, with different schemas and signers: an identity owner signs a profile, and an authorized guild role signs guild metadata.

The object uses canonical encoding and carries a layout version, a kind version, and a random nonce inside the signed object. The ledger event carries the object's hash, signer, and chain position on the identity or guild chain. These are the planned object and event responsibilities in [#1313](https://github.com/avalon-initiative/avalon-protocol/issues/1313).

## Current object and stale copies

Planned: the latest commitment on the owning chain identifies the current object; chain order supersedes older commitments. A node whose held object does not match that commitment treats its copy as stale and refetches from other nodes. Mirror notifications can trigger that check.

Any node can serve an object by its commitment hash. A client verifies the object against the commitment on the chain, rather than trusting the serving node's copy merely because it was returned. This is the serve-and-fetch rule in [#1313](https://github.com/avalon-initiative/avalon-protocol/issues/1313).

## Availability

Planned: SDKs push the object to several nodes when publishing it. A node serving a chain head can serve the matching object or point to where it is held. If no copy exists, clients fall back to the id. A commitment provides verification, not the missing content; the publication and fallback behavior is tracked in [#1313](https://github.com/avalon-initiative/avalon-protocol/issues/1313).

## Why the nonce matters

Planned: the random nonce prevents someone from confirming a guessed short value against the commitment hash alone. A hash of a predictable display name without that nonce would permit guessing. This is the purpose of the nonce in [#1313](https://github.com/avalon-initiative/avalon-protocol/issues/1313), not a promise that a node holding the object will forget it; see [permanence and redaction](./permanence-and-redaction.md).

## Implementation

Status: Planned. The shared format, serving and fetching, publication, and conformance vectors are tracked in [avalon-protocol#1313](https://github.com/avalon-initiative/avalon-protocol/issues/1313). While that mechanism is not yet implemented, the [identity](./identity.md) and [privacy](./privacy.md#what-the-ledger-makes-public) pages describe the inline profile and guild payloads readers can encounter today.

## Related

- [Identity](./identity.md), [guilds](./guilds.md), [names and handles](./names.md)
- [Permanence and redaction](./permanence-and-redaction.md), [privacy](./privacy.md)
- [Protocol events](./protocol-events.md), [per-identity event chains](./identity/event-chains.md)
