# Future Layers: Portable Assets and Economy

**Status:** Planned — neither layer has any implementation

Two phases sit deliberately after the network, the SDKs, and external integrations have proven themselves: portable assets (phase 4) and economic interoperability (phase 5). Neither is foundational. This page records what today's design must not preclude, so that when the time comes nothing has to be torn out.

Nothing on this page exists in the code. No asset type, event, or economic primitive is implemented.

## Portable assets (phase 4)

Ownership and functionality are separate. Provenance can be portable while behavior stays integrator-specific.

```text
Asset
    ID:               game:ashen-realms:asset:legendary-sword:<serial>
    Source integrator: Ashen Realms
    Original issuer:  Ashen Realms
    Originally to:    Identity Y
    Transfers:        Y -> Z, Z -> X
    Current owner:    Identity X

Ashen Realms:  a powerful weapon
Integrator B:  recognized as the "Champion Blade" cosmetic
Integrator C:  not recognized at all
```

All three integrators behave correctly. The asset's identity and history survive; what it does is each integrator's decision, exactly as with achievements ([trust model](../protocol/trust-model.md)).

Boundaries that hold from day one:

- **Not every item is an Avalon asset.** An integrator decides which of its items, if any, are portable. Integrator-specific inventory stays in the integrator's database.
- **Provenance is first-class:** who issued it, where it originated, when, who owns it now, whether it has been revoked, and whether a consuming integrator recognizes it ([provenance](../protocol/provenance.md)).
- **Integrators have scoped authority.** Integrator A can issue integrator A's assets. It cannot rewrite integrator B's, and it cannot alter ownership history.
- **Standardized asset schemas are Undecided.** The general model for integrator data (representation, publication, versioning) is settled in [integrator space](../protocol/integrator-space.md), but its asset-specific application is not. A schema reference on the asset, like the one attestations carry, is the likely shape; a universal item format is not.

## Economy (phase 5)

A universal cryptocurrency, currency, item market, or financial layer is not the foundation of Avalon, and Avalon must deliver value without one. The reasons are concrete: speculation, volatility, market manipulation, regulatory and tax exposure, AML and KYC obligations, minors interacting with financial systems, disruption of integrator economies, integrators turning into financial products, and incentive attacks on everything the network measures ([registry](../protocol/registry.md)). Settlement has no native currency or token ([ADR 0186](decisions/0186-no-blockchain-validator-consensus-transparency-log-only.md)).

If economic interoperability is ever introduced, the developer-facing shape is an abstraction, not a wallet:

```rust
store.purchase(user, "premium_mount").await?;
```

with no smart contracts, chain transactions, signing, or settlement visible to the integrator, which is the same principle as the rest of the SDK ([SDK design](../sdk/design.md)). Economic infrastructure is introduced only after the network demonstrates real utility and only if it serves the ecosystem rather than defining it. Whether it is built at all is Undecided.

## What today's design must not preclude

- **Asset provenance as attestations plus ownership events.** Issuance is an attestation by the source integrator; each transfer is a durable, signed protocol event referencing the previous owner. The event pipeline, batching, and revocation model already support this shape ([protocol events](../protocol/protocol-events.md), [revocation](../protocol/revocation.md)). Nothing in the protocol should assume the only attestable thing is an achievement.
- **Namespaced asset ids.** Global ids already namespace by owner and kind, so assets get a kind, not a new id scheme.
- **Recognition policies that scope by asset class.** The trust model's scoping dimensions include asset class and currency claims from the start, even though nothing issues them yet.
- **No protocol-level currency assumptions.** Nothing in identity, guilds, or attestations references a balance, a wallet, or a price. Wallet capability names in the permission model are reserved names, not a commitment to build them.

## Implementation

Status: Planned. If assets are built they would be a module of the existing protocol types component, not a new component; the global id and achievement attestation types in the [protocol crate](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/protocol) are the patterns an asset issuance would follow.

## Related

- [Overview](overview.md)
- [Settlement](settlement.md)
- [Trust model](../protocol/trust-model.md), [provenance](../protocol/provenance.md)
- [Integrator space](../protocol/integrator-space.md)
