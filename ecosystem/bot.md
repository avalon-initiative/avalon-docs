# avalon-bot

**Status:** Implemented — for its current scope, Discord to GitHub; an Avalon integration is Planned and not built.

`avalon-bot` is the Avalon community's Discord bot. Today it does one thing: turn a Discord message into a GitHub issue without leaving Discord, and link the issue back to the discussion. It uses no AI, keeps no database, and files nothing without an explicit submit.

## How it fits

The bot is a community tool and is currently independent of the protocol and SDKs. It supports the project's practice of keeping durable decisions in issues and Discussions instead of chat: an idea raised in Discord is moved into an issue. It can also promote a decision issue into an architecture-decision-record format, following the record shape used in [architectural decisions](../architecture/decisions/README.md).

Its Avalon integration is a later goal: an integrator like any other, using an SDK and the capability model. That is not built, and no page here should be read as saying it is. See [apps and services](../integrations/apps-and-services.md) for how a non-game integrator would fit.

## Where to read more

- [avalon-bot repository](https://github.com/avalon-initiative/avalon-bot) and its [setup guide](https://github.com/avalon-initiative/avalon-bot/blob/main/docs/setup.md).

## Related

- [Ecosystem map](README.md)
- [Contributing](../developers/contributing.md)
- [Apps and services](../integrations/apps-and-services.md)
