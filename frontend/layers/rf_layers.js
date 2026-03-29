function sanitizeCells(rows) {
  if (!Array.isArray(rows)) return [];
  return rows
    .map((row) => ({ lat: Number(row?.lat), lon: Number(row?.lon ?? row?.lng), value: Number(row?.value) }))
    .filter((row) => Number.isFinite(row.lat) && Number.isFinite(row.lon) && Number.isFinite(row.value));
}

function validCoord(row) {
  return Number.isFinite(Number(row?.lat)) && Number.isFinite(Number(row?.lon ?? row?.lng));
}

function resolveSelectedNode(payload, selection) {
  if (!selection?.nodeId || !selection?.nodeType) return null;

  if (selection.nodeType === 'station') {
    const stations = Array.isArray(payload?.stations) ? payload.stations : [];
    const row = stations.find((s) => s?.station_id === selection.nodeId && validCoord(s));
    if (!row) return null;
    return { lat: Number(row.lat), lon: Number(row.lon ?? row.lng), type: 'station', nodeId: selection.nodeId };
  }

  if (selection.nodeType === 'zone') {
    const [latText, lonText] = String(selection.nodeId).split('|');
    const lat = Number(latText);
    const lon = Number(lonText);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
    return { lat, lon, type: 'zone', nodeId: selection.nodeId };
  }

  return null;
}

function focusOpacity(distanceKm, strongRadiusKm = 4, neighborRadiusKm = 10) {
  if (distanceKm <= strongRadiusKm) return 1.0;
  if (distanceKm <= neighborRadiusKm) return 0.8;
  return 0.1;
}

function approxDistanceKm(a, b) {
  if (!a || !b) return Infinity;
  const dLat = (Number(a.lat) - Number(b.lat)) * 111;
  const dLon = (Number(a.lon) - Number(b.lon)) * 111 * Math.cos(((Number(a.lat) + Number(b.lat)) / 2) * Math.PI / 180);
  return Math.sqrt(dLat * dLat + dLon * dLon);
}

function alphaForRow(row, focusRef, strongKm, neighborKm, baseAlpha) {
  if (!focusRef) return baseAlpha;
  const distance = approxDistanceKm(row, focusRef);
  return Math.round(baseAlpha * focusOpacity(distance, strongKm, neighborKm));
}

function createStationHaloLayer(stations, selection, layerId = 'rf-station-halo') {
  const rows = Array.isArray(stations) ? stations.filter(validCoord) : [];
  if (!rows.length) return null;

  const focusRef = resolveSelectedNode({ stations }, selection);

  return new deck.ScatterplotLayer({
    id: layerId,
    data: rows,
    pickable: false,
    radiusUnits: 'meters',
    getPosition: (d) => [Number(d.lon ?? d.lng), Number(d.lat)],
    getRadius: 240,
    getFillColor: (d) => {
      const isSelected = focusRef?.type === 'station' && d?.station_id === focusRef?.nodeId;
      return [22, 163, 74, isSelected ? 78 : 28];
    },
    stroked: false,
  });
}

export function createStationsLayer(stations, layerId = 'rf-stations', selection = null) {
  const rows = Array.isArray(stations) ? stations.filter(validCoord) : [];
  if (!rows.length) return null;
  const focusRef = resolveSelectedNode({ stations }, selection);

  return new deck.ScatterplotLayer({
    id: layerId,
    data: rows,
    pickable: true,
    radiusUnits: 'meters',
    getPosition: (d) => [Number(d.lon ?? d.lng), Number(d.lat)],
    getRadius: (d) => {
      const isSelected = focusRef?.type === 'station' && d?.station_id === focusRef?.nodeId;
      return isSelected ? 290 : 220;
    },
    getFillColor: (d) => {
      const isSelected = focusRef?.type === 'station' && d?.station_id === focusRef?.nodeId;
      return [22, 163, 74, isSelected ? 255 : 205];
    },
    getLineColor: [240, 253, 244, 255],
    lineWidthMinPixels: 2.5,
    stroked: true,
  });
}

function buildCoverageLayer(spatial, focusRef, mode) {
  const rows = sanitizeCells(spatial?.coverage_density).filter((r) => r.value > 0);
  if (!rows.length) return null;
  const modeAlpha = mode === 'rf' ? 82 : 58;

  return new deck.ScatterplotLayer({
    id: 'rf-coverage',
    data: rows,
    pickable: true,
    radiusUnits: 'meters',
    getPosition: (d) => [d.lon, d.lat],
    getRadius: (d) => 220 + Math.log1p(Math.max(d.value, 0)) * 300,
    getFillColor: (d) => [125, 211, 252, alphaForRow(d, focusRef, 5, 11, modeAlpha)],
    getLineColor: (d) => [125, 211, 252, alphaForRow(d, focusRef, 5, 11, Math.round(modeAlpha * 1.4))],
    lineWidthMinPixels: 1,
    stroked: true,
  });
}

function buildCriticalLayer(spatial, focusRef, mode) {
  const rows = sanitizeCells(spatial?.unique_coverage).filter((r) => r.value > 0.4);
  if (!rows.length) return null;
  const modeAlpha = mode === 'network' ? 64 : 96;

  return new deck.ScatterplotLayer({
    id: 'rf-critical-observations',
    data: rows,
    pickable: true,
    radiusUnits: 'meters',
    getPosition: (d) => [d.lon, d.lat],
    getRadius: (d) => 96 + Math.log1p(Math.max(d.value, 0)) * 138,
    getFillColor: (d) => [125, 211, 252, alphaForRow(d, focusRef, 4, 9, modeAlpha)],
    getLineColor: (d) => [226, 232, 240, alphaForRow(d, focusRef, 4, 9, Math.round(modeAlpha * 1.5))],
    lineWidthMinPixels: 1,
    stroked: true,
  });
}

function buildSignalLossLayer(spatial, focusRef, mode) {
  const rows = sanitizeCells(spatial?.blind_problematic?.length ? spatial.blind_problematic : spatial?.blind_zones_masked);
  if (!rows.length) return null;
  const modeAlpha = mode === 'diagnostics' ? 110 : 22;

  return new deck.ScatterplotLayer({
    id: 'rf-signal-loss',
    data: rows,
    pickable: true,
    radiusUnits: 'meters',
    getPosition: (d) => [d.lon, d.lat],
    getRadius: (d) => 130 + Math.log1p(Math.max(d.value || 1, 1)) * 30,
    getFillColor: (d) => [239, 68, 68, alphaForRow(d, focusRef, 4, 10, modeAlpha)],
    getLineColor: (d) => [239, 68, 68, alphaForRow(d, focusRef, 4, 10, Math.round(Math.min(150, modeAlpha * 1.8)))],
    lineWidthMinPixels: mode === 'diagnostics' ? 2.1 : 1.0,
    stroked: true,
  });
}

function buildValidationLayer(spatial, focusRef) {
  const rows = sanitizeCells(spatial?.analysis_mask);
  if (!rows.length) return null;

  const problematic = new Set(sanitizeCells(spatial?.blind_problematic).map((r) => `${r.lat.toFixed(5)}|${r.lon.toFixed(5)}`));

  return new deck.ScatterplotLayer({
    id: 'rf-model-validation',
    data: rows,
    pickable: true,
    radiusUnits: 'meters',
    getPosition: (d) => [d.lon, d.lat],
    getRadius: 52,
    getFillColor: (d) => {
      const key = `${d.lat.toFixed(5)}|${d.lon.toFixed(5)}`;
      const alpha = alphaForRow(d, focusRef, 4, 10, 160);
      return problematic.has(key) ? [239, 68, 68, alpha] : [34, 197, 94, Math.round(alpha * 0.85)];
    },
  });
}

function buildSelectedNodeHighlight(payload, selection) {
  const ref = resolveSelectedNode(payload, selection);
  if (!ref) return null;

  return new deck.ScatterplotLayer({
    id: 'selected-node-highlight',
    data: [ref],
    pickable: false,
    radiusUnits: 'meters',
    getPosition: (d) => [d.lon, d.lat],
    getRadius: (d) => (d.type === 'station' ? 360 : 220),
    getFillColor: [250, 204, 21, 36],
    getLineColor: [250, 204, 21, 220],
    lineWidthMinPixels: 2,
    stroked: true,
  });
}

export function buildRFLayers(payload, filters, selection = null, options = {}) {
  const spatial = payload?.metrics?.spatial_network_features;
  const mode = options?.mode || 'rf';
  const focusRef = resolveSelectedNode(payload, selection);
  const layers = [];

  if (filters.showCoverage) layers.push(buildCoverageLayer(spatial, focusRef, mode));
  if (filters.showCriticalObservations) layers.push(buildCriticalLayer(spatial, focusRef, mode));
  if (filters.showSignalLoss) layers.push(buildSignalLossLayer(spatial, focusRef, mode));
  if (filters.showModelValidation) layers.push(buildValidationLayer(spatial, focusRef));

  layers.push(createStationHaloLayer(payload?.stations, selection));
  layers.push(buildSelectedNodeHighlight(payload, selection));
  layers.push(createStationsLayer(payload?.stations, 'rf-stations', selection));
  return layers.filter(Boolean);
}
