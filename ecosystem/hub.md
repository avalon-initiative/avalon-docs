# avalon-hub

**Status:** Partially implemented — the web app is implemented; the desktop and mobile app is a smaller slice of it.

The Hub is Avalon's first-party client: a place where a person manages their identity, friends, guilds, achievements, and connected integrators with no game or app open. It is a client of the network like any other, with no backend of its own and no privilege a third-party client could not have ([ADR 0077](../architecture/decisions/0077-the-hub-is-a-client-of-the-network-not.md)).

## What it is

`avalon-hub` is one npm workspace with two apps:

- **Web app** (`apps/hub`, Vue 3, Vite, TypeScript). Implemented: identity setup (passkeys, devices, guardian recovery), friends, blocks, presence, discovery, guilds (roles, channels, chat, events), achievements, messages, integrator discovery, and per-integrator connections and grants.
- **Desktop and mobile app** (`apps/hub-app`, a Tauri shell around the same UI). Partially implemented: login, identity creation, cross-node login, home, and settings exist; guild, friends, and chat views are not built.

## How it fits

The Hub sits at the client edge. It reaches the network only through the published TypeScript SDK and shares presentation with other first-party clients through [common UI](common-ui.md). It is the reference consumer of the SDKs: whatever it needs that the server lacks becomes a protocol request first, and it has no Hub-only endpoints. It is not a launcher, store, or authority over integrators, and it shows every authentic, valid claim with its provenance without ranking issuers. A person who never installs any Hub client loses nothing at the protocol level.

For the person-facing guide see [users](../getting-started/users.md).

## Where to read more

- [avalon-hub repository](https://github.com/avalon-initiative/avalon-hub)
- [Hub docs](https://github.com/avalon-initiative/avalon-hub/blob/main/docs/hub/README.md) and [Hub app docs](https://github.com/avalon-initiative/avalon-hub/blob/main/docs/hub-app/README.md)
- [Using the Hub](https://github.com/avalon-initiative/avalon-hub/blob/main/docs/hub/for-users.md)

## Related

- [Ecosystem map](README.md)
- [SDKs](sdks.md)
- [Common UI](common-ui.md)
- [Bindings](../protocol/bindings.md)
