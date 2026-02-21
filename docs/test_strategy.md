To prove AuraGC is superior, you need to move beyond average performance and focus on **reliability under pressure**. The best test is a **"Memory Saturation & Recovery"** benchmark.

In this test, the "Better" metric isn't just speed; it's the **Survival Rate** and **P99 Latency Stability**.

---

## 1. The "Leak Storm" Stress Test (Best for Hackathons)

This test simulates a real-world bug where a specific API endpoint leaks memory (circular references) under high traffic.

* **The Setup:** Configure both instances (Default vs. AuraGC) with a strict **1024MB RAM limit** via Docker Compose.
* **The Load:** Use **Locust** to flood the `/simulate/leak` endpoint at 50 requests per second.
* **The Proof:**
* **Default GC:** Will eventually exceed the 1024MB limit because its reactive nature doesn't account for the *speed* of the leak. The OS will send a `SIGKILL` (OOM).
* **AuraGC:** The PSI sensor detects the "Memory Pressure" early. The Governor calculates a high **Urgency Score** and forces a `gc.collect(2)` *before* the threshold is hit.


* **Winning Metric:** **Uptime.** Show that AuraGC stayed alive for 10 minutes while the Default GC crashed in 45 seconds.

---

## 2. The "Tail Latency" Jitter Test

This test proves that AuraGC provides a smoother user experience by avoiding massive "Stop-the-World" pauses.

* **The Setup:** Pre-load the application with a 300MB "Warm-up" dataset.
* **The Load:** A steady stream of lightweight API requests.
* **The Proof:**
* **Default GC:** Periodically, it will trigger a full Gen 2 scan. Because it scans the entire 300MB heap, response times for those specific requests will spike (e.g., from 10ms to 500ms).
* **AuraGC:** Because of **Immortal Branding** (`gc.freeze()`), AuraGC ignores the 300MB warm-up data during scans.


* **Winning Metric:** **P99 Latency.** Show that AuraGC's worst-case response time is 5x faster than the default.

---

## 3. The "Throughput vs. Pressure" Test

This demonstrates how AuraGC intelligently balances GC overhead with traffic needs.

* **The Setup:** A variable load that peaks every 30 seconds.
* **The Proof:**
* **Default GC:** Triggers GC based only on object count, potentially firing right in the middle of a traffic peak, slowing down the CPU when it's needed most.
* **AuraGC:** Uses the **Integral ()** part of its formula. It can "silent" (postpone) GC during short spikes if pressure is manageable, and then aggressively clean up during the lulls between traffic bursts.


* **Winning Metric:** **Requests Per Second (RPS)** during peak bursts.

---

## Summary Comparison Table for Your Demo

| Feature | Best Test Case | Winning Visualization |
| --- | --- | --- |
| **Resilience** | Memory Leak Storm | **Survival Chart** (Time vs. RSS) |
| **Predictability** | High-Traffic Jitter | **Latency Histogram** (P95/P99 bars) |
| **Efficiency** | Large Static Dataset | **Scan Time Comparison** (Flame Graphs) |

### Recommended Visual Strategy for Project C

In your **Project C (Visualizer)**, I recommend a split-screen dashboard:

1. **Top:** Real-time RSS Memory (AuraGC should show a "Sawtooth" pattern while Default is a "Straight line up to death").
2. **Bottom:** A "Tombstone" counter showing how many times the Default GC container has restarted due to OOM errors.

**Would you like me to generate the specific Locust load-testing script for the "Leak Storm" scenario?**