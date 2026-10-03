# ADR-1177: Decide how an account stays usable anywhere when its registering node goes away

**Status:** Accepted — decided 2026-10-02

Original record: [avalon-protocol#1177](https://github.com/avalon-initiative/avalon-protocol/issues/1177). The text below is preserved as recorded; `#N` references are avalon-protocol issue numbers and file paths are as they were when the decision was made. The decision is not built yet; see the implementation state at the end.

## Context

The intended model is that an account has no home: it is accessible from any node, and decommissioning the node it was first registered through must not kill it. A code review of the registration, mirroring, and cross-node login paths found this holds only partly today.

- `register_finish` commits the identity events (`identity.created`, the passkey event, `identity.signing_key_added`) to the registering node's own ledger. A node with no shard override and no remote authority auto-derives a self-certifying `node:<hash>` shard, so that is the default fresh-node case.
- Other nodes mirror `core` and named `game:` shards and project them into their identity tables. `node:` shards are mirrored only when the operator opts in (`AVALON_MIRROR_ALL_DISCOVERED_SHARDS`, off by default) and are then stored as raw mirrored rows but never projected, because "a shard anyone can mint must not create identities".
- Cross-node login resolves the signing key from the shard `core` only (a hard-coded shard in the verified fetch, checked against the pinned core key). An identity whose events are not in `core` and not projected on the destination cannot log in there.
- Result: an account registered on a default node is not visible and not loginable elsewhere, and does not survive that node being decommissioned. An account registered on the `core` author, or on a named shard that others mirror, does survive and log in elsewhere.
- Passkeys are never portable: the WebAuthn credential is held in the node's own table under its relying-party id, and the only cross-node credential is a device-held signing key.
- The documentation promises more than this in places (an identity has no home node; identity events go to `core`).

## Decision

Option A: any node accepts and projects verified, self-authenticating identity events from any shard it mirrors, and cross-node login resolves an identity's entries from the shard they live in, verified against that shard's own key and the identity's signature chain. Option B (route identity events to `core`) is rejected: it makes `core` a registry and a single point of failure for accounts. Option C (keep today's behavior and document it) is rejected: accounts on a default node would stay tied to it. Passkey portability is a separate decision (#1183). Tracked in the epic #1178.

## Why

With self-certifying identity ids and signature verification at projection time (#1129, #1130), an identity event proves itself: it is signed by the key the id is derived from, and a hostile shard cannot forge another identity. The original reason `node:` shards are not projected (anyone can mint a shard, so it must not create identities) then only concerns spam, not forgery, and per-source caps can bound it.

## Alternatives considered

- Project verified identity events from any shard, with per-source and per-shard caps and rate limits, and have cross-node login resolve identity entries from the shard the locator points to, verified against that shard's own key (a `node:` shard's key is derived from its id) and the identity's signature chain, instead of `core` only. Decentralized, no registry; needs mirroring of identity-bearing shards to be on by default for seed and mirror nodes.
- Route all identity events to `core` (what the documentation describes). Portable by construction but makes `core` a registry and a single point of write authority, and does not suit a node that authors its own shard.
- Keep the current behavior and say so in the documentation. Accounts on default nodes stay tied to their node.

## Consequences

Touches mirror projection rules, mirroring defaults, cross-node login and the identity locator, and the replication gate that guards single-node loss. The passkey half needs its own decision (a shared relying-party id, or login through the device-held signing key only). Related to the display-name conflict rule across shards and to recovery.

## Implementation state

This section is not part of the recorded decision. The work is tracked in the epic [avalon-protocol#1178](https://github.com/avalon-initiative/avalon-protocol/issues/1178), whose slices (#1179 to #1182) and the passkey decision (#1183) were open when this page was written. Until they land, the behavior in the context above is what the code does; see [nodes](../nodes/README.md#identity-and-social-actions-and-shards) and [cross-node login](../nodes/cross-node-login.md).

## Related

#1129, #1130, #1125, #1137, #1178, #1183, [ADR 0786](0786-on-demand-cross-node-identity-data-resolution.md).
