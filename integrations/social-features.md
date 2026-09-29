# Friends, presence, guilds, and messages

**Status:** Implemented — reads and messaging listed here are available; guild administration is intentionally not available to integrators.

An integrator can read a person's friends, presence, guild memberships, and conversations, and post messages as the person, all within the capabilities the person granted. This page explains what each read returns and where the boundaries are. Concepts: [social graph](../protocol/social-graph.md), [presence](../protocol/presence.md), [guilds](../protocol/guilds.md).

## Friends

Reading friends requires `friends.read`. Each friend can carry presence, but only when `presence.read` is also granted; it is embedded through one batched lookup rather than a request per friend, so there is nothing extra to ask for. A friend's display name is not resolved today because no endpoint resolves another identity's profile; the SDKs return it empty.

## Presence

Reading presence requires `presence.read`. A person publishing their own status needs no capability. Reads are filtered server-side by each subject's own visibility setting (default: friends). A caller gets a real status only for an identity that is themselves, a friend, or where the setting is public or authenticated-only. Everyone else reads as offline, indistinguishable from a missing entry, the same posture applied to a block. Live-push subscriptions over WebSocket are available in addition to point-in-time reads. Presence is ephemeral and never enters durable history ([ADR 0078](../architecture/decisions/0078-realtime-presence-is-ephemeral-and-never-enters-durable-history.md)). See [privacy](../protocol/privacy.md).

## Guilds

`guilds.read` covers the person's memberships, rosters, and events. `guilds.chat` covers channels and messages; the two are separate, with no blanket guild grant. Rosters embed presence the same way friends do. Channel and message reads are filtered by the server's per-channel view permissions.

**Integrators never act with guild authority.** Creating guilds, inviting, kicking, changing roles, and managing channels stay identity-authority actions taken by the person, for example through the Hub. Posting a channel message is done as the identity, under their own session, never as the integrator.

## Conversations

Direct and small-group messages need `messages.read` to list and read and `messages.send` to send or create a 1:1 conversation. A rejected read or send returns the same error whether the caller was never a participant or is blocked, deliberately, so the API never reveals that a block exists.

## Related

- [Capabilities](capabilities.md)
- [Social graph](../protocol/social-graph.md)
- [Guilds](../protocol/guilds.md)
- [Presence](../protocol/presence.md)
- [Privacy](../protocol/privacy.md)
