<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-blue.svg" alt="License: Apache-2.0"></a>
  <a href="https://discord.gg/FFDsFw9F4g"><img src="https://img.shields.io/badge/discord-join%20the%20chat-5865F2.svg?logo=discord&logoColor=white" alt="Join the Avalon Discord"></a>
</p>

# Avalon Documentation

This is where you learn Avalon: what it is, why it exists, how it works, how the projects fit together, and how to build on it.

## What is Avalon?

Avalon is an open, self-hostable identity and social layer. A person has one identity, one friends list, and one history of guilds and achievements, and carries them between every game, app, and service that opts in. The identity is a keypair the person holds, not an account any single company controls.

## What problem does it solve?

The internet split into walled gardens: a separate login, friends list, and history for every app and game. Achievements, friendships, and communities are trapped in whichever service's database happens to hold them, and they disappear when that service does.

Avalon moves the durable parts of that (identity, friends, guild membership, verifiable achievements) into a shared layer that outlives any one participant, and leaves everything else with the integrator. A game keeps full control of its own world, characters, economy, and rules. Avalon provides the connective infrastructure between them and no authority over any of them.

Read the full case in [Why Avalon](getting-started/why-avalon.md).

## The ecosystem at a glance

```text
                    Avalon Protocol
        (identity, social graph, guilds, attestations,
         signed transparency log, node network)
                          │
                          ├── SDKs (Rust, C#, TypeScript)
                          │      │
                          │      ├── Hub (web, desktop, mobile)
                          │      ├── Topology Visualizer
                          │      └── Integrating games, apps, services
                          │
                          └── Common UI (shared components for first-party clients)
```

The protocol defines the contracts. The SDKs are generated from and checked against them. Everything else consumes the SDKs. See [the ecosystem map](ecosystem/README.md) for how each project relates to the others.

## Avalon projects

| Repository | Description |
| --- | --- |
| [`avalon-protocol`](https://github.com/avalon-initiative/avalon-protocol) | The protocol and its reference implementation: the node server, signed ledger, indexer, CLI, and conformance vectors. The source of truth for every contract. |
| [`avalon-sdks`](https://github.com/avalon-initiative/avalon-sdks) | Client SDKs for Rust, C#, and TypeScript, released together under one version. What integrators and first-party apps build on. |
| [`avalon-hub`](https://github.com/avalon-initiative/avalon-hub) | The Hub web app and the desktop and mobile app: a person's own doorway to their identity, friends, guilds, and achievements. |
| [`avalon-common-ui`](https://github.com/avalon-initiative/avalon-common-ui) | The shared Vue component library used by Avalon's first-party clients. |
| [`avalon-topology-visualizer`](https://github.com/avalon-initiative/avalon-topology-visualizer) | A developer tool that maps the live network of nodes and how they connect, and traces packets across it. |
| [`avalon-bot`](https://github.com/avalon-initiative/avalon-bot) | The community's Discord bot: turns a Discord message into a GitHub issue. |
| [`avalon-docs`](https://github.com/avalon-initiative/avalon-docs) | This repository: the canonical documentation for the ecosystem. |
| [`.github`](https://github.com/avalon-initiative/.github) | Organization-wide defaults: contribution guidelines, shared labels, and reusable workflows. |

## Where to go next

| I want to... | Start here |
| --- | --- |
| Understand what Avalon is | [Getting started](getting-started/README.md), then [Concepts](getting-started/concepts.md) |
| See how the pieces fit together | [Ecosystem](ecosystem/README.md) and [Architecture](architecture/README.md) |
| Learn how the protocol works | [Protocol](protocol/README.md) |
| Build a game, app, or service on Avalon | [Integrations](integrations/README.md), then [SDKs](sdk/README.md) |
| Run a node | [Running a node](developers/running-a-node.md) |
| Contribute | [Developers](developers/README.md) |
| Understand why something is designed this way | [Architectural decisions](architecture/decisions/README.md) |
| Look up a term | [Glossary](reference/glossary.md) |

## Contents

| Section | What it covers |
| --- | --- |
| [Getting started](getting-started/README.md) | What Avalon is, why it exists, and the core concepts. |
| [Architecture](architecture/README.md) | How the system is shaped: nodes, settlement, synchronization, querying, scaling, recovery. Includes the invariants the design is held to. |
| [Protocol](protocol/README.md) | The concepts and rules: identity, social graph, guilds, attestations, trust, events, security, privacy. |
| [SDKs](sdk/README.md) | How the SDKs relate to the protocol, and the language-agnostic design they share. |
| [Integrations](integrations/README.md) | Building games, apps, and services on Avalon. |
| [Ecosystem](ecosystem/README.md) | Each project in the ecosystem and how it fits. |
| [Developers](developers/README.md) | Contributing, running a node, and how this documentation is maintained. |
| [Architectural decisions](architecture/decisions/README.md) | Numbered records of decisions that shape Avalon as a whole. |
| [Reference](reference/glossary.md) | Glossary and the meaning of the status labels used across these pages. |

## How these docs are organized

This repository explains Avalon as a whole. Each project repository explains how to build, run, and contribute to that project. When a topic belongs in both, the explanation of how Avalon works lives here and the project links to it.

Every page carries a status: Implemented, Partially implemented, Planned, Proposed, Experimental, or Undecided. Planned and proposed work is never described as if it exists. See [status labels](reference/status-vocabulary.md).

## Community

- [GitHub Discussions](https://github.com/orgs/avalon-initiative/discussions) and issues are the durable record for questions, proposals, and decisions.
- [Discord](https://discord.gg/FFDsFw9F4g) is for drop-in conversation.

Corrections and improvements to these pages are welcome as pull requests. See [contributing](developers/contributing.md).

## License

Apache-2.0. See [LICENSE](LICENSE).
