# TransitPulse Benchmark Results

All runs: synthetic data with injected anomalies, single laptop, Windows 11,
Docker Desktop (Kafka, Postgres, Redis), Python consumer (rolling per-route z-score).

## Run 1: scale test (2M events, unlimited rate)

- **Date:** 2026-10-0X
- **Command:** `python bench/bench.py 2000000 0`
- **Threshold:** z > 3.0 (window = 500 per route, min 30 samples)

| Metric | Result |
|---|---|
| Events processed | 2,000,000 |
| Wall time | 159.9 s |
| End-to-end throughput | ~12,500 events/sec |
| True positives | 66,197 |
| False positives | 3,694 |
| False negatives | 0 |
| Precision | 0.95 |
| Recall | 1.00 |

**Note:** latency is not reported for this run. At unlimited rate the producer
fills Kafka faster than the consumer drains it, so measured latency (p50 76 s)
is queueing delay, not processing time.

## Run 2: smaller runs (20k events, unlimited rate)

| Run | Throughput | Precision | Recall |
|---|---|---|---|
| 1 | 9,985 events/sec | 0.95 | 0.99 |
| 2 | 13,246 events/sec | 0.95 | 1.00 |

## Threshold sweep (10k events, paced 500/sec)

| Threshold | Precision | Recall |
|---|---|---|
| 2.0 | | |
| 2.5 | | |
| 3.0 | 0.94 | 1.00 |

## Latency (paced run)

| Metric | Result |
|---|---|
| p50 | TBD |
| p95 | TBD |

## Caveats

- Anomaly labels are injected by the producer, so precision/recall measure
  agreement with synthetic ground truth, not real-world transit incidents.
- Numbers come from one machine and will vary with hardware.


## Latency (paced run)

- **Command:** `python bench/bench.py 10000 500` (actual producer rate ~450 events/sec)
- **Threshold:** z > 3.0

| Metric | Result |
|---|---|
| p50 latency | 308 ms |
| p95 latency | 546 ms |
| Precision | 0.97 |
| Recall | 1.00 |
| TP / FP / FN | 439 / 12 / 0 |

Latency is measured from producer timestamp to the moment the consumer scores
the event, so it includes Kafka transit and consumer batching.

## Threshold sweep (10k events, paced 500/sec)

| Threshold | Precision | Recall |
|---|---|---|
| 2.0 | TBD | TBD |
| 2.5 | TBD | TBD |
| 3.0 | 0.97 | 1.00 |

## Dataset versions

- The 2M-event run and the 20k runs used the first generator (random
  anomalies, 10 stations).
- The paced runs use the current generator (21 stations, rush-hour,
  weather and event effects). Results are not directly comparable.