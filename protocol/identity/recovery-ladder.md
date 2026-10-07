# The Recovery Ladder

**Status:** Partially implemented — device pairing and the mnemonic fallback exist; guardian recovery restores a passkey only, and the version that authorizes a new signing key is planned.

An identity is its signing key, and nobody holds a copy of it for the person. This page lays out, in order, what a person can fall back on when they lose a device or every device, what each step needs, and what happens when the ladder runs out. The mechanics of the guardian steps are on [recovery and rollback](./recovery.md); key custody is on [authentication and signing keys](./authentication.md). It is part of [identity](../identity.md).

## The ladder

Each rung is used only when the one above it is unavailable.

| Step | Needs | Protects against | Status |
| --- | --- | --- | --- |
| 1. Another registered device | Any other device that still holds an active key approves the new one ([device pairing](./authentication.md#cross-device-pairing-for-clients-without-webauthn)) | Losing or replacing one device | Implemented |
| 2. The mnemonic | The recovery phrase written down at registration; any device derives the same signing key from it offline | Losing every device while keeping the phrase | Implemented in the reference web client; mnemonic-derived keys are not in every SDK ([language support](../../sdk/language-support.md)) |
| 3. Guardian recovery | M of N guardians approve, then a mandatory public delay passes with no veto | Losing every device and the phrase | Partially implemented: restores a passkey only. Planned: one atomic `identity.recovered` v2 carrying the new signing key and the guardian approvals ([ADR 1135](../../architecture/decisions/1135-recovery-authorises-a-new-signing-key-with-guardian-signatures.md)) |
| 4. Nothing | Nothing remains | Nothing | The identity cannot be recovered |

A successful recovery revokes every prior key and passkey of the identity, so whoever held a credential before it is locked out. A stolen key cannot be kept alive by recovering around it.

## Total key loss is final

An identity with no remaining key, no guardians and no mnemonic cannot be recovered. The person creates a new identity. No node, operator or Avalon maintainer can look the identity up and reissue it, and the id (a hash of the first key) cannot be reassigned.

A node-attested reset, where a node operator or the network vouches that "this is really the same person" after a delay, is deliberately not offered. It would be a special authority that can take over any identity, which is the central point of trust the design exists to remove. The cost of that choice is exactly this rule, and it is accepted knowingly.

## What to tell users at onboarding

The Hub prompts a new user to write down the mnemonic or choose guardians before relying on the identity. Integrators that create identities for their users (or send them to create one) should say the same things, plainly and before the first sign-in:

- Avalon has no "forgot my password" flow. Nobody can reset the identity for them.
- They should keep at least one of: a second device, the written-down mnemonic, or guardians they trust.
- The mnemonic is a bearer secret: anyone who has it controls the identity. It belongs offline, not in a screenshot or a cloud note.
- Guardians are named on the public ledger (see [guardian ids are public](./recovery.md#social-recovery-via-m-of-n-guardians)).
- If everything is lost, they start over with a new identity and their friends, guilds and history under the old one do not move.

An integrator never holds an identity's key and cannot recover it either; point users at the Hub's setup and recovery screens rather than building a custom reset.

## Related

- [Recovery and rollback](./recovery.md), [authentication and signing keys](./authentication.md), [identity](../identity.md)
- [Building an integration](../../integrations/building-an-integration.md), [security model](../security-model.md)
