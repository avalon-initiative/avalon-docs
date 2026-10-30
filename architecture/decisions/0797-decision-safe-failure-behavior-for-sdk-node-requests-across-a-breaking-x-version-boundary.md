# ADR-0797: Decision: safe failure behavior for SDK<->node requests across a breaking (X) version boundary

**Status:** Accepted — decided 2026-10-05

Original record: [avalon-protocol#797](https://github.com/avalon-initiative/avalon-protocol/issues/797). The text below is preserved as recorded; `#N` references are avalon-protocol issue numbers and file paths are as they were when the decision was made. The recorded release-process path is shown as code rather than a relative link.

## Context

Two failure modes exist when a network isn't uniformly on the same
release:

- **A node upgrades to an `X` release before some connected SDK clients
  do.** If an SDK's request assumed the old wire format, what actually
  happens — silently accepted-but-misinterpreted (the real risk worth
  worrying about: data quietly dropped or corrupted), or cleanly rejected?
- **An SDK client upgrades to a new `X` release before the node it talks
  to has.** The symmetric risk in the other direction.

This is a non-issue by design when both sides are on the same release, or
when the release is `Y`/`Z` —
`docs/projects/backend-server/for-maintainers/release-process.md`'s
semver policy already requires those to stay wire-compatible with the
previous version, generalizing the additive-only direction #308 (closed,
decided) already established for the wire/API surface. This issue is
scoped specifically to the case that policy exists to make rare: an actual
`X` bump.

Nothing enforces safety here today. There is **no SDK-to-node version
reporting or negotiation at all** — the existing `protocol_version`
machinery (#368) is node-to-node only (`crates/server/src/nodes.rs`,
`mirror_watcher.rs`, `dht.rs`); ordinary API routes an SDK calls
(identity, friends, guilds, achievements) carry no version field in
either direction. #91 (open) covers *choosing* which node to connect to
in the first place, not what happens to an already-established connection
whose client ends up behind or ahead of the node it's talking to.

## Decision

Every request carries the rules version (`rules_version`, #1152) and the node checks it on every request: in the body for writes (inside the signed bytes for signed objects) and in a header or query parameter for reads, which have no body. A node rejects a version it does not support with a typed error naming the supported range and never accepts a request it cannot handle correctly (#1325, with the typed error from #1309). `/info` and announce state `rules_supported` and `rules_emitting` so a client can detect a mismatch on connect (#1155). The SDKs send the version automatically, read the node's range and surface typed too-old and too-new errors (avalon-sdks #113). A node does not rebroadcast an unsigned claim that a newer version exists, because a node's self-reported version is never authoritative (#308); nodes find out through the opt-in check against the real release feed (#795), each independently.

## Why

The actual harm here isn't "a request returns an error" — a clean
rejection is a good outcome: loud, visible, and fixable. The harm to
prevent is a request **silently succeeding while being misinterpreted**
across an incompatible version boundary — the concrete "data gets
dropped" risk. A clean, typed rejection is strictly safer than either side
guessing, and per #308's invariant, a version claim already can't be
trusted enough to build automatic remediation on top of (see question 2)
— so the only safe automated response to a version mismatch is "refuse
and say why," never "route around it" or "trust the rumor and update."

## Alternatives considered

- **Silent best-effort compatibility shims** (server tries to accept an
  old-shape request and translate it) — rejected: this is exactly the
  additive-only policy #308 already decided against relying on past an
  `X` boundary; a real `X` bump means the old shape genuinely can't be
  serviced correctly, and pretending otherwise is how data quietly gets
  dropped.
- **Capability-based request forwarding** (Option E in #308, already
  explicitly deferred there for its own trust-hop problem) — not
  revisited here, same reasoning applies.
- **Unsigned peer-to-peer version rumor propagation** ("blast to the
  network") — see Decision above; rejected pending #619's signed release
  channel, at which point this becomes safe to reconsider as a real
  rollout-staggering mechanism (which is what #619's own Motivation
  already describes).

## Consequences

- If question 1 is decided yes: `sdk`/`bindings/*` need a wire-level
  version field on requests (new infrastructure across every official
  SDK, not just the server), and every route needs to define which
  client version range it accepts — real design and implementation work,
  not a small addition.
- An `X` release's advance-announcement requirement (already called out
  informally in `release-process.md`'s `X` bullet — "announced ahead of
  the tag going out where possible") should become a hard requirement
  once this is decided, specifically so an integrator developer — who has
  no way to auto-update their own code, only a human choosing to bump a
  dependency — gets real lead time before their existing client starts
  hitting the new clean-rejection behavior instead of quietly corrupting
  data the moment an `X` release ships.
- Directly informs #619 (opt-in auto-update): a hoster's node
  auto-updating without any of this in place is *more* dangerous, not
  less — an auto-updated node with SDK clients still on the old version
  has exactly the "node ahead of SDK" problem above, just triggered
  automatically instead of by a manual upgrade decision.

## Related

#308 (the decision this operationalizes, especially its cross-cutting
invariant and Option C), #368 (existing node-to-node version awareness
this extends to SDK-to-node), #91 (node *discovery*, a related but
distinct SDK/node version concern), #795 (the opt-in update-check this
recommends instead of unsigned rebroadcast), #619 (opt-in auto-update —
this issue's outcome should gate how safe that epic actually is to build)
