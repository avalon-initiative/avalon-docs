# Documentation guide

**Status:** Implemented — describes how this repository is organized and maintained.

This repository is the canonical knowledge base for the Avalon ecosystem: what Avalon is, why it exists, how it works, how the projects relate, and how to integrate. This guide explains its philosophy, layout, page conventions, and where a given piece of documentation belongs.

## Philosophy

- **Explain the whole, not each part.** Project repositories answer how to build, run, and contribute to that project. This repository answers what Avalon is and how it fits together. A topic that belongs in both is explained here and linked from the project.
- **Honest status.** Every page says what state it describes. Planned or proposed functionality is never written as if it exists, and pages are checked against the code, not against older documents.
- **Decisions are recorded once.** Architectural decisions live in [architectural decisions](../architecture/decisions/README.md). Pages link to the decision instead of re-arguing it, and describe the current model when a decision has been superseded.
- **Plain Markdown.** No site generator; pages read the same on GitHub and locally.
- **Precise language.** Technical, no marketing tone. Avalon is described as a signed, append-only transparency log, not a blockchain or token. Games are one kind of integrator, not the only kind.

## Layout

| Directory | Holds |
| --- | --- |
| `getting-started/` | What Avalon is, why, concepts, and user-facing overview. |
| `architecture/` | How the system is shaped, plus `decisions/` for numbered records. |
| `protocol/` | Concepts and rules: identity, social graph, guilds, attestations, trust, events, security, privacy. |
| `sdk/` | How SDKs relate to the protocol and the design they share. |
| `integrations/` | Building games, apps, and services on Avalon. |
| `ecosystem/` | Each project and how it fits. |
| `developers/` | Learning path, contributing, running a node, this guide. |
| `reference/` | Glossary and status vocabulary. |

## Page conventions

- One `# Title`, then directly beneath it a status line: `**Status:** <value>`, optionally followed by ` — ` and a short qualifier.
- A one to three sentence introduction that stands alone, since a reader may arrive from a search.
- Define a term before using it or link to the [glossary](../reference/glossary.md).
- Short, focused pages. Split a page that covers more than one idea, and keep an index page at the original topic name.
- A `## Related` list at the bottom, using relative links.
- Diagrams only where they materially help; small ASCII or Mermaid.

## Status markers

| Status | Meaning |
| --- | --- |
| Implemented | Exists in the code and behaves as described. |
| Partially implemented | Some of it exists; the page labels which parts. |
| Planned | Committed direction, not built. |
| Proposed | A design under consideration, not committed. |
| Experimental | Exists but may change or be removed. |
| Undecided | An open question, deliberately not resolved. |
| Reference | A stable lookup page (glossary, vocabularies). |

Decision records additionally use Accepted and Superseded. The full definitions are in [status vocabulary](../reference/status-vocabulary.md). Where a page mixes states, mark it by its main state and label the exceptions in a heading or the first sentence, for example "Planned:".

## Where documentation belongs

| Content | Lives in |
| --- | --- |
| What Avalon is, concepts, protocol rules, architecture, decisions | This repository |
| Build, run, test, and release steps for one project | That project's repository |
| Per-language SDK install and code samples | [avalon-sdks](https://github.com/avalon-initiative/avalon-sdks) |
| Node hosting and operations steps | [avalon-protocol](https://github.com/avalon-initiative/avalon-protocol) |
| Contract definitions (OpenAPI, conformance vectors) | [avalon-protocol](https://github.com/avalon-initiative/avalon-protocol); see [protocol API](../protocol/api.md) |
| Crate, module, environment variable, and make-target detail | The implementing repository, linked from a short "Implementation" section here |

Keep implementation detail out of concept pages. When one is needed, state its status and link to the code or docs that own it.

## Checking your changes

Run `make check` from the repository root. It verifies that relative links resolve, heading anchors exist, and every page under a content directory has a valid status line. Links to other repositories use absolute GitHub URLs.

## Related

- [Contributing](contributing.md)
- [Status vocabulary](../reference/status-vocabulary.md)
- [Glossary](../reference/glossary.md)
- [Developers](README.md)
