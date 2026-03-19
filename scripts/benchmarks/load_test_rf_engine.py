import random
import time

from ogn_tool.runtime.streaming.rf_state_engine import RFStateEngine

stations = {"FK50887": (47.37, 7.35, 430)}
engine = RFStateEngine(station_coords=stations)

N = 10_000_000

start = time.perf_counter()

for i in range(N):
    packet = {
        "src": f"A{i % 100}",
        "igate": "FK50887",
        "ts_epoch": 1700000000 + i,
        "lat": 47.2 + random.random() * 0.3,
        "lon": 7.1 + random.random() * 0.4,
        "alt": 1000 + random.random() * 2000,
    }
    engine.ingest_packet(packet)

elapsed = time.perf_counter() - start

print("Packets:", N)
print("Time:", elapsed)
print("Packets/s:", N / elapsed)

# Stability checks
print("Aircraft states cached:", len(engine.aircraft_states))
print("Spatial index cache cells:", len(engine.spatial_index._cache))
metrics = engine.get_metrics_snapshot()
hist = metrics.get("station_azimuth_histogram", {}).get("FK50887", [])
print("Azimuth bins:", len(hist))
