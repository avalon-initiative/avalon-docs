# ADR-0672: Realtime WebSocket extraction proxies through Gateway, not direct-connect

**Status:** Accepted — decided 2026-09-20

Original record: [avalon-protocol#672](https://github.com/avalon-initiative/avalon-protocol/issues/672). The text below is preserved as recorded; `#N` references are avalon-protocol issue numbers and file paths are as they were when the decision was made.

## Context

#663 extracts Realtime (`crate::presence`/`crate::chat`'s WebSocket
service, #16/#438) into a genuinely separate deployable role, per #78's
own closed ADR ("Milestone 1 runs it inside `avalon-server`; it can be
split into its own process later ... and this decision is what keeps that
split possible"). Unlike #662's Indexer extraction, an open WebSocket
connection is stateful in a way a query-layer call isn't — it has to
terminate somewhere real, on some actual TCP connection, for its whole
lifetime. Two ways to get a client's realtime traffic to a node that isn't
running Realtime locally:

1. **Proxy-through-Gateway.** The client keeps connecting to the
   Gateway's own `/ws/presence`/`/ws/messages` endpoints, exactly as
   today. Internally, once authenticated, the Gateway dials the remote
   Realtime node's identical endpoint as a WebSocket client and pipes
   frames bidirectionally between the two connections for the session's
   lifetime.
2. **Direct-connect.** The client is told (via whatever #665's
   discovery/routing work eventually formalizes) to open its WebSocket
   connection directly against the Realtime node's own address, bypassing
   the Gateway entirely for that traffic.

## Decision

Proxy-through-Gateway. The client always talks to exactly one node's URL
for everything it does, including realtime traffic; the Gateway is
responsible for reaching a remote Realtime node internally when it isn't
running that role itself.

Implementation: `AVALON_NODE_ROLES` (`crate::nodes::node_roles`) becomes a
real, load-bearing gate for the `realtime` role, the same mechanism #662
(Indexer) and #664 (Settlement) use for their own roles. When a process's
resolved roles exclude `realtime`, `AVALON_REALTIME_URL` must name a
reachable remote Realtime node or the process refuses to start
(`crate::nodes::realtime_mode_from_env`). `presence::presence_ws`/
`chat::chat_ws` authenticate the caller locally as always, then — when a
remote URL is configured — hand the upgraded socket to
`crate::realtime_proxy::proxy_websocket`, which dials the remote node's
own identical endpoint (forwarding the same session token) and pumps
frames both directions until either side closes.

## Why

- **Keeps the "one node, one URL" invariant every other role extraction
  in epic #291 preserves.** #661's internal RPC and #662's Indexer
  extraction both let a Gateway reach another role without the caller
  (an SDK, a browser) needing to know or care that the role moved out of
  process. Direct-connect breaks that for the one surface (realtime)
  where a client is a browser/game client talking WebSocket, not this
  crate's own internal `Indexer`/`SettlementProvider` trait — a browser
  would need real routing/discovery logic (which node currently serves
  Realtime for this deployment, including failover) that doesn't exist
  yet. Proxy-through needs none of that: the Gateway's own URL is already
  what every client is configured to use.
- **Doesn't require #665 to exist first.** Direct-connect is naturally
  where #665's routing/discovery work would eventually let a client skip
  the extra hop once that work lands — proxy-through is what makes
  Realtime extractable *today*, without blocking on it, and nothing about
  this decision forecloses layering direct-connect in later as an
  optimization once #665 gives a client a real way to discover and trust
  a Realtime node's address.
- **The existing cross-node relay mesh (#539/#584) already reaches a
  separate Realtime node correctly.** `crate::realtime_relay::relay_to_peers`
  posts every locally-originated presence/chat event to any same-network
  peer advertising a `realtime`/`gateway`/`combined` role via #362's peer
  table (DHT-scoped via #584's interest registry when available) — a
  dedicated Realtime node is exactly such a peer. Proxy-through composes
  cleanly with this: a REST mutation handled by the Gateway (e.g.
  `PUT /me/presence`, `POST .../messages`) still relays to the Realtime
  node exactly as it would to any other realtime-capable peer, and the
  proxied WebSocket connection — which, once dialed, is a dumb byte pipe
  terminating in `handle_presence_socket`/`handle_chat_socket` running
  *on the Realtime node itself* — receives it from there.

## Alternatives considered

- **Direct-connect now, formalized via a hardcoded/env-configured single
  Realtime URL instead of waiting for #665.** Rejected for this pass:
  it would mean shipping a second "which URL does the client use for
  what" concept (today: always the Gateway) for exactly one surface,
  ahead of the routing/discovery design (#665) that's supposed to own
  that decision generally. Revisiting this once #665 lands is explicitly
  left open, not foreclosed.
- **No local fan-out on the Gateway at all, relying purely on the relay
  mesh and requiring every client to know both a Gateway and a Realtime
  URL.** Rejected for the same client-simplicity reason as direct-connect
  generally — it's a variant of the same alternative.

## Consequences

- `crate::realtime_proxy` is the new home for the proxy implementation
  (frame pumping, remote-URL construction, the restart/unreachable
  failure path — a real `Close` frame to the client, never a silent
  hang).
- `AppState::realtime_remote_url` is the resolved `Option<String>` every
  WebSocket handler checks; `None` (the default — `combined`, or any role
  list including `realtime`) means this process still serves
  `/ws/presence`/`/ws/messages` locally exactly as before this issue.
- A Gateway configured this way still constructs a full local
  `PresenceStore`/`ChatBus`/`InterestRegistry` in `AppState` (this issue
  doesn't split `AppState` itself apart, only the WebSocket-serving
  decision) — they simply have no locally-terminated WebSocket
  connections registering into them, other than whatever the relay mesh
  feeds `PresenceStore::apply_relayed`/`ChatBus::publish_*` from a peer.
- Every realtime message now crosses one extra network hop on a Gateway
  configured this way (client -> Gateway -> Realtime -> Gateway ->
  client) versus terminating directly. Accepted as this decision's
  explicit tradeoff for keeping client-facing behavior unchanged.
- `docs/architecture/nodes.md`'s "Today in the repo" section documents
  this split and links back here.

## Related

#291, #661, #662, #664, #665, #78, #539, #584, #663
