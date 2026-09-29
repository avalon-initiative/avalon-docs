# Cross-Integrator Events

**Status:** Planned — no event-specific module exists; the design reuses the implemented attestation mechanism and is on hold as a feature.

An integrator event result is an attestation for a durable, cross-integrator-relevant outcome that an integrator produces: a tournament, a seasonal championship, a world-first race, a community campaign. The integrator runs the event, decides the outcome, and signs a claim; Avalon carries that durable fact; another integrator verifies it and decides for itself what to do. The event's gameplay (brackets, live scores, matchmaking, spectator state) never enters the protocol. Only the result crosses the boundary. It needs no new primitive. The mechanism is domain-agnostic and is illustrated with games because games are the first live use case.

## The flow

```text
The Great Avalon Championship (a tournament: one kind of integrator event)

Integrator A (Ashen Realms)
    |
    +-- runs the event, entirely integrator-side
    +-- determines the outcome
    +-- issues a signed attestation
             |
             v
       Avalon Protocol (recorded, indexed, verifiable)
             |
             v
Integrator B
    verifies:   authentic? valid?
    decides:    recognized? -> legendary title, cosmetic, event hall access, or nothing
```

The attestation:

```text
Issuer:        game:ashen-realms
Event:         game:ashen-realms:integrator_event:avalon-championship-2027
Subject:       Avalon Identity X
Achievement:   game:ashen-realms:integrator_event:avalon-championship-2027:winner
Issued at:     2027-08-14T20:11:03Z
Schema:        game-event-result/v1
Signature:     ...
```

Every check Integrator B performs is the standard one from the [trust model](./trust-model.md): the signature proves Ashen Realms issued it, history proves it is not revoked and the issuer was in good standing, and B's own recognition policy decides whether this event from Ashen Realms unlocks anything.

## Not a new primitive

Results reuse [achievements and attestations](./achievements-and-attestations.md) with a namespaced id and a schema reference:

```text
game:<slug>:integrator_event:<event-id>:winner
game:<slug>:integrator_event:<event-id>:finalist
game:<slug>:integrator_event:<event-id>:participant
```

The event itself gets an identity (a `GlobalId` of kind `game_event`) so that participation, placement, and victory attestations from one occurrence can be grouped, and so a consumer can scope a recognition policy to that event rather than to everything the issuer ever signs. A schema reference on the definition ("this is an event result, version 1") lets a consumer recognize the shape independently of the issuer's naming. There is no separate settlement path: a result is `achievement.issued` with the game-event schema, batched and committed like any other [protocol event](./protocol-events.md). The catalogue row `game_event.result_issued` describes exactly that and is not a distinct emitted kind.

## What counts as an integrator event

Anything an integrator runs that produces a durable, interoperable outcome worth recording outside it: tournaments and championships, seasonal events and world-first races, guild competitions (a guild-level subject rather than an identity), community campaigns, cross-integrator quests with a recorded completion, developer-sponsored events, esports results, and collaborative achievements.

What does not cross the boundary: matchmaking, brackets, live scores, spectator state, in-progress rounds. Do not assume all gameplay needs to become protocol data; only the final, durable result does.

## Recognition is still contextual

Three integrators can each run a "championship" and issue "winner". Provenance makes them distinct and nothing makes them equal. Integrator B may trust Ashen Realms' results and ignore Integrator C's, and the Hub shows both with the issuer named. The [registry](./registry.md) may eventually report event activity as a derived metric and never ranks events or the integrators that ran them.

## Scenario G: cross-integrator event

Can Integrator A issue an event result that Integrator B can verify? Yes: A signs it under a registered [issuer key](./issuers.md), Avalon records and indexes it, and B checks authenticity and validity through the SDK and applies its own policy. If A later revokes the result (a disputed match, a scoring correction), history shows both the issuance and the [revocation](./revocation.md), and B re-evaluates.

## Implementation

Status: nothing event-specific is built. The design reuses `AchievementAttestation` and `GlobalId` ([`achievements.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/achievements.rs), [`ids.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/ids.rs)). The schema reference lives on `AchievementDefinition.schema`, not on the attestation, which only references its achievement. The feature is on hold and tracked so the existing attestation and event designs do not preclude it.

## Related

- [Achievements and attestations](./achievements-and-attestations.md), [trust model](./trust-model.md), [revocation](./revocation.md), [registry](./registry.md), [issuers](./issuers.md)
- [Integrations for games](../integrations/games.md)
