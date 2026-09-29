# Contributing

**Status:** Implemented — summarizes the organization's current workflow; the authoritative text is the organization's contributing file.

Contributions to Avalon repositories follow one organization-wide workflow, defined in the [.github repository's CONTRIBUTING file](https://github.com/avalon-initiative/.github/blob/main/CONTRIBUTING.md). A repository may override it with its own file. This page summarizes the workflow so the shape is clear before you open a pull request; where the two differ, the linked file wins.

Opening a pull request makes you part of the Avalon Initiative rather than an outside contributor to someone else's project. The standard is the one every operator and integrator on the network is held to.

## Where to start

- **Questions and design discussion:** open an issue or an [organization Discussion](https://github.com/orgs/avalon-initiative/discussions). Issues and Discussions are the durable record. [Discord](https://discord.gg/FFDsFw9F4g) is for informal chat and is not a record; move anything worth keeping into an issue or Discussion.
- **Which repository:** see the [ecosystem map](../ecosystem/README.md). The protocol, server, and design decisions live in `avalon-protocol`; documentation in this repository.
- **Build and test commands:** each repository documents its own in its README or contributing file.

## Workflow in brief

- **Issues track work.** Open an issue first when the work is non-trivial. Comment `/claim` on an issue before starting; a bot assigns it. Claim a specific sub-issue rather than an epic. Quiet claims are pinged and eventually unassigned.
- **Branches** are named `<issue#>-short-description` off `main`.
- **Pull request titles** use `[#<issue>] - <short description>`. Merges are squash-only, so the title is what lands on `main`. A CI check verifies the PR closes an issue the author is assigned to.
- **Restricted markers:** `[noissue]`, `[hotfix]`, and `[security]` are reserved for maintainers and a named set of trusted developers.
- **Do not bypass a convention silently.** If a rule gets in the way, open an issue to discuss it.
- **Do not suppress lint or format rules to make a check pass.** Fix the code, or question the rule.

## Design principles a change is checked against

Proposals are checked against the project's guiding principles, principally whether a change keeps integrators sovereign over their own worlds while giving Avalon only connective infrastructure. See [what is Avalon](../getting-started/what-is-avalon.md#guiding-principles) and the [architecture map](../architecture/README.md).

## Cross-repository changes

- The repository that implements a capability owns it. A consumer that needs a protocol capability requests it in the protocol repository first.
- Contract changes (signing bytes, tree-head format, trust anchors, OpenAPI) update the protocol repository and the SDK conformance vectors together, then consumers.
- All three SDKs share one version and one release.
- Tags, package publication, and pushes to protected branches are deliberate, outward-facing steps.

## Documentation changes

Follow the [documentation guide](documentation-guide.md).

## Conduct and security

- [Code of Conduct](https://github.com/avalon-initiative/.github/blob/main/CODE_OF_CONDUCT.md)
- [Security policy](https://github.com/avalon-initiative/.github/blob/main/SECURITY.md)

## Related

- [Developers](README.md)
- [Documentation guide](documentation-guide.md)
- [Ecosystem](../ecosystem/README.md)
