# Network environments

**Status:** Partially implemented — the local, dev, int and prod tiers are in use and named in the trust-anchor list; the staging tier is proposed.

Avalon runs more than one network for itself so a change can be proven on something disposable before it reaches the network people rely on. Each tier has a purpose, a naming convention and a rule about whether it may be wiped. This page explains the tiers; the procedure for operating them is a maintainer runbook in the protocol repository.

## The tiers

| Tier | `network_id` | Purpose | May it be wiped? |
| --- | --- | --- | --- |
| Local | `avalon-dev-local` | One developer's machine. A template entry whose key belongs to no real server. | Yes, always. |
| Dev | `avalon-dev-<name>` | A real non-production deployment, one to a few nodes, for trying changes. | Yes, while it is being worked. |
| Int | `avalon-int-<name>` | A 1 to 5 node interconnected test bed that verifies a change integrates across nodes before it ships. | Yes, on a regular cadence. Rebuilding it from nothing is itself the proof that the network can be stood up from scratch. |
| Staging | `avalon-staging-<name>` (**Proposed**) | Volume testing at a realistic node count and data volume. | Between runs. |
| Prod | `avalon-mainnet-N` | The one canonical public network. | Never. A move to `N+1` is a deliberate, rare migration that carries the final checkpoint forward. |

The `environment` field of a trust-anchor entry records the tier. It currently documents `local-dev`, `dev`, `int` and `prod`; the Hub calls out every entry that is not `prod`. Staging is not yet a listed value, and tooling for volume testing a deployed network does not exist yet.

## Rules that hold for every tier

- Tiers never share hosts or databases, and a test never runs against a shared database.
- A `network_id` is never reused for a different network.
- A network's key is its identity: a node refuses to start under a different `network_id` than its database was created with.
- Changing the published list of networks is a reviewed change, never a runtime action.

## Prod

There is exactly one canonical mainnet at a time. Its protections are layered: reviewed changes to the list, protected branches, tag-only releases, and a documented key ceremony and custody (planned). A code-level guard against destructive commands on a production database does not exist yet, so the runbook states the rules explicitly.

## Where the procedure lives

Creating and retiring a network, adding it to the trust-anchor list, and the prod checklist are in the [environments runbook](https://github.com/avalon-initiative/avalon-protocol/blob/main/docs/maintainers/environments.md). Running a network that is not part of Avalon's own list is in [running your own network](../developers/running-your-own-network.md).

## Related

- [Network trust anchors](../protocol/network-trust-anchors.md)
- [Running your own network](../developers/running-your-own-network.md)
- [Self-hosting](self-hosting.md)
- [Disaster recovery](disaster-recovery.md)
