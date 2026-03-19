import random
import time

from ogn_tool.runtime.streaming.rf_state_engine import RFStateEngine

# station test (Delemont approx)
stations = {
    "FK50887": (47.37, 7.35, 430)
}

engine = RFStateEngine(station_coords=stations)

N = 200_000

start = time.perf_counter()

for i in range(N):
    packet = {
        "src": f"AC{i % 50}",
        "igate": "FK50887",
        "ts_epoch": 1700000000 + i,
        "lat": 47.2 + random.random() * 0.3,
        "lon": 7.1 + random.random() * 0.4,
        "alt": 1000 + random.random() * 2000,
    }

    engine.ingest_packet(packet)

elapsed = time.perf_counter() - start
pps = N / elapsed

print(f"\nPackets processed: {N}")
print(f"Elapsed time: {elapsed:.3f} s")
print(f"Packets/s: {pps:,.0f}")
print(f"Time per packet: {(elapsed / N) * 1e6:.1f} us")

print("\nMetrics snapshot:")
print(engine.get_metrics_snapshot())
