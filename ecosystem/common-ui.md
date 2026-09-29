# avalon-common-ui

**Status:** Implemented — published as `@avalon-initiative/common-ui` (0.1.1 at time of writing).

`avalon-common-ui` is the shared Vue 3 component library for Avalon's first-party clients. It holds presentation only: no network calls and no protocol logic. Components take data through props and report intent through events.

## How it fits

It is a leaf of the dependency map. The [Hub](hub.md) and the [topology visualizer](topology.md) use it so the first-party clients look and behave alike, and it knows nothing about storage, the protocol, or the SDKs. Styling comes from shared design tokens, and components are developed and documented in Storybook. Because it carries no protocol logic, a change to a contract never lands here first.

## Where to read more

- [avalon-common-ui repository](https://github.com/avalon-initiative/avalon-common-ui) for install (a GitHub Packages token with `read:packages` is needed), usage, and conventions.

## Related

- [Ecosystem map](README.md)
- [Hub](hub.md)
- [Topology visualizer](topology.md)
