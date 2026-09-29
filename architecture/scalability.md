# Scalability

**Status:** Partially implemented — single-node limits and behavior under load are measured; multi-host, real-scale deployment has not been

The stress model is deliberately large: 1,000 integrators by 100,000 identities each is 100,000,000 identities. That is not 100 million gameplay events per second flowing through Avalon, because gameplay stays integrator-side. The question is how many durable facts that population produces, how much history it accumulates, how many reads and connections it generates, and whether each part of the system scales independently.

## What scale is not

Not transaction throughput on a chain. Movement, combat, HP, XP ticks, NPC state, and ordinary chat never reach Avalon ([protocol events](../protocol/protocol-events.md)). A design that puts hot gameplay on infrastructure that cannot scale with gameplay is wrong, not the infrastructure.

## Dimensions

Each is evaluated on its own. A system that handles event volume but takes a week to rebuild an index is not scalable.

| Dimension | The question | Where it lands |
| --- | --- | --- |
| Durable event volume | How many protocol events per day, network-wide? | [settlement](settlement.md) |
| Batch size and cadence | How many events per batch, how often, and with what latency to "settled"? | [settlement](settlement.md) |
| Query volume | How many profile, friend, guild, and registry reads per second? | [query and indexing](query-and-indexing.md) |
| Realtime connections | How many identities are connected, and how does presence fan out? | [distributed topology](distributed-topology.md), [presence](../protocol/presence.md) |
| Historical volume | How large is the log after 5, 10, or 20 years? | [retention and growth](settlement/retention-and-growth.md) |
| Rebuild time | How long to reconstruct every projection from genesis? | [disaster recovery](disaster-recovery.md) |
| Node specialization | Can settlement, indexing, realtime, and gateway scale separately? | [nodes](nodes/roles-and-extraction.md) |
| SDK routing | Does discovery and failover stay cheap as node count grows? | [discovery](nodes/discovery-and-peering.md), [SDK design](../sdk/design.md) |

## Back-of-envelope

Every number below is an assumption to be replaced by data. The point is the shape.

- **Events.** Suppose an active identity generates one durable event a day on average and 10% of the 100M are active daily: about 10M events a day, roughly 115 per second. Bursty (a raid completes, a tournament ends) but nowhere near gameplay rates. A batch of 10,000 events every minute would be about 1,000 commitments a day regardless of backend.
- **History.** At about 1 KB per event, 10M events a day is about 10 GB a day, 3.6 TB a year, and 36 TB at ten years before compaction or payload pruning. This is why rebuild time and mirror cost are first-class concerns and why not every convenience field goes in the log.
- **Reads.** Reads dwarf writes by orders of magnitude and are entirely the indexer's problem; they never touch settlement. Indexers partition by domain or by shard before settlement needs to.
- **Presence.** 10M concurrently online identities is a fan-out problem for the realtime vertical alone. Losing a realtime node costs nothing durable.
- **Rebuild.** If replay sustains 50,000 events per second on one indexer, ten years of history (about 36 billion events at the rate above) is roughly eight days. Snapshots plus incremental replay, and per-domain projections rebuilt in parallel, are the obvious levers, and the reason rebuild must be parallelizable by domain before the log is large. Snapshots are Planned; see [disaster recovery](disaster-recovery.md).

## Failure questions

Asked of every design, with the intended answer.

- **A node disappears.** The SDK routes elsewhere and nothing durable is lost (scenario K, [nodes](nodes/README.md)).
- **A region disappears.** Realtime presence in that region lapses, reads are served by indexers elsewhere, and settlement is mirrored.
- **A database is lost.** Projections rebuild from the log (scenario J, [disaster recovery](disaster-recovery.md)).
- **The settlement log stalls.** Events queue in the outbox, projections keep serving, and commitments resume when the operator does. There is no validator set to stall.

## Scenario L: 1,000 integrators, 100M identities

Does Avalon avoid becoming a gameplay bottleneck? Yes by construction, as long as the hot and durable line holds. The parts that do scale with population (event volume, history size, read volume, presence fan-out) each have an independent lever, which is what the three verticals and the node roles exist to provide.

## Per-process safety limits

Independent of the durable-history scaling story, one server process needs floors that stop it falling over in a burst. These are enforced in the server and described in [node safety limits](nodes/safety-limits.md): a database pool size, a concurrency limit that backpressures, a per-IP and a per-principal rate limit, connection timeouts, and body-size limits.

## Load testing

The repository ships a load-test harness that starts its own isolated server processes on loopback, each with a private Postgres schema dropped afterwards, and drives them with a closed-loop generator that refuses any non-loopback target. A smoke scale runs in continuous integration. The figures below are indicative dev-machine numbers (a shared machine with a networked Postgres, a debug build by default), not capacity claims, and are the range over three runs.

**Limits hold.** A single-address flood was bounded by the per-address ceiling with `429` and `Retry-After` on every rejection, a spoofed forwarding header did not escape the limit, and other clients were unaffected. The per-identity limit held while a second identity from the same address was served. A flood of announces with fabricated peer URLs was cut to the per-source new-peer limit, a full table held its cap by evicting the oldest, and forbidden addresses were rejected with the documented codes. A concurrency cap of 4 under 64 workers produced no drops or errors, only higher latency (about 2.2x to 2.6x at the median). With the database pool at 10 under a mixed 50% write load, throughput was about 3,200 to 3,500 requests per second with no errors.

**Baseline.** A sustained mixed profile (64 workers, 200 identities) reached about 2,850 requests per second on a debug build and about 2,925 on release, with p99 under 6 ms and no errors. Closed-loop saturation of the session-authenticated read path was about 6,200 requests per second on release. The release build used about a fifth of the CPU and two thirds of the memory of debug.

**Slow and oversized requests.** Against default settings before hardening, idle, slow-header, and slow-body connections were never closed. Header-read and request timeouts now close them (a `408` for the slow body), and the request body ceiling is explicit and configurable, with a much smaller one for node-coordination routes. Header-size limits stay at the HTTP library's defaults.

**Known gaps.**

- A database pool of 2 stalls the whole node under concurrent writes: in-flight requests wait for the acquire timeout and fail with `500`, then the node recovers. Three connections and above worked in every test. The cause is not isolated. This is Undecided as to fix.
- Request-processing limits are per process. Loopback runs cannot show behavior behind a real proxy chain, real latency, TLS, or a mesh larger than three nodes.
- Fixed: announce gossip used to carry fabricated entries into neighbors' main tables. Relayed entries now go to a separate unverified pool ([discovery and peering](nodes/discovery-and-peering.md)).

Tuning guidance for hosters (keep the pool at four connections or more and below the database's connection limit divided by node processes, set trusted proxies behind a reverse proxy, use a release build) is in the protocol repository's hosting docs.

## Rebuild-time baseline

The live rebuild test logs the wall-clock time of its own rebuild each run: tens of milliseconds for a small synthetic ledger. That is a first data point for comparison at larger sizes, not a capacity claim. Rebuild runs in one transaction, so time scales with total ledger size.

## Implementation

Status: Partially implemented. A single node's limits are measured. Batching, Merkle roots, and signed tree heads are real, with commit and proof-serving cost O(log n) in ledger size ([settlement](settlement.md)); a real indexer and WebSocket presence service run; and node-role extraction exists. A real-scale, multi-host deployment has not been measured. The trait boundaries between settlement and indexer are the load-bearing scaling affordances. The harness is in the [avalon-protocol repository](https://github.com/avalon-initiative/avalon-protocol/tree/main/crates/loadtest).

## Related

- [Settlement](settlement.md), [query and indexing](query-and-indexing.md)
- [Nodes](nodes/README.md), [node safety limits](nodes/safety-limits.md)
- [Disaster recovery](disaster-recovery.md)
- [Distributed topology](distributed-topology.md)
