# Abuse Model

**Status:** Planned — accepted direction; the requests inbox, guild-chain admission policy, trust-scoped discovery, and lazy projection are not yet built. Existing controls are linked below.

Avalon protects attention and node resources through consent and bounded exposure. Identity creation is free and unlimited by design; preventing it is a non-goal because charging for it either punishes real users or requires a special authority. This model follows the accepted [abuse and moderation decision](https://github.com/avalon-initiative/avalon-protocol/issues/1298); acceptance records the direction, not its deployment.

## Contact from strangers

Planned: [requests inbox and per-sender limits (#1320)](https://github.com/avalon-initiative/avalon-protocol/issues/1320). Friend requests and direct messages are delivered but sorted by shared context: a shared guild, mutual friend, same game binding, or signed invite. Without that context they land in a requests inbox with no push notification. Direct messages from non-friends allow a few messages until accepted, and a per-sender rate limit set above any human rate bounds new-stranger contacts. The recipient can tighten the setting to shared context only or nobody, or loosen it.

Today, creating a [direct or small-group conversation](../architecture/communication.md#direct-messages-and-small-group-conversations) requires every named participant to be a friend or mutual guild member of the caller. The existing [social graph](./social-graph.md#blocking-and-harassment) documents blocks that refuse friend requests and hide presence across integrators. Those controls do not imply that the requests inbox is implemented.

## Guild admission and bans

Planned: [guild admission policy (#1321)](https://github.com/avalon-initiative/avalon-protocol/issues/1321). A guild's admission rule is its main lever against abuse by many identities: invite-only, approval, vouching, or an attestation from an issuer the guild requires. The rule is authority state on the guild chain. In the accepted model, a guild ban is a signed guild-chain event; ban evasion is limited only by admission rules.

Current [membership rules](./guilds/permissions-and-roles.md#membership) already include invite-only and open joins, invites, and recruiting-guild join requests reviewed by members with permission. These are not the planned guild-chain admission policy.

## Discovery scoped by trust

Planned: [trust-scoped discovery (#1322)](https://github.com/avalon-initiative/avalon-protocol/issues/1322). Discovery ranks and filters by graph distance and attestations from issuers the consumer trusts. There is no global reputation score; each consumer chooses its trust context.

The current [people discovery](./social-graph.md#handles-and-discovery) already offers relationship-based suggestions and opt-in name search. The broader ranking and filtering model remains planned.

## Bounded node exposure

Planned: [lazy projection (#1323)](https://github.com/avalon-initiative/avalon-protocol/issues/1323). The model combines per-source mirroring and projection caps with projection of only relevant identities rather than every identity ever created. Other identities stay in the log within mirroring caps and are projected on demand when needed. The accepted model also permits a hoster to add an admission policy for its own registrations.

Existing [node safety limits](../architecture/nodes/safety-limits.md) already bound requests, connections, peer tables, and relay resources. [Auto-mirroring discovered shards](../architecture/settlement/sharding.md#automatic-shard-discovery) is bounded per source and by other budgets; self-certifying shards' entries currently stay in mirror tables without being projected. Those limits are current controls; lazy identity projection is planned.

## What this does not solve

There is no network-wide ban and no global reputation score: someone would have to hold that power. A personal block applying across integrators is not a ban from the network.

Planned for a later layer, not for launch: optional signed shared blocklists and labels that guilds and nodes subscribe to, under the accepted decision.

An attacker with many identities can still annoy open guilds and spend their own node's resources. Ban evasion is limited only by admission rules; free identity creation does not establish that a new identity is a different person.

## Related

- [Social graph](./social-graph.md), [guilds](./guilds.md), [privacy](./privacy.md)
- [Security model](./security-model.md), [trust model](./trust-model.md)
- [Node safety limits](../architecture/nodes/safety-limits.md)
