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