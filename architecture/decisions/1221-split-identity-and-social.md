# ADR-1221: Identity and social become separate roles, shipped as three binaries

**Status:** Accepted — decided 2026-10-04

Original record: [avalon-protocol#1221](https://github.com/avalon-initiative/avalon-protocol/issues/1221), recorded on 2026-10-04. Item 1 (which `friend.*` and `guild.*` ledger kinds leave) was amended by [#1223](https://github.com/avalon-initiative/avalon-protocol/issues/1223), recorded the same day. The text below preserves the recorded decision with that amendment; `#N` references are avalon-protocol issue numbers. The decision is not built yet; see the implementation state at the end.

## Context

Identity and trust (ids, keys, recovery, ledger, mirroring, networking and attestations) and social (friends, blocks, presence, guilds and conversations) ship in one server crate, roughly 81k lines and 120+ modules. The process roles in #291 are an operator-internal split; every hoster still runs identity, ledger and social. The code boundary is thin, but one Postgres database and one sequence of 83 migrations tie social tables to `identities(id)` through foreign keys. Self-certifying ids and projection-time verification are prerequisites for a social host to verify identities without trusting their registering node.

The ledger currently carries four friend and fourteen guild kinds. As #1223 established, mirroring and replay supply friendships and guild rosters used for authorization, while guild metadata is node-local and chat is relayed. Removing links would remove their replication mechanism. Friend and roster events are node-attributed rather than actor-signed (#1216).

## Decision

Identity/ledger and social become separate roles, shipped as three binaries built from one codebase: **default** (identity + ledger + social, the one-command install), **identity** (identity, ledger, mirroring, witnessing and networking), and **social** (community features that use identities and the ledger).

1. **What is on the ledger, as amended by #1223 (O1).** `friend.requested`, `friend.accepted`, `friend.removed`, `friend.relationship_reversed`, `guild.created`, `guild.member_added`, `guild.member_removed`, `guild.membership_reversed` and `guild.role_changed` stay as full events, made actor-signed and authorized at projection. `guild.owner_transferred` settles in the roster slice, either with a projection or through `guild.role_changed`. The eight indexer-ignored metadata kinds (`guild.updated`, `guild.role_defined`, `guild.role_deleted`, `guild.game_associated`, `guild.favorite_games_updated`, `guild.channel_created`, `guild.channel_renamed`, `guild.channel_archived`) leave the ledger vocabulary, subject to the guild-home decision. Replication, rebuild and recovery rollback continue through the ledger. Chat, conversations, guild messages, guild events (RSVPs), blocks and presence are already off the ledger.
2. **Authentication.** A social host accepts the existing login grant signed by the identity's own signing key, in a new version with structured encoding and an audience bound to the host's node id, and mints its own local session. Passkeys stay for identity operations only.
3. **Verifying identities.** Reuse the existing verifier, projection-time verification (#1130) and projection from any shard (#1178). A social host needs the identity chains of its users, not the whole ledger. Add a protocol constant for the maximum age of cached key sets, with an immediate recheck before sensitive actions.
4. **Grey zone.** Achievements, attestations, issuers, revocations, permission grants, game bindings and schema registration stay on the identity side. Integrator data instances become integrator-signed and off the ledger, sliced separately.
5. **Discovery.** Nodes advertise roles as an extensible set of strings (unknown values are ignored) and serve a well-known document listing identity and social endpoints, defaulting to the same host. SDK configuration selects a network (tier or network id); an explicit server URL is an override. The correction in #1221's comments specifies seeds resolved from the trust-anchor list fetched at runtime, not a bundled copy; the list's location is the hardcoded input.
6. **Recovery.** A guardian may be any identity id whose signature approves; remove the friend requirement. The Hub may still suggest friends, while the M-of-N threshold and the owner's veto remain the protections.

Signing bytes move to a structured, fixed byte layout with versions and distinct domain tags for social events and login grants (#1214), before the format freeze (#1156). OpenAPI/JSON versus protobuf on the wire is parked as a separate decision, tracked on its own. Follow-on decisions recorded separately cover how an actor-signed link event gets its chain position (#1251) and where guild metadata lives (#1252).

## Why

Identity and the ledger provide a root of trust with strict correctness needs; social has product churn, moderation and heavier load. The split lets them change, scale and be hosted independently, lets an integrator use identity without carrying guilds, and makes social the first reference integrator of identity through public interfaces. The all-in-one preserves one-command onboarding. #1223 accepts a public, permanent friend graph and guild membership on mainnet and retains the ledger's replication, rebuild and recovery rollback machinery.

## Alternatives considered

- Status quo: one binary with roles selected by environment variable. Cheapest, but hosting everything remains mandatory in practice and the boundary stays soft.
- Two binaries with no all-in-one: simpler, but breaks one-command onboarding and doubles what a casual hoster runs. The three-binary outcome was adopted instead.
- Separate repositories and protocols now: clearer ownership, but premature until the boundary has been proven.
- Three binaries as feature flags on one cargo target: an implementation detail left for slicing.
- #1223 O1, full link events on the ledger: adopted. Keeps replication, rebuild and rollback, at the cost of public, permanent friendships and membership.
- O2, commitments on the identity chain with content off the ledger: still one entry per action, with content availability dependent on its holders and a new fetch path.
- O3, everything off the ledger: the original #1221 item 1, superseded by #1223. Needs pairwise friend delivery, signed guild rosters, ordering, rebuild and recovery rollback replacements.
- O4, split by who needs to know: bilateral friendships delivered between the two hosts, with guild rosters on the ledger for other hosts and games to authorize against; metadata leaves.

## Consequences

- Extract social into its own protocol server crate (router, handlers, projections and realtime) behind public interfaces. Identity/ledger keeps `identity_chain`, `outbox`, settlement, mirroring and nodes. Add three binary targets and generalize the interest registry used for network scope.
- Separate schemas or databases per role without cross-role foreign keys; a social host keeps its own verified identity view. Split the migration sequence. Development databases are wiped and rebuilt, without compatibility shims.
- Tag or split OpenAPI by role. SDKs take two base URLs defaulting to the same host; all three SDKs change under one version and release, with conformance vectors updated if signing bytes change. Hub, bot and other consumers adopt the two-endpoint configuration; architecture, hosting and SDK documentation follow. Separately hosted identity and social endpoints qualify the single-URL invariant recorded in [ADR 0672](0672-realtime-websocket-extraction-proxies-through-gateway-not-direct-connect.md). Realtime proxying through the Gateway the client already talks to remains governed by that decision.
- Release artifacts, installers, container images, the setup wizard and bundled-Postgres packaging need role variants. Social-only hosts need access to at least one identity node; the network needs enough nodes of each kind. This is large, cross-repository work ordered protocol first, then SDKs, then consumers.
- Under #1223, friend and roster slices become "actor-signed and authorized at projection" rather than "move"; cleanup folds into the eight-kind metadata slice. A social-only host needs the identity chain head and a path to a ledger authority to author and submit events. Structured encoding, v3 signing and the integrator-data slice are unchanged.

## Implementation state

This section is not part of the recorded decision.

Tracked in epic [avalon-protocol#1222](https://github.com/avalon-initiative/avalon-protocol/issues/1222). Its `release-blocker` slices cover what cannot change after launch without a fork, reset or flag day (#1151): removing the eight metadata kinds (subject to the guild-home decision) and the integrator-data kinds, structured signing encoding and its formats, actor-signed social forms, and SDK vectors. The role split, binaries, database layout, SDK network configuration, Hub and docs ship after launch through the upgrade mechanism (#1150). The decision was not built when this page was written; [nodes](../nodes/README.md) describes the existing capability roles and behavior.

## Related

#1223, #1222, #1214, #1216, #1153, #1150, #1151, #1251, #1252, #291, [ADR 0672](0672-realtime-websocket-extraction-proxies-through-gateway-not-direct-connect.md), [ADR 1129](1129-identity-ids-are-self-certifying.md), [ADR 1177](1177-an-account-stays-usable-anywhere-when-its-registering-node-goes-away.md), [nodes](../nodes/README.md).
