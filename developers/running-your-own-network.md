# Running your own network

**Status:** Partially implemented — every command below exists and is documented; the full path has not yet been drilled end to end on a clean machine, and a hosted option for third-party networks is not offered.

A developer, a company or a community can run an Avalon network of its own, under its own `network_id` and its own settlement key, using the same code as the public network. This page is the step-by-step path. Before starting, know what you are building: your network is a separate network, cryptographically unable to merge with the public one. Signatures are network-agnostic, the ledgers are not. See [network trust anchors](../protocol/network-trust-anchors.md) for why.

## Two ways to do it

| Path | Fork needed | What clients see |
| --- | --- | --- |
| **Custom network** | No | The SDKs and the Hub report the network as unverified or custom. It works, and nothing vouches for it. Good for development and private communities. |
| **Verified network** | Yes: the protocol repository and the SDKs | Your own trust-anchor list pins your network's key, so clients you ship verify it. Good for a company or community that wants its clients to verify its network. |

Both start with steps 1 to 4. Steps 5 to 7 are the verified path.

## 1. Choose a `network_id`

Any unique string. Avoid the `avalon-` prefix for a network that is not part of the Avalon Initiative's own list, and never use `avalon-mainnet-N`, which is reserved for the one canonical public network. A name such as `acme-prod-1` is clear. Never reuse an id for a different network.

## 2. Generate the settlement signing key

The signing key is a 32-byte Ed25519 seed. Keep it secret and back it up; losing it ends the ability to extend the network's own history.

```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

Derive the verify key, the public half you will publish. Paste the seed on standard input so it stays out of shell history:

```bash
python3 -c "
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey as K
print(K.from_private_bytes(bytes.fromhex(input().strip())).public_key().public_bytes_raw().hex())"
```

## 3. Start the first node

Run the guided setup from the [hosting guide](https://github.com/avalon-initiative/avalon-protocol/blob/main/docs/projects/backend-server/for-hosters/standalone-binary.md), with these set in the environment or the generated `avalon.env`:

```bash
AVALON_NETWORK_ID=acme-prod-1
AVALON_SETTLEMENT_SIGNING_KEY=<the seed from step 2>
avalon setup          # add --yes to take every answer from the environment
```

The Docker route (`make stack-up` in the protocol repository) generates both values for you; replace them with your own in `.env` before the first start. The first start commits the `network_id` into the ledger genesis. A database remembers the id it was created with and refuses to start under a different one, so decide before this step. Put the node behind TLS before it is reachable beyond loopback ([deployment](https://github.com/avalon-initiative/avalon-protocol/blob/main/docs/projects/backend-server/for-hosters/deployment.md)).

## 4. Check it is healthy

```bash
curl -s https://<your-node>/nodes/status        # network_id is the one you chose
curl -s https://<your-node>/ledger/sth/latest   # a signed tree head
```

At this point you have a working custom network. Integrators can point their SDKs at the node's URL.

## 5. Fork the protocol repository and publish your entry

Fork `avalon-protocol`. In your fork, add an entry to `docs/trusted-networks.json`:

```json
{
  "label": "acme-prod-1",
  "network_id": "acme-prod-1",
  "verify_key": "<the verify key from step 2>",
  "signing_key_id": "settlement-operator-1",
  "server_url": "https://node1.example.com",
  "environment": "prod",
  "seed_nodes": ["https://node1.example.com", "https://node2.example.com"],
  "notes": "What this network is for and any availability promise."
}
```

Add the matching row to the README's trusted-networks table and run `make check-trust-anchors`. Field meanings are in [network trust anchors](../protocol/network-trust-anchors.md#the-trust-anchor-list). Remove or keep the Avalon entries as you prefer; your fork's file is yours.

## 6. Point the SDKs at your list

The SDKs fetch the trust-anchor list at runtime from one constant: `TRUST_ANCHORS_URL` in the Rust and TypeScript SDKs and `TrustAnchors.PublishedUrl` in the C# SDK. Fork `avalon-sdks` and change that constant to the raw URL of your fork's `docs/trusted-networks.json`. The three SDKs share one version and one release in the Avalon Initiative's own repository; releasing your fork's packages is your own process.

## 7. Add seeds and join more nodes

List several seeds on different hosts and networks, and monitor them as described in [seed nodes](https://github.com/avalon-initiative/avalon-protocol/blob/main/docs/projects/backend-server/for-hosters/seed-nodes.md). A joining node sets the same `AVALON_NETWORK_ID`, finds the network through the seeds in its entry, mirrors the core shard and verifies every head against the pinned key. A node reads the list compiled into its binary, so an entry change reaches nodes with your fork's next release; set `AVALON_BOOTSTRAP_PEERS` and `AVALON_MIRROR_PEERS` to bridge the gap.

## What you take on

- You hold the settlement key. Its custody, rotation and backup are your responsibility: see [key rotation](https://github.com/avalon-initiative/avalon-protocol/blob/main/docs/projects/backend-server/for-maintainers/key-rotation.md).
- You track upstream. Protocol changes and releases come from the Avalon Initiative's repositories; your fork rebases onto them. Mixed versions across your own nodes follow the same [upgrade guidance](https://github.com/avalon-initiative/avalon-protocol/blob/main/docs/projects/backend-server/for-hosters/upgrading.md).
- Integrators register as issuers per network, so an integrator already issuing on another network registers again on yours.
- Moving a network to a new `network_id` later is possible with `avalon migrate-network`; plan for it only as a rare event.

## Related

- [Running a node](running-a-node.md)
- [Network environments](../architecture/network-environments.md)
- [Network trust anchors](../protocol/network-trust-anchors.md)
- [Self-hosting](../architecture/self-hosting.md)
- [Building an integration](../integrations/building-an-integration.md)
