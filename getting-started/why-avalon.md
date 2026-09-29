# Why Avalon

**Status:** Reference — the motivation and positioning for the project, not a specification.

The internet was built to connect computers, and identity and social connection never became protocol-level concepts the way addressing and routing did. Every app and game built its own private answer to "who are you" and "who do you know", and each one makes people start over. This page explains the gap Avalon targets and what it does and does not claim.

The idea that motivates it is small and specific: **a person's identity does not belong to any single world they visit.** Avalon does not try to build one universal world or avatar, only the shared identity layer underneath many worlds.

## The internet was supposed to do this already

A different login for every service, a friends list that means nothing outside the app it lives in, and a history and reputation that disappear when you leave are the ordinary experience of the internet. Avalon does not try to fix the whole internet. It tries to show, for one domain, what an open identity and social layer looks like when it is built as infrastructure instead of a product feature: the same identity, friends, and earned history, portable across everything that chooses to connect.

## What already exists

Pieces of the idea exist, each built by a company for its own purposes:

- **Platform accounts** (Steam, Xbox Live, PlayStation Network, Epic Online Services) give one identity, friends, and presence across games on that platform. Across platforms they do not know each other.
- **Achievement systems** (Gamerscore, Trophies, Steam achievements) are portable within one platform's games, verified by one company, and meaningless outside it.
- **Avatar portability** (for example Ready Player Me) is about how a person looks, not who they are, what they have done, or who they know.
- **In-game guilds and clans** are real communities that die when the game's servers do.
- **Chat platforms** (Discord) hold communities that outlive any game, but know nothing about identity, achievements, or trust inside those games.
- **Blockchain gaming identity projects** tried to solve portability with tokens and wallets, and mostly produced speculative assets rather than something users wanted.

## The gap

Each of these is one or more of:

1. **Platform-locked:** it works only across games one company controls.
2. **Character- or avatar-shaped:** portable appearance, not portable identity.
3. **Proprietary:** closed, unextendable, and not something an independent developer can self-host or build against without a platform holder's permission.

None separates the **user** from the **character**. A guild in an MMO is rows in one database. An achievement is a badge image verified only by the platform that issued it.

What has not been built is an **open, self-hostable protocol** where:

- identity is first-class and independent of any character, platform, or single company's servers;
- friends and guilds are network-level entities that outlive any one game;
- achievements are verifiable claims a receiving integrator can trust or ignore on its own terms;
- and any independent developer can connect without a platform holder's permission.

## What Avalon claims

Avalon does not claim to be the first to imagine persistent cross-game identity. It claims to be building the open, protocol-level infrastructure for it, the piece platform-locked and character-locked attempts skipped because none had a reason to make their version work for someone else's game.

"Open" has a specific meaning here: a user's identity is a fact any integrator can read, not a fact that depends on which server it happens to trust. That rules out federation (servers deciding whether to recognize each other) as much as a single company's walled garden, since both make identity conditional on a relationship between servers instead of a property of the user. The mechanism is a public, verifiable log; see [settlement](../architecture/settlement.md) and [network trust anchors](../protocol/network-trust-anchors.md).

For the design that follows from this, see the [design proposal](../architecture/design-proposal.md): identity separate from characters, guilds and friends as network entities, achievements as attestations, and integrators that stay fully sovereign while opting into whichever parts they want.

## What this is not

This is not a government or platform digital-ID system and is not on a path to becoming one. An Avalon identity identifies a keypair, not a person. No name, government ID, biometric, or other real-world identifier exists anywhere in it, by construction and not by policy. There is no validator set, no platform owning identity, and no single operator that could be compelled to produce a mapping from a keypair to a human, because that mapping is never collected. What is portable is online activity (who you have played with, what you have earned, which communities you belong to), never personhood. See [identity](../protocol/identity.md) and [privacy](../protocol/privacy.md).

> A character in one game can remain unique to that game, and a character in another can be completely different. The person behind them stays the same, and for the first time that fact is something the integrators themselves, not just one platform, can recognize.

## Who this belongs to

Not one studio and not one company selling access to the things built on it. It is built by the Avalon Initiative, and the name describes the shape of the thing rather than a legal wrapper around one team. A node operator mirroring the log, a studio integrating an SDK, and a hoster running a node for their own community are all doing the same thing: participating in an open protocol. It stays open not through one party's goodwill but because enough separate parties run it that none could close it. See [self-hosting](../architecture/self-hosting.md) and [running a node](../developers/running-a-node.md).

## Related

- [What is Avalon?](what-is-avalon.md)
- [Concepts](concepts.md)
- [Why build an integration](../integrations/games.md)
- [Design proposal](../architecture/design-proposal.md)
