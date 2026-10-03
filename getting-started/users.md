# For users

**Status:** Implemented — the Hub is the one user-facing product today; other surfaces are covered by the integrating apps themselves.

This page is for people who use games, apps, or services that integrate Avalon, and for people evaluating Avalon from the outside. It explains what a user gets and controls, and points to the guide for the Hub, the first-party client.

## What an Avalon identity gives you

- One identity that is a keypair you hold, not an account a company owns. It carries no name, government ID, or biometric.
- Login with a passkey, the same mechanism your phone or browser uses for Face ID, a fingerprint, or a PIN. There are no passwords.
- Recovery if you lose every device: a small group of guardians you choose can approve recovery, and no one holds a master key.
- A friends list, guild memberships, and earned achievements that follow you between integrators.

## What you control

- **Grants.** An integrator sees only the capabilities you grant it, such as reading your friends or issuing an achievement. You can revoke a grant at any time.
- **Visibility.** Presence and guild rosters are scoped by your own visibility settings; anyone outside the scope reads as offline. These settings control what a node's API returns. Friend and guild-membership events are committed to the public ledger with their details and cannot be hidden or removed there; see [privacy](../protocol/privacy.md#what-the-ledger-makes-public).
- **Blocks.** A block is never revealed to the person who was blocked.

Technical detail: [bindings](../protocol/bindings.md), [privacy](../protocol/privacy.md), [social graph](../protocol/social-graph.md).

## Where to manage it

The Hub is a web app and a desktop and mobile app where you manage identity, devices, guardians, friends, guilds, achievements, and which integrators can see what, without any game open. The step-by-step guide lives with the Hub: [Using the Hub](https://github.com/avalon-initiative/avalon-hub/blob/main/docs/hub/for-users.md). See also [the Hub in the ecosystem](../ecosystem/hub.md).

## If you are evaluating Avalon

Read in this order:

1. [Why Avalon](why-avalon.md): the problem and the gap.
2. [What is Avalon?](what-is-avalon.md): the system in one page.
3. [Design proposal](../architecture/design-proposal.md): the full product overview, including current limitations, known challenges, and open questions.
4. [Architecture map](../architecture/README.md): the invariants the design is held to.

## Related

- [Concepts](concepts.md)
- [Glossary](../reference/glossary.md)
- [Integrations](../integrations/README.md)
