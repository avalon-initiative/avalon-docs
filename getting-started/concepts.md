# Concepts

**Status:** Implemented — describes shipped concepts; the last section lists the ones that are not built.

A one-page tour of the ideas the rest of the documentation builds on. Each section gives the short version and links to the page that holds the detail. Terms are defined in the [glossary](../reference/glossary.md).

## Identity

An identity is a self-custodied keypair: a WebAuthn passkey for login plus a separate Ed25519 key that signs the events the identity authors. It can register several passkeys and devices, recover through M-of-N guardian approval if every device is lost, and pair a new device without starting over. It identifies a keypair, not a person. See [identity](../protocol/identity.md) and [identity aggregate view](../protocol/identity-aggregate-view.md).

## Characters are not identity

A character (race, class, level, inventory) is integrator-owned gameplay data. Avalon never sees it unless the integrator publishes a schema describing part of it. One identity can sit behind many unrelated characters across integrators. See [ADR 0067](../architecture/decisions/0067-identity-is-separate-from-game-characters.md) and [integrator space](../protocol/integrator-space.md).

## Integrators, bindings, and capabilities

An **integrator** is a game, app, or service that connects to Avalon. A person **binds** an identity to an integrator and grants specific **capabilities** (for example `friends.read`, `achievements.issue`). The integrator sees only what was granted, and the person can revoke it. The server enforces this on every request. See [bindings](../protocol/bindings.md) and [integrations: capabilities](../integrations/capabilities.md).

## Social graph, presence, guilds

Friends and blocks are network-level facts. Guilds are network-level entities with roles, channels, and history, so they survive any one game ([ADR 0074](../architecture/decisions/0074-guilds-are-network-level-primitives-not-game-owned.md)). Presence is real-time and ephemeral and never enters durable history ([ADR 0078](../architecture/decisions/0078-realtime-presence-is-ephemeral-and-never-enters-durable-history.md)). See [social graph](../protocol/social-graph.md), [guilds](../protocol/guilds.md), and [presence](../protocol/presence.md).

## Attestations and the three questions

An achievement is an attestation: a claim signed by an issuer about an event. Three separate questions apply to any attestation ([ADR 0076](../architecture/decisions/0076-attestation-trust-model-authenticity-validity-and-recognition-are-separate.md)):

| Question | Who answers | Meaning |
| --- | --- | --- |
| Authentic? | The network | The signature verifies against the issuer's key history. |
| Valid? | The network | It has not been revoked. |
| Recognized? | Each integrator | Under its own policy, does it accept this issuer and claim? |

Avalon records provenance; integrators decide meaning. See [achievements and attestations](../protocol/achievements-and-attestations.md), [trust model](../protocol/trust-model.md), [revocation](../protocol/revocation.md), and [issuers](../protocol/issuers.md).

## The transparency log

Durable protocol facts are written to an append-only, hash-chained log whose tree heads are signed and can be cosigned by independent witnesses. Anyone can mirror and verify it. It is a transparency log, not a blockchain: no validator consensus and no native currency ([ADR 0186](../architecture/decisions/0186-no-blockchain-validator-consensus-transparency-log-only.md)). Query databases are projections rebuilt from it ([ADR 0075](../architecture/decisions/0075-durable-protocol-history-is-canonical-query-databases-are-projections.md)). See [settlement](../architecture/settlement.md), [witness cosigning](../protocol/witness-cosigning.md), and [query and indexing](../architecture/query-and-indexing.md).

## Networks and trust anchors

A `network_id` is a plain string with no authority on its own. The root of trust is a published list pinning each known network to its settlement operator's public key, which clients use to verify tree heads. See [network trust anchors](../protocol/network-trust-anchors.md).

## Nodes

A node is a running `avalon-server`. Nodes have independent roles (settlement, indexer, realtime, gateway), can mirror shards from each other, and discover peers through gossip. Participation must not depend on public reachability ([ADR 0903](../architecture/decisions/0903-node-participation-must-not-depend-on-public-reachability-nat.md)). See [nodes](../architecture/nodes/README.md), [distributed topology](../architecture/distributed-topology.md), and [synchronization](../architecture/synchronization.md).

## What survives an integrator's death

The organizing question for the design is what should outlive a particular game or server. The answer is the person's identity and history, not the game. The table that spells this out is in the [architecture map](../architecture/README.md); recovery from infrastructure loss is in [disaster recovery](../architecture/disaster-recovery.md).

## Not built

An economic layer (currency, wallet, purchases) and portable assets are not implemented and have no near-term commitment. See [future layers](../architecture/future-layers.md).

## Related

- [What is Avalon?](what-is-avalon.md)
- [Architecture map](../architecture/README.md)
- [Protocol concept map](../protocol/README.md)
- [Glossary](../reference/glossary.md)
