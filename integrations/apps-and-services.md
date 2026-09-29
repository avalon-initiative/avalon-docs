# Integrating an app or service

**Status:** Partially implemented — the integrator model is not game-specific and works for any app or service; there are no non-game reference integrations other than first-party clients.

Avalon is not games-only. Any website, app, tool, or community service can be an integrator: it connects to the same identity and social layer through the same SDKs and the same capability model. This page describes what that looks like and where the game-oriented vocabulary does not apply.

## What is the same

- **Identity and grants.** A person connects the service and grants capabilities. The service sees only what was granted. See [capabilities](capabilities.md).
- **Attestations.** A service can issue signed claims about its own domain (a completed course, a verified contribution, a community role) and verify others' claims. In the protocol, the equivalent of an achievement for an app or service is a **milestone** (`milestones.issue`), an attestation about progress in a non-game context.
- **Recognition is local.** The service decides which issuers it trusts. Avalon never ranks integrators.
- **Sovereignty.** The service's data, rules, and business model stay its own. It publishes to Avalon only what it chooses.

## Examples of fit

| Integrator | Uses |
| --- | --- |
| Community website or forum | Login with an Avalon identity; show a member's guilds and verified history. |
| Chat or Discord-style client | Read friends, presence, and guild channels as another client of the same network. |
| Streaming or events tool | Verify achievement attestations; issue participation attestations. |
| Developer or analytics tool | Read public network data, as the topology visualizer does. See [ecosystem: topology](../ecosystem/topology.md). |

These are illustrations of the model, not a list of shipped integrations. The first-party clients (the [Hub](../ecosystem/hub.md) and the topology visualizer) are the working examples of non-game clients, and the Hub is built on the same SDK and API as any third party.

## What differs from games

- Terms like "character" and "guild" may not map to a service's domain. Use the parts that do: identity, social graph, attestations, and the [integrator space](../protocol/integrator-space.md) for publishing structured data.
- The Discord bot in this ecosystem does not integrate Avalon yet; see [ecosystem: bot](../ecosystem/bot.md).
- Client-only front ends should use the TypeScript SDK, which drives a real WebAuthn ceremony. See [language support](../sdk/language-support.md).

## Getting started

The flow in [building an integration](building-an-integration.md) applies unchanged.

## Related

- [Games](games.md)
- [Building an integration](building-an-integration.md)
- [Integrator space](../protocol/integrator-space.md)
- [Issuers](../protocol/issuers.md)
