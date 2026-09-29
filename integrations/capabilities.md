# Capabilities

**Status:** Partially implemented — nine capabilities are used by SDK methods; the rest of the vocabulary is defined but has no SDK surface.

A capability is a named permission a person grants an integrator, such as `friends.read` or `achievements.issue`. An integrator receives only the capabilities explicitly granted, can lose them at any time, and never gets blanket access to an identity's history. This page lists them and explains what a missing grant means. The underlying model is in [bindings](../protocol/bindings.md).

## The capability list

Capabilities are permanent wire strings. The string, not any language's enum name, is the stable identifier a grant is stored and compared against. An SDK preserves a capability string it does not recognize instead of failing, so a new server-side capability never breaks an older SDK.

Used by SDK methods today:

| Capability | Unlocks |
| --- | --- |
| `friends.read` | Reading the person's friends list. |
| `presence.read` | Reading presence, subscribing to presence updates, and presence embedded in friends and guild rosters. |
| `guilds.read` | Listing the person's guilds, guild rosters, and guild events. |
| `guilds.chat` | Listing guild channels, reading channel messages, and posting as the person. |
| `achievements.read` | Reading the person's full attestation history. |
| `achievements.issue` | Issuing an achievement to the person. |
| `milestones.issue` | Issuing a milestone (the app and service equivalent of an achievement). |
| `messages.read` | Listing conversations and reading their messages. |
| `messages.send` | Creating or getting a 1:1 conversation and sending messages. |

Defined in the vocabulary with no SDK method checking them: `identity.read`, `profile.read`, `presence.publish`, `guilds.issue`, `assets.read`, `assets.issue`, `wallet.read`, `wallet.write`. The `assets.*` and `wallet.*` names belong to the [future economic layer](../architecture/future-layers.md), which is Planned and not built. The authoritative source is the protocol's capability definition in [`permissions.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/permissions.rs).

Two things need no capability: a person reading their own profile with a valid session, and a person publishing their own presence status.

## How a person grants one

Through a consent flow in a first-party client such as the Hub, which calls the server's connect endpoint for the integrator. There is no SDK call for an integrator to request a grant, because the grant is the person's act. A person can revoke an individual grant or disconnect the integrator entirely.

## What a missing grant means

A capability error means exactly one of: the person never granted it, or the grant existed and was revoked. The SDK checks before making a request, so it costs no round trip. The server enforces the same check independently on every request, so the client-side check is a convenience and never the security boundary. See [errors and retries](errors-and-retries.md).

Grants are least-privilege by design: granting guild access does not imply friends, private messages, or achievement history.

## Related

- [Bindings](../protocol/bindings.md)
- [Security model](../protocol/security-model.md)
- [Building an integration](building-an-integration.md)
- [SDK design](../sdk/design.md#capability-checks-per-method)
