# Building an integration

**Status:** Implemented — every step below is available in all three SDKs unless noted.

This page walks through the language-agnostic flow of connecting a game, app, or service to an Avalon network: register, obtain consent, authenticate, use capabilities, and issue or verify claims. Language-specific code and installation live in the [SDK repository](https://github.com/avalon-initiative/avalon-sdks); the concepts are the same in every language.

## Overview

```text
1. Choose network + SDK
2. Register the integrator  ──►  you hold a private signing key
3. (to issue) Register as an issuer on the target network
4. Person connects you and grants capabilities (in the Hub or your own UI)
5. Authenticate with the person's session token  ──►  capability-gated session
6. Read / act within grants; issue signed attestations
7. Handle errors; retry only what is safe
```

## 1. Choose a network and an SDK

An integrator targets a specific network by `network_id`. A `network_id` alone has no authority; the SDK verifies the server's signed tree head against the pinned trust anchors ([network trust anchors](../protocol/network-trust-anchors.md)). When registering as an issuer, the integrator must state which network it means (the exact id or a deployment tier). The SDK refuses, before sending anything, if the server verifies as a different network. This catches configuration copied from the wrong environment.

Pick an SDK from [language support](../sdk/language-support.md). For local development, run a node ([running a node](../developers/running-a-node.md)) with the `avalon-dev-local` network, which is a standalone node with no seed peers.

## 2. Register the integrator

Registration creates the integrator record (a slug and metadata) and its credential. The integrator's Ed25519 private key is shown once and stored only by the integrator; the server keeps the public half. Registration is a call on the client before any person session exists. The dev CLI can also do it for local work. See [issuers](../protocol/issuers.md) and [registry](../protocol/registry.md).

## 3. Register as an issuer

To issue attestations on a real network, the integrator's signing key must be admitted to write on that network. This per-network registration is separate from step 2 ([ADR 0479](../architecture/decisions/0479-network-isolation-via-per-network-issuer-registration-not-signature.md)). Details are in [issuing and verifying achievements](achievements.md).

## 4. Obtain the person's consent

A person grants the integrator capabilities through a consent flow, typically in the Hub, which is a first-party account client. There is no SDK call for an integrator to request a grant, because granting is the person's act. In production the integrator sends the person to a consent surface and receives a session token back; the transport (deep link, redirect, pasted code) is the integrator's choice. Clients without a WebAuthn surface, such as a console or game engine, use device-pairing login. See [bindings](../protocol/bindings.md) and [capabilities](capabilities.md).

## 5. Authenticate

The integrator presents the person's session token with its own credential key id. The SDK reads the person's profile and this integrator's active grants, and returns a session scoped to those grants. The session token is something the integrator never mints itself. Reading the person's own profile needs no grant beyond a valid session.

## 6. Use capabilities

Each session method requires a named capability and fails fast without it. See [capabilities](capabilities.md) for the list, [social features](social-features.md) for friends, presence, guilds, and messages, and [achievements](achievements.md) for issuing and verifying. Two rules hold throughout:

- The integrator acts on a person's behalf only inside grants, and only for that person. It cannot exercise guild authority or account-level power.
- The server enforces the same checks; client-side checks are a convenience.

## 7. Handle errors

Errors arrive as a small typed set, and only calls that are provably safe are retried. See [errors and retries](errors-and-retries.md).

## Local development

To exercise the whole flow without a game client, run a local node and use the dev CLI (`avalon`): create an identity, log in for a token, register an integrator, and issue an achievement through the same SDK call a real integration uses. Commands are in the protocol repository's [local development guide](https://github.com/avalon-initiative/avalon-protocol/blob/main/docs/maintainers/local-development.md). Mutating dev commands exist only in the default dev-tools build of the CLI and are stripped from deployment builds.

## What moved to the SDK repository

Language-specific walkthroughs (crate and package installation, client construction, per-language code samples, runnable examples) belong with each SDK in [avalon-sdks](https://github.com/avalon-initiative/avalon-sdks).

## Related

- [Integrations overview](README.md)
- [SDK design](../sdk/design.md)
- [The recovery ladder](../protocol/identity/recovery-ladder.md): what to tell users at onboarding, and why total key loss is final
- [Trust model](../protocol/trust-model.md)
- [Running a node](../developers/running-a-node.md)
