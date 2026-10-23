# ADR-1154: Decision: emergency upgrade path for a fix that cannot wait for the activation window

**Status:** Accepted — decided 2026-10-05

Original record: [avalon-protocol#1154](https://github.com/avalon-initiative/avalon-protocol/issues/1154). The text below is preserved as recorded; `#N` references are avalon-protocol issue numbers and file paths are as they were when the decision was made.

## Context

A security fix may need to take effect faster than the normal notice window. Decide what is allowed: a shortened window, who can authorize it, how it is signed and announced, what happens to nodes that miss it, and how it is logged so it is auditable. The path must not become a way for one key to rewrite validity.

## Decision

An emergency fix is an ordinary release that skips only the 30-day minimum gap of #1152; there is still no activation key, and adopting it means installing it. It is signed by the normal release signing threshold or a higher one (#1295) and carries a signed advisory with a severity, the findings in plain words and a link to the public decision record; there is no single-key override. It may tighten validation for new events and ship quarantine hints that each node applies as local policy; it may not loosen validity or retroactively invalidate events already accepted, and affected owners remediate through normal signed events. Manifests and advisories go in an append-only public release log that every node checks independently (#1326). Auto-update is a per-category choice (emergency, security and normal releases set independently, or never or all): by default emergency and security releases auto-apply and normal releases stay manual, and an operator can opt in or out fully or partially (#1327). Apply is safe: the previous binary is kept, migrations run in a transaction, the new binary is health-checked and rolled back automatically on failure, which works because the previous binary keeps running on the new schema (#1158). A node that does not update stays visibly behind: it gets an upgrade-required signal and peers on newer rules drop it with an explicit reason until it updates, then catches up from peers (#1152, #1161). Every automatic update is announced loudly and recorded: a notice file in the node's data directory with what changed, why and where the decision is recorded, an /info banner, a log line and a local update history (#1328). Transparency about updates is a requirement, not an option.

## Alternatives considered

- No emergency path: the normal window applies to everything. Safe but may leave a known flaw live.
- Single maintainer key can force activation. Rejected as a single point of control.

## Consequences

## Related

Part of the network upgrade epic (#1150).
