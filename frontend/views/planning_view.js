
import { buildPlanningLayers } from '../layers/planning_layers.js';

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function distanceKm(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

function scoreLabel(score) {
  if (score < 0.3) return 'Low interest';
  if (score < 0.6) return 'Moderate';
  return 'High';
}

function getReferenceStationId(context) {
  const explicit = context?.referenceStationId;
  if (typeof explicit === 'string' && explicit.trim()) return explicit.trim().toUpperCase();

  const payloadStation = context?.payload?.reference_station_id;
  if (typeof payloadStation === 'string' && payloadStation.trim()) return payloadStation.trim().toUpperCase();

  return null;
}

function getCandidateStation(context) {
  const stationId = getReferenceStationId(context);
  const registry = Array.isArray(context?.stationRegistry) ? context.stationRegistry : [];
  const payloadStations = Array.isArray(context?.payload?.stations) ? context.payload.stations : [];

  const merged = new Map();
  for (const row of registry) {
    if (typeof row?.station_id === 'string') merged.set(row.station_id.toUpperCase(), { ...row });
  }
  for (const row of payloadStations) {
    const station_id = typeof row?.station_id === 'string' ? row.station_id.toUpperCase() : null;
    if (!station_id) continue;
    merged.set(station_id, { ...(merged.get(station_id) || {}), ...row });
  }

  if (!stationId) return null;
  const candidate = merged.get(stationId);
  if (!candidate) return null;

  const lat = Number(candidate.lat);
  const lon = Number(candidate.lon ?? candidate.lng);
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;

  return {
    station_id: candidate.station_id || stationId,
    lat,
    lon,
    source: candidate.source || 'registry',
    alt_m: candidate.alt_m ?? null,
  };
}

function buildPlanningData(context) {
  const candidate = getCandidateStation(context);
  if (!candidate) {
    return {
      candidate_station: null,
      planning: {
        neighbor_count: 0,
        closest_station: null,
        avg_distance_km: null,
        placement_score: 0,
        nearby_stations: [],
      },
    };
  }

  const registry = Array.isArray(context?.stationRegistry) ? context.stationRegistry : [];
  const neighbors = registry
    .filter((row) => typeof row?.station_id === 'string' && row.station_id.toUpperCase() !== String(candidate.station_id).toUpperCase())
    .map((row) => ({
      station_id: row.station_id,
      lat: Number(row.lat),
      lon: Number(row.lon ?? row.lng),
      source: row.source || 'registry',
    }))
    .filter((row) => Number.isFinite(row.lat) && Number.isFinite(row.lon))
    .map((row) => ({
      ...row,
      distance_km: distanceKm(candidate.lat, candidate.lon, row.lat, row.lon),
    }))
    .filter((row) => row.distance_km <= 100)
    .sort((a, b) => a.distance_km - b.distance_km);

  const nearbyStations = neighbors.slice(0, 8);
  const avgDistance = nearbyStations.length
    ? nearbyStations.reduce((acc, row) => acc + row.distance_km, 0) / nearbyStations.length
    : null;
  const placementScore = avgDistance == null ? 1 : clamp(avgDistance / 30, 0, 1);

  return {
    candidate_station: candidate,
    planning: {
      neighbor_count: nearbyStations.length,
      closest_station: nearbyStations.length
        ? { station_id: nearbyStations[0].station_id, distance_km: nearbyStations[0].distance_km }
        : null,
      avg_distance_km: avgDistance,
      placement_score: placementScore,
      nearby_stations: nearbyStations,
    },
  };
}

export function buildPlanningView(context) {
  const planningPayload = buildPlanningData(context);
  const planning = planningPayload.planning || {};

  const summary = {
    neighborCount: planning.neighbor_count ?? 0,
    closest: planning.closest_station ?? null,
    avgDistance: planning.avg_distance_km ?? null,
    score: planning.placement_score ?? 0,
    scoreLabel: scoreLabel(planning.placement_score ?? 0),
  };

  return {
    layers: buildPlanningLayers(planningPayload, context),
    nodeContext: context?.selection?.nodeId
      ? {
          supported: false,
          reason: 'Node inspection is not applicable in planning mode',
          focusData: null,
        }
      : {
          supported: true,
          reason: null,
          focusData: null,
        },
    summary,
    planningPayload,
  };
}
