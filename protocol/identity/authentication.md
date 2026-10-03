# Authentication and Signing Keys

**Status:** Implemented — with two labeled limits: hybrid-transport login is configuration-verified only, and mnemonic-derived signing keys are stored unencrypted in the reference web client.

An Avalon identity is a self-custodied pair of keys, each with a different job, and no password or shared secret exists anywhere. This page describes how an identity logs in, how it authors signed events, which actions need a fresh signature on top of a session, and how a client with no browser or a client talking to a different node gets a session. It is part of [identity](../identity.md).

## Two keys, two jobs

The design follows how passkey-based wallets are built: the passkey is a secure unlock, and a separate key is the actual signer. WebAuthn's challenge is deliberately not a general-purpose signing oracle, so one key cannot do both jobs.

| Key | Proves | Used for |
| --- | --- | --- |
| WebAuthn passkey | interactive presence: "the holder of this device authorized this request, right now" | the entire login mechanism |
| Ed25519 signing key | authorship of a specific durable event | signing `identity.created`, approving new device keys, revoking keys, fresh signatures (below) |

- **Passkeys.** Multiple passkeys per identity are supported. Any registered passkey authenticates the identity, none is privileged, and each can be named and revoked independently. Registering or revoking one emits a durable `identity.passkey_registered` or `identity.passkey_revoked` event carrying only public credential material, so a node that only mirrored the identity's history can verify a fresh login for it. Revoking the last remaining passkey requires explicit confirmation.
- **Signing key.** The identity's first signing key (the inception key) signs `identity.created`, and the identity id is derived from that key (see [the identity id](../identity.md#the-identity-id)). The event's issuer is `identity:<id>:self:created`, not a node. A hosted node therefore cannot fabricate an identity that never registered, the same guarantee that stops a node fabricating an integrator's attestation (see [security model](../security-model.md)). Later keys are added by device grant and never change the id. Losing one device's key while another active key exists is recoverable: the other device approves a replacement. Losing every signing key is not: the passkey still logs in, but a new signing key can only be authorized by an active one, and recovery restores a passkey and not a signing key (see [recovery](./recovery.md#recovery-restores-a-passkey-not-a-signing-key)).

Login is identity-id-first, not fully usernameless (the identity id is the 64-character hex id, and the WebAuthn user handle is its first 16 bytes). True discoverable-credential login would need attested resident keys, a heavier registration path that is not built. The property that matters still holds: no shared secret, and a real challenge-response proof every time.

## Two authorization tiers

Most account actions (reads, chat, presence, profile edits, ordinary guild membership churn, reversible social-graph edits) are authorized by the session's bearer token alone. Actions with real blast radius or that are hard to reverse additionally require a fresh Ed25519 signature from the identity's own signing key at the moment of the action. A stolen session token alone is not sufficient for that second tier.

Actions in the fresh-signature tier:

- approving a device-pairing request, or a device-signing-key grant
- revoking the last remaining passkey
- removing a recovery guardian or raising the recovery threshold
- connecting to an integrator (granting it standing capabilities)
- creating, updating, or deleting a guild role or permission override
- transferring guild ownership or changing another member's role
- reversing an event through [post-compromise rollback](./recovery.md#post-compromise-rollback)

A signature-required request carries `signing_key_id` (one of the caller's own non-revoked signing keys) and a base64 `signature`. The server rebuilds the exact byte string the key must have signed and verifies against it; a client never supplies pre-computed "valid" bytes. The message is `avalon:<action_tag>:v1:<field1>:<field2>:...`, a short versioned action tag followed by the action's own load-bearing fields in a fixed order, so a signature minted for one action or target cannot verify against another. Failures are `NO_REGISTERED_SIGNING_KEY`, `FRESH_SIGNATURE_REQUIRED`, `SIGNING_KEY_NOT_FOUND`, and `INVALID_FRESH_SIGNATURE`.

Every first-party client mints these signatures automatically. This tier does not let an integrator credential escalate into account-level power; integrator sessions and account sessions are separate types in every SDK.

## Cross-device pairing for clients without WebAuthn

A game engine with no embedded browser, a console, or any headless client has no WebAuthn surface and does not need one, because SDKs take a bearer session token rather than performing a ceremony. Pairing solves how such a client obtains the token, the same way platform account systems do:

1. The incapable client requests a pairing (`POST /auth/device/start`, unauthenticated) and receives a short human-typeable `user_code` (shown to the user, for example as a QR code) plus an opaque `device_code` only it holds.
2. The user completes a real WebAuthn login on a capable device and approves the pairing there (`POST /auth/device/approve`).
3. The waiting client polls (`POST /auth/device/poll`) until it receives an ordinary session token, minted by the same mechanism as a normal login.

The security boundary is not the secrecy of the `user_code`. Approval requires the approver's own already-authenticated session, so there is no path from knowing the code to a minted session. The code still has real entropy, a roughly 10-minute expiry, and single-use delivery (an approved token is returned exactly once).

This is a different problem from adding a trusted signing device to an identity that is already authenticated somewhere. That uses a device-key grant: an already-trusted device approves a new device's public key by signing `avalon:device_grant.approved:v2:{grant_id}:{identity_id}:{requested_public_key_hex}`, the server verifies it against the approver's active key, and a grant only ever authorizes a public key and never transfers a private one. The requested key must be an acceptable Ed25519 key (canonical and not of small order). The resulting `identity.signing_key_added` event carries the grant id and the approval signature.

Revoking a signing key also needs a signature. An authenticated session for the identity names one of its active keys (`revoked_by_signing_key_id`, which may be the key being revoked) and supplies that key's signature over `avalon:identity.signing_key_revoked:v2:{identity_id}:{signing_key_id}:{revoked_by_signing_key_id}`. The last active key cannot be revoked (409 `LAST_SIGNING_KEY`), because recovery cannot add a signing key and the identity would be locked out. Both operations return 409 `IDENTITY_CHAIN_FORKED` while the identity is forked. The server checks these signatures at write time; mirroring nodes do not yet verify them when projecting (see [the identity page](../identity.md#what-is-not-built-yet)).

## Hybrid transport

WebAuthn's hybrid transport (a browser shows a QR code and a nearby phone unlocks its own passkey over Bluetooth) is a built-in browser and OS feature. Avalon neither implements nor disables it: the server sets no authenticator-attachment restriction or transport hint. This was verified at the configuration level and by a register-then-login round trip through a generic virtual authenticator. **An end-to-end hybrid ceremony with a real phone has not been run**; that would need a real browser and device. The SDK never sees any of this, since an integrator only exchanges an already-issued session token.

## Where the signing key lives

The reference web client derives the signing key from a freshly generated BIP39 mnemonic during registration and shows the mnemonic once, never storing it. Any device with the phrase can re-derive the identical key offline; the server only ever sees the public key. The derivation is a hash of the BIP39 seed with a versioned domain-separation label, not a hierarchical derivation, since there is one signing key per device rather than a tree. Test vectors are in `conformance/vectors/bip39-mnemonic.json`.

The primary path is the device-grant model above, with no phrase in the common case: each device holds its own key. **Limit:** the reference web client stores the derived secret key in unencrypted browser `localStorage`, keyed by identity id, with the same exposure as any other script-readable value on that origin. The passkey has no equivalent decision, since it never leaves the platform authenticator. Granting a signing key never authenticates a login by itself.

## Session continuation across nodes

An opaque bearer token is node-local: it is minted by the node that ran the WebAuthn login and checked only against that node's session table. If that node goes offline, the token is dead even though other nodes mirror the identity's history and could serve it.

The fix adds a second, additive credential in the same `Authorization: Bearer` slot: a **session-continuation token**, a short-lived (60 seconds by default) self-signed assertion `{identity_id, signing_key_id, nonce, issued_at, expires_at, signature}` minted entirely client-side with the identity's signing key. No server issues one. Verifying it needs only the token's own fields, the signing key's public half from the durable signing-key projection (identical whether the node authored the key or only mirrored it), and a one-time-use nonce checked against a node-local anti-replay table. That table is not itself mirrored, so a token replayed against a different node within its 60-second window can still succeed there. This is an accepted, narrow residual risk rather than a reason to build cross-node nonce coordination.

A continuation token never logs anyone in: it only extends an established session, and nothing routes it into registration or session start. Revoking the signing key makes every future token minted with it fail immediately on every node. Test vectors are in [`session-continuation.json`](https://github.com/avalon-initiative/avalon-protocol/blob/main/conformance/vectors/session-continuation.json).

Third-party games and tools using an SDK receive an already-authenticated session token and never the raw key, so minting happens in first-party client code. A generic SDK-level node-failover story is separate, still-open work.

## Implementation

- Server: [`auth.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/auth.rs), [`passkeys.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/passkeys.rs), [`devices.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/devices.rs), [`device_pairing.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/device_pairing.rs), [`signature_gate.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/signature_gate.rs), [`continuation.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/server/src/continuation.rs).
- Token type: [`crates/protocol/src/continuation.rs`](https://github.com/avalon-initiative/avalon-protocol/blob/main/crates/protocol/src/continuation.rs).
- Endpoints are in the [OpenAPI document](https://github.com/avalon-initiative/avalon-protocol/blob/main/docs/generated/openapi.json) under `/identities/register`, `/sessions`, `/me/passkeys`, `/me/devices`, and `/auth/device`.
- The SDK account-session types mint fresh signatures; see the [SDK design](../../sdk/design.md).

## Related

- [Identity](../identity.md), [recovery and rollback](./recovery.md), [per-identity event chains](./event-chains.md)
- [Security model](../security-model.md), [protocol events](../protocol-events.md)
- [ADR 0786: on-demand cross-node identity data resolution](../../architecture/decisions/0786-on-demand-cross-node-identity-data-resolution.md)
- [Nodes](../../architecture/nodes/README.md), [cross-node login](../../architecture/nodes/cross-node-login.md)
