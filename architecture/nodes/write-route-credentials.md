# Node-to-Node Write Routes

**Status:** Implemented — two residuals are open: a first-writer-wins replica insert, and relayed chat events carry no binding between the sending node and the scope (#1121)

Three routes let one node push data into another: `POST /nodes/relay` (live presence and chat events), `POST /nodes/replicate-chat` (at-rest copies of chat history), and `POST /mirror/notify` (a prompt to poll a mirror source early). They carry no user session, so the caller has to be identified as a node, and what that node may do through each route is checked per route. This page defines the credential, the standing a caller needs, the refusals, and the per-route checks. Transport is on the [connectivity](connectivity.md) page; the general limits are on [safety limits](safety-limits.md).

## The credential is the node's identity key

Every node has a libp2p identity key. That key is the credential, and there is no unsigned fallback: a request without one is refused, and all nodes in a network update together.

| Transport | What identifies the caller |
| --- | --- |
| libp2p stream | The peer id authenticated by the noise handshake. A relay cannot forge it. Any `x-avalon-node-auth` header on a stream request is ignored. |
| HTTP | The signed `x-avalon-node-auth` header. The signing key must hash to the peer id the header claims. |

The signed header is `v1; peer=<id>; key=<hex>; ts=<unix seconds>; nonce=<hex>; bh=<hex>; sig=<hex>`, parsed strictly (one header, ASCII, seven fields in that order, lowercase hex, at most 512 bytes). The Ed25519 signature covers a domain tag, the method, the raw request path, the SHA-256 of the body, the network id, the intended recipient, the claimed peer id, the timestamp, and the nonce. A captured header therefore cannot be replayed against another route, body, network, or recipient. The format and a conformance vector are in the protocol repository (`conformance/vectors/node-request.json`).

The recipient is the receiving node's libp2p peer id or the origin (scheme, host, port) of its own http(s) base URL. A sender signs for the peer's libp2p id when its peer table has one, and for the URL's origin otherwise. A peer URL with a path prefix cannot be signed, so requests to it are refused.

### Verification order over HTTP

1. The header is parsed, its timestamp must be within 60 seconds of the receiver's clock, and its key must hash to the claimed peer id.
2. The signer must have standing (below).
3. The signature is checked against the header's own body hash, which fixes the method, path, network, and recipient. A signature made for another recipient or network is indistinguishable from a forged one and is refused as a bad signature.
4. The nonce must not have been used by that signer.
5. Only then is the body read, within the route's size cap, a total timeout, an idle timeout, and the signer's budgets. The body's SHA-256 must equal the signed hash.

A stranger is refused before any body is read. A request that fails the signature stage costs the receiver at most one signature verification.

### Single use and replay

A nonce is single use across all three routes. It is consumed when the body read begins, so a captured header that was never used is worth one lost request to its sender, and every later use is a cheap refusal that costs the real sender no budget. A body that never arrives, or does not match its hash, burns its nonce, so senders use a fresh 128-bit random nonce per request.

The receiver keeps a 128-bit truncated hash of the signer id and nonce for each live nonce, for 121 seconds. It never evicts a live nonce: when the cache is full it refuses new requests with 503 until entries expire, which can delay delivery and never opens a replay window. The cache is in process memory, so a restart, replicas that share one identity key, or the clock stepping forward re-opens up to the 60 second window for a captured request. The cache is capped at 1,048,576 nonces and is sized from the peer table limit, since only nodes with standing can fill it.

### Standing

A caller has standing when its libp2p peer id belongs to a bound entry in the main peer table. Binding is defined in [discovery and peering](discovery-and-peering.md#identity-binding-is-not-a-security-boundary): the entry's own URL reported that id. A node known only through gossip, or held only in the unverified pool, has none. A node that announces itself as `p2p://<peer id>` over a stream the handshake authenticated as that id has standing through that entry, so a node with no public URL can call these routes. Standing is cheap to get, because admission to the network is open. It identifies the sender and does not trust it: a credential grants no authority beyond what each route checks below.

Standing is for sending only. A `p2p://` entry is never a chat replication or realtime fan-out target, so the node receives no chat, and it registers its mirror interest under its `p2p://` address. Its `/nodes/relay` and `/nodes/replicate-chat` calls are delivered under its node credential, and the neighbor that stores a replica tags the row with the sender's peer id (`replicated_by`).

Current limitation: such a node cannot be a mirror source. Sources are configured and matched by HTTP URL, so its `POST /mirror/notify` is refused with 403 (scope) even though its credential is valid, and its neighbors learn of new entries by polling. Letting a node with no public URL be a mirror source is planned under protocol issue #1141.

### Gaining standing

A key gains standing by announcing as `p2p://<its id>` over its own libp2p stream. Before it has announced, every call is refused with 403 `node_auth_no_standing` over a stream or signed HTTP, and an HTTP request with no header gets 401 `node_auth_missing`. After the announce, the same key is accepted on `/nodes/replicate-chat` over both transports. Standing is cheap by design: the defence is the bound-peer table cap and the per-signer limits, not the cost of obtaining a key.

### Reading the refusals

A stream request carries no `x-avalon-node-auth` header, since the handshake is the credential. These routes are outside the OpenAPI document, so a client generated from it shows no authentication on them. The node credential applies regardless, and a caller that cannot supply it is refused as below.

| Route | Credential refusals | Scope refusals |
| --- | --- | --- |
| `/nodes/relay` | 401 `node_auth_missing` and the other 401 codes, 403 `node_auth_no_standing` | 403 no local subscriber for the scope, 422 oversize message |
| `/nodes/replicate-chat` | same | 403 not an indexer or combined node, 422 invalid event, 429 replica rate, 404 delete of a row the signer did not insert |
| `/mirror/notify` | same | 403 signer is not a configured mirror source, 400 wrong network or non-positive tree size |

## Refusals

| Status | Meaning |
| --- | --- |
| 400 | The body could not be read, or `/mirror/notify` names another network or a tree size of zero or less. |
| 401 | No header over HTTP, or a header that is malformed, stale, from the future, signed by a key that does not hash to the claimed peer id, has a bad signature, a wrong body hash, or a nonce already used. It is also the answer when the receiver's recipient identity does not match: an ephemeral identity changes on restart, and requests addressed to the old id are refused until the sender learns the new one. |
| 403 | The caller has no standing (no bound entry, so a first contact is refused until the sender has announced), or the route's own scope check fails (below). A 403 reveals whether an id is a known node, which is not secret. |
| 408 | The body was not fully received within the total or idle timeout. A timeout costs the signer ten failure units of its 30 a minute. |
| 413 | The body is over the route's cap: 64 KiB for `/nodes/relay`, 64 KiB for `/nodes/replicate-chat`, 1 KiB for `/mirror/notify`. |
| 422 | A chat message is over the 4000 character send limit, or a replicated message has an implausible sent time. |
| 429 | The signer is over its request budget, has its share of body reads in flight, or has used its failure budget; the source address caused too many expensive failures; or the replica rate is exceeded. Sent with `Retry-After` where the refusal is a load limit. |
| 503 | The replay cache is full, or too many body reads are running at once. Sent with `Retry-After`. |

The response carries a stable `code` (for example `node_auth_replay`, `node_auth_no_standing`, `node_auth_busy`). Delivery on these routes is best effort, and a mirror falls back to polling, so a refusal is a delay or a dropped live event, not lost ledger correctness.

## Budgets and knobs

All knobs are read at startup. A value that is not a positive integer falls back to the default, and values above a ceiling are lowered to it.

| Variable | Default | Meaning |
| --- | --- | --- |
| `AVALON_NODE_AUTH_RATE_PER_MINUTE` | 3000 | Requests one signer may make a minute across the three routes. Fixed one-minute windows, so a signer can burst to twice the rate across a boundary. The default matches the per-IP limit these routes were under, so raise it before lowering it: a node fans one event out per peer. |
| `AVALON_NODE_AUTH_FAILED_PER_MINUTE_PER_IP` | 30 | Expensive failures (bad signature, wrong body hash, oversize body, body timeout) one source address may cause a minute, counted per /64 for IPv6, before further failures are answered 429 uncounted. A valid credential is never refused for the address it came from, since behind a proxy not listed in `AVALON_TRUSTED_PROXIES` every client shares one address. |
| `AVALON_NODE_AUTH_MAX_CONCURRENT_BODIES` | 64 | Body reads running at once; the excess gets 503. A quarter of them is reserved for signers that completed a read in the last 10 minutes. Stream requests take no read stage. |
| `AVALON_NODE_AUTH_MAX_INFLIGHT_PER_SIGNER` | 16 (at most 64) | Body reads one signer may have in flight. |
| `AVALON_NODE_AUTH_BODY_TIMEOUT_MS` | 5000 (at most 30000) | Total time a body read may take. |
| `AVALON_NODE_AUTH_BODY_IDLE_TIMEOUT_MS` | 1500 (at most 10000) | Longest a body read may go without receiving a byte. |
| `AVALON_NODE_AUTH_REPLICATE_PER_MINUTE` | 600 | Replica requests one signer may make a minute to `/nodes/replicate-chat`. |

A signer also has a failure budget of 30 units a minute: a wrong or oversize body or a failed read costs 1, a timeout 10. Standing is cheap, so a determined set of many standing keys, each earning the reserved read stages and then timing out, can still degrade the body read stage; this is stated rather than hidden.

## What each route checks

A credential says who is calling. Each route then checks what that node may do.

### Realtime relay

`POST /nodes/relay` carries presence updates, chat messages, and message deletions.

- A chat event (message, deletion, conversation message) is accepted only for a channel or conversation this node has a connected local subscriber for (403 otherwise), so a node cannot push content for a scope nobody here is listening to.
- A message body over 4000 characters is refused (422).
- Presence has no channel or conversation scope and is accepted from any node with standing.
- A relayed event never makes this node relay onward; it reaches only this node's own live connections.

The sender logs a throttled warning for refusals.

### Chat replication

`POST /nodes/replicate-chat` writes at-rest copies of channel and conversation messages to separate replica tables that carry no foreign keys.

- Served only by a node whose roles include `indexer` or `combined` (403 otherwise).
- At most `AVALON_NODE_AUTH_REPLICATE_PER_MINUTE` requests a minute per signer (429 over it).
- A message body must fit the 4000 character send limit, and its sent time must be after 2024-01-01 and at most 5 minutes ahead of this node's clock (422).
- Each replica row records the signer that inserted it (`replicated_by`). An insert never overwrites an existing row, and a delete applies only to a row the same signer inserted (404 otherwise). Rows replicated before the signer column existed record an empty signer, so no node can delete them, and a node that rotates its identity key cannot delete rows it inserted under the old one.

### Mirror notification

`POST /mirror/notify` prompts a node to poll a mirror source early.

- The signer must be one of this node's configured mirror sources: a peer bound in the table whose URL has the same origin as a source in `AVALON_MIRROR_PEERS` (the network's seed nodes when it is unset). Any other signer gets 403. The match is on scheme, host, and port, so a source configured by hostname but announced by IP address is refused and the node polls instead.
- The network id must be this node's, and the tree size positive (400 otherwise).
- The mirror watcher is woken only when the announced tree size is greater than what this node has already observed from that source. A stale size is acknowledged with 202 and wakes nothing.
- The notification is a prompt to look, never a source of truth. Every entry is still verified by the mirror pipeline, and the route starts no outbound work itself.

## Known residuals

These are what the standing-peer model does not close, stated as they are in the code.

- Replica inserts are first-writer-wins. A node with standing can insert a message id before the node that originated the message replicates it, and the later, genuine insert is a no-op.
- Relayed events carry no signer-to-scope binding. A relayed chat or presence event is not tied to the node that sent it, and carries no sent time, so a node with standing is trusted for the content of events in scopes this node has a subscriber for.

Both are tracked as protocol issue #1121, which proposes attributing replicated and relayed chat events to their origin node.

## Implementation

Status: Implemented. The signing format is in the [protocol crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/protocol) (`node_request`), and enforcement is in the [server crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/server) (`node_auth`, `realtime_relay`, `chat_replication`, `mirror_push`). Hosting variables are in the protocol repository's [hosting docs](https://github.com/avalon-initiative/avalon-protocol/tree/main/docs).

## Related

- [Nodes](README.md)
- [Connectivity](connectivity.md#node-to-node-requests-over-libp2p-streams)
- [Discovery and peering](discovery-and-peering.md#identity-binding-is-not-a-security-boundary)
- [Safety limits](safety-limits.md)
