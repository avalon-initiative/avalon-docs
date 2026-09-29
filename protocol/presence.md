# Presence

**Status:** Implemented

Presence is ephemeral state ("this identity is online, in this integrator, right now") that never enters durable protocol history. It is the realtime vertical of the network alongside settlement and query, and the one whose loss costs nothing: if presence storage disappears, identities look offline until their next heartbeat. The decision is recorded in [ADR 0078](../architecture/decisions/0078-realtime-presence-is-ephemeral-and-never-enters-durable-history.md).

## Two kinds of fact

```text
"User X is currently online in Ashen Realms."      ephemeral
"User X defeated the Dragon Lord."                 durable history
```

The first changes every few seconds, matters only now, and is worthless in an append-only log. The second is the kind of fact Avalon exists to preserve. The architecture keeps them apart at every layer; see the [overview](../architecture/overview.md).

## What presence covers

| Field | Example |
| --- | --- |
| status | `online`, `away`, `do_not_disturb`, `offline` |
| active in | the integrator the identity is currently active in |
| heartbeat | last seen at |

Anything a user would want a friend or guildmate to know right now, and nothing anyone needs to prove later.

## Rules

- Presence is not a `ProtocolEvent`. It is never written to the settlement store and is never in [disaster-recovery](../architecture/disaster-recovery.md) rebuild scope.
- It may live in process memory, a cache, or a dedicated realtime service; it is not required to be in Postgres.
- Presence is permissioned. An integrator publishing presence on an identity's behalf needs `presence.publish` under an active [binding](./bindings.md), can publish only for identities bound to it, and may set `active_in` only to its own integrator id. Who can see presence is a [visibility](./privacy.md) setting, defaulting to friends only.
- An identity can independently opt `active_in` out of ever being shown, regardless of any integrator grant. That standing preference is a durable row, not part of the ephemeral store.
- Realtime population numbers ("players online in Integrator A") are labeled realtime wherever shown and never stored as durable metrics in the [registry](./registry.md).
- What is durable about presence-adjacent activity (a binding established, an achievement earned) is its own protocol event, never inferred from heartbeats.
- `online` is tracked automatically: a live entry within the heartbeat TTL (120 seconds by default) reads `online`, a stale one reads `offline`. `away`, `do_not_disturb`, and `offline` are sticky manual overrides: once explicitly published, that status is reported on every read regardless of TTL or heartbeats, survives a reconnect (not a server restart, since the store is in memory), and clears only by explicitly publishing `online`.

## What presence powers

Friends lists with online and where, guild rosters with "members currently playing", the Hub's activity view and companion apps, cross-integrator "join me" flows and matchmaking an integrator chooses to build, and community tools.

## Delivery

`GET /presence?ids=...` reads current presence. `GET /ws/presence` is a live push transport, additive to the read. A client subscribes with a list of identity ids (additively; sending again grows the subscription), receives a catch-up snapshot, and then every subsequent change. Browsers cannot set headers on a WebSocket handshake, so the token is passed as a query parameter. Fan-out is a bounded, lossy broadcast: a slow consumer drops interim updates rather than backing up the publisher, an acceptable tradeoff for ephemeral data and unlike the outbox's durable delivery for protocol events. Visibility is enforced on the WebSocket too (friends by default, with blocks always winning).

**Cross-node relay.** Each process has its own presence store, so without relay two friends connected to different realtime nodes could not see each other online. After each update a node posts it once to every same-network peer that advertises a realtime, gateway, or combined role. The receiving node applies it with the origin node's timestamp and never relays again, so relay is single-hop by construction. A single-node deployment is unaffected, and a client that reconnects to a different node resumes live delivery with the same session token, with any gap bounded to the disconnect window. See [node roles and realtime extraction](../architecture/nodes/roles-and-extraction.md) and [ADR 0672](../architecture/decisions/0672-realtime-websocket-extraction-proxies-through-gateway-not-direct-connect.md).

## Deployment

Presence runs inside the node process by default. Because it shares no storage with settlement or indexing and emits no events, it can move to its own process or node role without touching either. Scaling realtime connections is a separate axis from scaling history or queries; see [scalability](../architecture/scalability.md).

## Open questions

The full per-resource visibility-scope model (friends, guild, private, configurable by identity and guild, per resource) remains an open decision beyond what is built for presence and guild rosters; see [privacy](./privacy.md).

## Implementation

Status: implemented.

- Types: `PresenceStatus` and `Presence { identity_id, status, active_in, updated_at }` in [`social.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/social.rs).
- Server: [`presence.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/presence.rs), an in-process store that never touches the outbox or the chain, and [`realtime_relay.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/realtime_relay.rs). `PUT /me/presence` sets the caller's own status and the `hide_active_in` preference; `PUT /presence/{identity_id}` is the integrator publish path.
- Each subject's `profiles.presence_visibility` gates reads (default `friends`, changeable by the identity); a block is checked first.

## Related

- [Privacy](./privacy.md), [social graph](./social-graph.md), [guilds](./guilds.md), [bindings](./bindings.md)
- [Overview](../architecture/overview.md), [nodes](../architecture/nodes/README.md), [scalability](../architecture/scalability.md)
- [ADR 0078](../architecture/decisions/0078-realtime-presence-is-ephemeral-and-never-enters-durable-history.md), [ADR 0437](../architecture/decisions/0437-three-tier-data-freshness-policy-realtime-push-poll-or.md)
