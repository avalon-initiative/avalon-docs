# Glossary

**Status:** Reference

Avalon reuses ordinary words (identity, event, node, chain) for specific, narrow meanings. This page gives one definition per term, the distinction that matters, and a link to the page that develops it. The linked page is authoritative if a definition here ever drifts from it.

## Core nouns

| Term | Means | Does not mean | See also |
| --- | --- | --- | --- |
| Identity | A self-owned, integrator-independent keypair: a WebAuthn passkey for login plus a separate Ed25519 key that signs the events it authors. It survives any single integrator, server, or database disappearing. | A username and password account, or anything an integrator can define, rewrite, or own. | [Identity](../protocol/identity.md) |
| Integrator | Any independently operated game, app, or service that connects to Avalon. Sovereign over its own world and data; Avalon never owns it. Older text and some code and tickets say "game" for the same concept. | Avalon itself, or a node operator. | [Overview](../architecture/overview.md) |
| Character | Integrator-owned gameplay data (race, class, level, appearance, progression, inventory) held in the integrator's own database. | An Avalon identity, or anything Avalon stores. | [Bindings](../protocol/bindings.md) |
| Binding (integrator profile) | The durable fact that an identity participates in an integrator, and nothing more. It scopes an integrator's authority to its own binding. | The character data itself. | [Bindings](../protocol/bindings.md) |
| Issuer | The keyed identity under which an integrator (or another authorized party) signs attestations. It has registered signing keys, a key history, and a status. A node operator is never an issuer by virtue of hosting. | The node that transports or stores a claim. | [Issuers](../protocol/issuers.md) |
| Achievement / attestation | A signed claim of the form "issuer X asserts identity Y accomplished Z", with a timestamp and a schema. The durable fact is the claim, not a shared row. | Proof that the claim is meaningful; that is recognition. | [Achievements and attestations](../protocol/achievements-and-attestations.md) |
| Guild | A network-level social primitive that exists independently of any integrator and can have members across many integrators. An integrator is a client of a guild, never its owner. | A guild system owned and hosted by one game. | [Guilds](../protocol/guilds.md) |
| Social graph | An identity's friends, presence, and communication. Persists across integrators and reaches an integrator only through explicit capability grants. | A per-integrator friends list. | [Social graph](../protocol/social-graph.md) |
| Integrator event | An attestation for a durable, cross-integrator result (a tournament, a championship) that an integrator runs and signs. Only the result crosses into Avalon. | Live match state, brackets, matchmaking. | [Cross-integrator events](../protocol/cross-integrator-events.md) |
| Integrator Space | The mechanism by which an integrator publishes a versioned, structural schema of its own data and controls how much is exposed, without Avalon standardizing what the data means. | A global data model integrators must conform to. | [Integrator space](../protocol/integrator-space.md) |
| Registry | The network's derived facts and aggregated statistics about integrators and issuers. | A ranking, score, or trust judgment. | [Registry](../protocol/registry.md) |
| Capability (grant) | An explicit, scoped permission an identity grants an integrator, for example "read my friends list". The mechanism behind least privilege; SDK methods check their required grant. | Blanket access to an identity's data. | [Security model](../protocol/security-model.md) |

## Trust and provenance

| Term | Means | Does not mean | See also |
| --- | --- | --- | --- |
| Provenance | Who signed a claim, when, under which key, and whether it still stands, recorded for every durable claim. | Meaning or trustworthiness of the claim. | [Provenance](../protocol/provenance.md) |
| Authentic | The claim's signature verifies against the issuer's registered key. A cryptographic fact anyone can check. | Valid or recognized. | [Trust model](../protocol/trust-model.md) |
| Valid | The claim has not been revoked, and its issuer was not suspended or revoked when it was issued. | Recognized. | [Trust model](../protocol/trust-model.md) |
| Recognized | Whether a specific receiving integrator chooses to honor a claim. Decided per integrator, never by the network. | A network-wide trust list; Avalon has none. | [Trust model](../protocol/trust-model.md) |
| Revocation | An appended fact ("issuer A later revoked claim X") layered on top of the original issuance. Both stay visible. | Deletion. | [Revocation](../protocol/revocation.md) |

## Settlement, history, and infrastructure

| Term | Means | Does not mean | See also |
| --- | --- | --- | --- |
| Protocol event | A durable fact that is part of Avalon's history (identity created, friend accepted, achievement issued). Append-only; a correction is a new event. Ordinary gameplay is never a protocol event. | Every action an integrator takes. | [Protocol events](../protocol/protocol-events.md) |
| Settlement / ledger / log | The durable-history vertical: a hash-chained, append-only, publicly verifiable transparency log on Postgres that commits protocol events in batches. There is no validator set and no consensus, because nothing written to it is contested. | A query database, a blockchain, or a cryptocurrency. | [Settlement](../architecture/settlement.md), [ADR 0186](../architecture/decisions/0186-no-blockchain-validator-consensus-transparency-log-only.md) |
| Signed Tree Head (STH) | A signed root over the log's Merkle tree at a given size, used by clients and mirrors to verify the log. Served at `GET /ledger/sth/latest`. | A block. | [Settlement](../architecture/settlement.md) |
| Witness cosignature | A second signature over an STH by an independent node that checked the head only grew from the last one it saw. | A vote on ordering. | [Witness cosigning](../protocol/witness-cosigning.md) |
| Shard | One independently authoritative log: one legitimate signer, its own hash chain and tree head. The reserved `core` shard holds identity, social, and guild history; integrators can author their own. | A partition of one log by load. | [Sharding and cross-shard commitment](../architecture/settlement/sharding.md) |
| Cross-shard root | A root over every known shard's tree head, computable by any node from public data. Not signed by any single party. | A global ordering of events. | [Sharding and cross-shard commitment](../architecture/settlement/sharding.md) |
| `network_id` | A string label for a deployment. It has no cryptographic authority alone; trust comes from pinning it to the deployment's real verify key. | A security boundary by itself. | [Network trust anchors](../protocol/network-trust-anchors.md) |
| Indexer | The fast-read query layer: a Postgres projection rebuildable from durable history. | The source of truth. | [Query and indexing](../architecture/query-and-indexing.md) |
| Outbox | The write pattern that commits a domain write and its ledger-bound event in one Postgres transaction, so a crash cannot leave one without the other. | A message broker. | [Settlement](../architecture/settlement.md#batching) |
| Presence | Realtime online state. Ephemeral; never enters durable history. | A record of when someone was online. | [Presence](../protocol/presence.md) |
| Node | Infrastructure that transports, indexes, settles, or serves protocol data. An infrastructure provider, never an authority. | A validator with governance power, or the issuer of what it carries. | [Nodes](../architecture/nodes/README.md) |
| Mirror | A node that syncs and re-serves the same `network_id`'s public log. Participation in the network, not a fork. | A private instance under a different `network_id`. | [Nodes](../architecture/nodes/README.md), [Self-hosting](../architecture/self-hosting.md) |
| Self-hosting | Running the Avalon code. Mirroring and running a shard keep the shared `network_id`; running under your own `network_id` is a private instance and a fork. | Mirroring. | [Self-hosting](../architecture/self-hosting.md) |
| Connectivity | How peers can reach a node (direct, NAT-traversed, relayed, outbound-only). A transport property that never affects authority. | A measure of trust or standing. | [Connectivity](../architecture/nodes/connectivity.md) |
| Stream transport | Carrying a node-to-node HTTP request over a libp2p stream to a `p2p://<peer id>` base URL, so relays and hole punching apply and a peer with no usable URL is reachable. | A way for clients or SDKs to reach a node, or a separate API. | [Connectivity](../architecture/nodes/connectivity.md#node-to-node-requests-over-libp2p-streams) |
| Relay selection | How a node with no reachable address picks which relays to hold reservations with: skip relays in backoff, operator-listed before discovered, a relay outside every network already held, then round trip and outcome history. | Probing relays, or a guarantee of the best relay. | [Relay selection](../architecture/nodes/connectivity.md#relay-selection) |
| Transport failover | Retrying a node-to-node request over the other transport (HTTP or libp2p stream) after a failure to connect, with a per-peer record that demotes a failing transport. | Retrying after an application answer, or replaying a write after a timeout. | [Transport failover](../architecture/nodes/connectivity.md#transport-failover) |

## Identity mechanics

| Term | Means | Does not mean | See also |
| --- | --- | --- | --- |
| Passkey | A WebAuthn credential used to log in. An identity can have several. | The signing key. | [Identity](../protocol/identity.md) |
| Identity id | The 64-character lowercase hex SHA-256 of the domain tag `avalon-identity-id-v1` and the identity's first Ed25519 public key. It never changes when keys are added, rotated, or recovered. | A UUID, a display name, or the `node:` id of a shard. | [Identity](../protocol/identity.md#the-identity-id) |
| Ed25519 signing key | The separate key, not the login passkey, that signs events an identity authors. | The login credential. | [Identity](../protocol/identity.md) |
| Social recovery | Recovering an identity when passkeys are lost, through approval by M of N designated guardians. | A centrally held backdoor. | [Identity](../protocol/identity.md) |
| Cross-device pairing | Adding a device or passkey to an existing identity. | Creating a second identity. | [Identity](../protocol/identity.md) |
| Cross-node login | Logging an identity into a node it never registered on, through a signed, human-approved grant bound to the destination node. | A shared login domain. | [Cross-node login](../architecture/nodes/cross-node-login.md) |

## Related

- [Architecture overview](../architecture/overview.md)
- [Status vocabulary](status-vocabulary.md)
- [Concepts tour](../getting-started/concepts.md)
