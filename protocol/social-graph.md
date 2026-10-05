# Social Graph

**Status:** Partially implemented — friendships, blocks, and discovery are built; capability-gated integrator reads of the graph are Planned.

An identity's friends are a network-level relationship that persists across integrators, so entering a new integrator never means rebuilding a friends list. An integrator never automatically receives an identity's social graph: any read of it is meant to be gated by a capability the identity granted and by the visibility the identity set.

## What persists

| Thing | Persists across integrators? | Where it lives |
| --- | --- | --- |
| Friendship (identity A and identity B) | Yes | a durable network relationship, owned by the network and not by either identity's current integrator |
| Friend requests (pending state) | Until resolved | server state for the pending record; sending a request also commits a `friend.requested` event to the public ledger |
| Presence of a friend | Ephemeral | see [presence](./presence.md) |
| Blocks and mutes | Yes | server state, never durable history (below) |
| An integrator's in-world social features (party, LFG) | No | integrator-side |

A friendship is symmetric: `Friendship { a, b, since }`. It references two [identities](./identity.md), never two game characters. An identity sees the same friends list from the Hub, from Integrator A, and from Integrator B, filtered by what each viewer is allowed to see. A friendship is promised-durable history (`friend.requested`, `friend.accepted`, `friend.removed`, see the [event catalogue](./protocol-events-catalogue.md)), since it is a social fact between two identities that no integrator owns. A declined or withdrawn request is not durable; only an established or ended friendship is. In the code, the friendship projection is built from `friend.accepted`, `friend.removed` and the recovery reversal; `friend.requested` is recorded on the ledger, but a pending request's state is server-owned and a rebuild does not restore it.

## What an integrator sees

**Planned as specified; the server does not yet enforce it.** Requesting `friends.read` is meant to mean: for the identity that granted it, under an active [binding](./bindings.md), the integrator may read the friends the identity chose to expose to integrators, enough to say "your friend Alice is also here", not a dump of the identity's relationships. `presence.read` is a separate capability, so an integrator may know who someone's friends are without knowing where they are.

The intended composition is three checks in order: an active binding, an active `PermissionGrant` for the specific capability, then the [visibility](./privacy.md) scope the identity set. None widens the others.

What exists today: friends endpoints accept only an identity session token, with no integrator-credential path, so an integrator cannot act on an identity's behalf here by construction. SDKs check the granted capabilities client-side before calling, but the server-side capability check exists only for writes such as `presence.publish` and attestation issuance. There is no integrator-facing friends read path on the server.

## What this powers

- friends lists in the Hub and in any integrator that asks
- "who's online and where" (with presence)
- cross-integrator invitations and coordination (later, via [communication](../architecture/communication.md))
- guild rosters intersected with friends
- matchmaking that an integrator chooses to build on top

## Blocking and harassment

Persistent identity makes harassment persistent too. Blocking works across integrators, not per integrator: a block hides the blocker's presence and refuses friend requests network-wide, in both directions. Unlike friendship it is never durable protocol history, never a protocol type, and never revealed to the blocked party through any endpoint (see [privacy](./privacy.md)). A blocked pair's friend request is rejected identically to one naming a nonexistent identity, and a blocked identity's presence reads as `Offline`, indistinguishable from a missing entry. Blocking a partner with a pending request resolves that request.

The same never-reveal rule extends to direct and small-group conversations: a send is rejected if a block exists between any two participants, using the same error a genuine non-participant gets, so a blocked participant's failed send is indistinguishable from never having been in the conversation (see [communication](../architecture/communication.md)). What a block means inside an integrator (matching, shared worlds) remains the integrator's decision, informed by the network fact.

## Handles and discovery

`display_name` is the handle: globally unique and case-insensitive, with no discriminator suffix. Uniqueness is enforced at the write itself by an index, so a concurrent writer cannot race past a prior check, and a taken name is a hard rejection at registration. A node projecting another shard's creation stores a later claimant of a taken name as `name~<id prefix>`, so cross-node names are best effort and the id is the identity ([identity](./identity.md#names-across-nodes)). This follows the current Discord scheme of a globally unique handle rather than the deprecated `name#1234` scheme, whose small numeric space became crowded at scale. `GET /friends/handle/{handle}` resolves an exact handle to an identity id.

Discovery is two-tier and private by default:

- **Always on, relationship-based.** `GET /people/discover` takes no query parameter: it surfaces friends-of-friends and identities sharing a guild with the caller, minus the caller, existing friends, and blocked relationships. It is read-only; acting on a suggestion still goes through the friend-request endpoint.
- **Opt-in name search.** `GET /identities/search?q=` matches only identities that switched on the `discoverable` preference (off by default for every identity, no exceptions). Matching is a case-insensitive substring match on the handle. Turning the preference off removes the identity from search immediately, since it is read live on every call. A non-opted-in identity never appears in search even to a caller who knows its exact handle; exact-handle resolution is a separate path.

## Implementation

Status: implemented for identity-session access; capability-gated integrator reads are not.

- Types: `Friendship`, `FriendRequest` in [`social.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/social.rs). There is no block type in the protocol crate.
- Server: [`friends.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/friends.rs), [`blocks.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/blocks.rs), [`discovery.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/discovery.rs). Events are enqueued through the outbox in the same transaction as the projection row. They are session-authenticated and node-attributed, not individually signed.
- Endpoints (see the [OpenAPI document](https://github.com/avalon-initiative/avalon-protocol/blob/main/docs/generated/openapi.json)): `/friends`, `/friends/requests`, `/friends/requests/{id}/accept`, `/friends/{identity_id}`, `/friends/handle/{handle}`, `/blocks`, `/people/discover`, `/identities/search`.

## Related

- [Identity](./identity.md), [guilds](./guilds.md), [presence](./presence.md), [privacy](./privacy.md), [bindings](./bindings.md)
- [Communication](../architecture/communication.md)
- [Protocol events](./protocol-events.md)
