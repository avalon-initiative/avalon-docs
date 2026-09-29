# Integrating a game

**Status:** Implemented — the capabilities described are available now; cross-game features marked Planned are not built.

This page explains what Avalon offers a game developer and what it does not take. Games are the first and most developed use case for Avalon, though not the only one (see [apps and services](apps-and-services.md)).

The short version: build the game and let Avalon handle the network around it. The game keeps its gameplay, characters, world, progression, economy, servers, and business model. Avalon supplies identity, social, guild, and attestation infrastructure that already exists and outlives the game.

## What a game gets

- **Identity without another account.** A player connects an existing Avalon identity instead of creating yet another login, friends list, and guild system. The first session starts already socially connected.
- **Social infrastructure it does not have to build or operate.** Friends, blocking, presence, guilds with roles and channels, conversations, and cross-device state live at the network level. The game asks for "this player's guild and its channels" and puts its own UI on top. It does not stand up servers, storage, or delivery for these.
- **Communities that outlive the game.** A guild is a network entity ([ADR 0074](../architecture/decisions/0074-guilds-are-network-level-primitives-not-game-owned.md)), not rows in one game's database. It keeps existing when the game is offline, replaced by a sequel, or shut down, and members stay reachable through the Hub or other clients.
- **Verifiable history.** A game can attest that a player defeated a boss or won a tournament as a signed claim other integrators can verify. See [issuing achievements](achievements.md).
- **Optional interoperability.** A game can choose to recognize another integrator's attestations (a boss kill in one game unlocking a title in another). Recognition is always the receiving game's decision, and nothing requires trusting another issuer blindly. See [trust model](../protocol/trust-model.md).
- **Character freedom.** Characters stay entirely game-specific. One identity can sit behind unrelated characters across games ([ADR 0067](../architecture/decisions/0067-identity-is-separate-from-game-characters.md)).
- **Choice of depth.** A small game might use only identity, friends, and guilds. A larger one might add chat, presence, and achievements. A game with rich state may publish schemas describing part of it through the [integrator space](../protocol/integrator-space.md). Nothing forces deeper integration.

## What a game keeps

```text
YOUR GAME                      AVALON
World                          Identity
Gameplay                       Friends
Characters                     Guilds
Combat                         Communication
Progression                    Presence
Economy                        Achievements and provenance
Rules and moderation
Monetization
```

The game also keeps the final say over what it recognizes from elsewhere on the network.

## Effects that depend on network size

Some benefits depend on other integrators being connected: showing that members of a player's guild are playing a game, guild events that span games, and social matchmaking across games are possible because guilds are network entities. They are consequences of the model, not features that exist as ready-made SDK calls. Treat them as **Planned** integrator-level features built on guild and presence data, and check the [SDK design](../sdk/design.md) for what is exposed today.

## What is not available

There is no cross-game currency, wallet, or purchase primitive, and no ownership or provenance for in-game items. An achievement is a claim about an event, not an asset. See [future layers](../architecture/future-layers.md).

## Getting started

Follow [building an integration](building-an-integration.md), pick an SDK from [language support](../sdk/language-support.md) (C# for Unity, Rust, or TypeScript), and read [capabilities](capabilities.md) to plan which grants to request.

## Related

- [Apps and services](apps-and-services.md)
- [Building an integration](building-an-integration.md)
- [Guilds](../protocol/guilds.md)
- [Cross-integrator events](../protocol/cross-integrator-events.md)
- [Disaster recovery](../architecture/disaster-recovery.md)
