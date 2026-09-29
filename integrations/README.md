# Integrations

**Status:** Implemented — identity, friends, presence, guilds, messaging, and achievements can be integrated today; economic and portable-asset features are Planned.

An integration is a game, app, or service (an **integrator**) that connects to an Avalon network to use persistent identity, social features, and verifiable achievements without building that infrastructure itself. This section explains why and how to integrate at the concept level, independent of language; the SDK repository holds language-specific code.

## Pages

| Page | What it covers |
| --- | --- |
| [Games](games.md) | What Avalon offers a game, and what it never takes. |
| [Apps and services](apps-and-services.md) | Non-game integrators: websites, tools, community services. |
| [Building an integration](building-an-integration.md) | The end-to-end flow: register, get consent, authenticate, use capabilities, issue and verify. |
| [Capabilities](capabilities.md) | The capability list, how grants work, and what a missing grant means. |
| [Issuing and verifying achievements](achievements.md) | Register as an issuer, define, issue, read, verify, revoke. |
| [Friends, presence, guilds, and messages](social-features.md) | Reading the social graph and community data, and what is scoped. |
| [Errors and retries](errors-and-retries.md) | The error taxonomy and what is safe to retry. |

## The integration model in brief

1. The integrator registers and holds its own signing key. Avalon stores only the public half.
2. A person connects the integrator and grants specific capabilities. Nothing is granted by default.
3. The integrator authenticates with the person's session token and its credential, and acts only within those grants.
4. Anything the integrator asserts (an achievement) is signed with its own key and verifiable by anyone.
5. Every other integrator decides for itself whether to recognize that assertion.

The integrator stays sovereign throughout: its world, rules, characters, economy, and moderation remain its own.

## Related

- [SDKs](../sdk/README.md)
- [Concepts](../getting-started/concepts.md)
- [Bindings](../protocol/bindings.md)
- [Trust model](../protocol/trust-model.md)
- [Developers: learning path](../developers/README.md)
