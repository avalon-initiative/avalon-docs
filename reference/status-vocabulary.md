# Status Vocabulary

**Status:** Reference

Every page in this repository carries a `**Status:**` line directly under its title. The value says how much of what the page describes exists today, so a reader can tell a shipped mechanism from a design that has not been built. This page defines each value.

## Values

| Status | Meaning |
| --- | --- |
| Implemented | The behavior described exists in the implementing repository's main branch and has been checked against the code. Known gaps are called out inside the page, not hidden. |
| Partially implemented | Some of the described behavior exists and some does not. The page labels each section that is not built (for example "Planned:" in a heading or first sentence). |
| Planned | A decision has been made to build this, but the behavior does not exist yet. The page describes the intended shape. |
| Proposed | A design has been written down and is under consideration, but it has not been decided. It may change or be dropped. |
| Experimental | Built, but expected to change or be removed, or not yet proven beyond a prototype. Do not build an integration that depends on its stability. |
| Undecided | A question the project has deliberately left open. The page records the options and the constraints, not an answer. |
| Reference | A stable lookup page (glossary, vocabulary, index) that describes no feature and so has no implementation state. |
| Accepted | Architecture decision records only. The decision is in force. |
| Superseded | Architecture decision records only. A later decision replaced this one, wholly or in part. The record is kept for history. |

## Rules

- The status describes the page's main subject. Where a page mixes states, the page takes its main state and each exception is labeled in the text. A page that is mostly implemented but contains a planned extension is `Implemented` with a "Planned:" section, not `Partially implemented`, unless the missing part is significant to the topic.
- Planned and proposed functionality is never described in the present tense as if it exists.
- Optional trailing text is allowed after ` — ` (for example `**Status:** Partially implemented — direct and relayed connectivity only`).
- Statuses are checked against the code when a page is written or changed. A page whose status has drifted is a bug in the page.
- Status is about the documented mechanism, not about a release. A mechanism can be `Implemented` in the protocol repository and not yet exposed by every SDK; the page says so.

## Related

- [Documentation guide](../developers/documentation-guide.md)
- [Glossary](glossary.md)
- [Architecture decisions](../architecture/decisions/0186-no-blockchain-validator-consensus-transparency-log-only.md) (an example of an `Accepted` record)
