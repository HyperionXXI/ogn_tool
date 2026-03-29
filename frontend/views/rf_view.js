import { buildRFLayers } from '../layers/rf_layers.js';

function getReceiverCentroid(payload, receiverId) {
  const rows = Array.isArray(payload?.metrics?.aircraft_positions) ? payload.metrics.aircraft_positions : [];
  const points = rows
    .filter((r) => Array.isArray(r?.seen_by) && r.seen_by.includes(receiverId))
    .map((r) => [Number(r.lat), Number(r.lon)])
    .filter((p) => Number.isFinite(p[0]) && Number.isFinite(p[1]));

  if (!points.length) return null;
  const lat = points.reduce((a, p) => a + p[0], 0) / points.length;
  const lon = points.reduce((a, p) => a + p[1], 0) / points.length;
  return { lat, lon };
}

export function interpretNode(selection, payload) {
  if (!selection?.nodeId) {
    return { supported: true, reason: null, focusData: null };
  }

  if (selection.nodeType === 'station') {
    const stations = Array.isArray(payload?.stations) ? payload.stations : [];
    const row = stations.find((s) => s?.station_id === selection.nodeId && Number.isFinite(Number(s?.lat)) && Number.isFinite(Number(s?.lon ?? s?.lng)));
    if (!row) return { supported: false, reason: 'Selected station is not present in this run.', focusData: null };
    return { supported: true, reason: null, focusData: { lat: Number(row.lat), lon: Number(row.lon ?? row.lng), nodeType: 'station', nodeId: selection.nodeId } };
  }

  if (selection.nodeType === 'receiver') {
    const centroid = getReceiverCentroid(payload, selection.nodeId);
    if (!centroid) {
      return { supported: false, reason: 'Receiver has no RF spatial footprint in this mode.', focusData: null };
    }
    return { supported: true, reason: null, focusData: { ...centroid, nodeType: 'zone' } };
  }

  if (selection.nodeType === 'zone') {
    const [latText, lonText] = String(selection.nodeId).split('|');
    const lat = Number(latText);
    const lon = Number(lonText);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
      return { supported: false, reason: 'Selected zone coordinates are invalid.', focusData: null };
    }
    return { supported: true, reason: null, focusData: { lat, lon, nodeType: 'zone' } };
  }

  return { supported: false, reason: 'Node type is not supported in RF mode.', focusData: null };
}

export function buildRFViewLayers(context) {
  const { payload, selection, uiFlags } = context;
  const nodeContext = interpretNode(selection, payload);

  const selectionForLayers = nodeContext.supported && nodeContext.focusData
    ? (nodeContext.focusData.nodeType === 'zone'
      ? {
          ...selection,
          nodeType: 'zone',
          nodeId: `${Number(nodeContext.focusData.lat).toFixed(6)}|${Number(nodeContext.focusData.lon).toFixed(6)}`,
        }
      : {
          ...selection,
          nodeType: nodeContext.focusData.nodeType,
          nodeId: nodeContext.focusData.nodeId ?? selection.nodeId,
        })
    : (nodeContext.supported ? selection : { ...selection, nodeId: null, nodeType: null });

  const layers = buildRFLayers(payload, { ...uiFlags, showCoverage: true }, selectionForLayers, { mode: 'rf' });
  return { layers, nodeContext };
}
