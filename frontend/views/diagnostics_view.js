import { buildRFLayers } from '../layers/rf_layers.js';

export function interpretNode(selection, payload) {
  if (!selection?.nodeId) {
    return { supported: true, reason: null, focusData: null };
  }

  if (selection.nodeType === 'station') {
    const stations = Array.isArray(payload?.stations) ? payload.stations : [];
    const exists = stations.some((s) => s?.station_id === selection.nodeId);
    if (!exists) return { supported: false, reason: 'Selected station has no diagnostics in this run.', focusData: null };
    return { supported: true, reason: null, focusData: null };
  }

  if (selection.nodeType === 'zone') {
    return { supported: true, reason: null, focusData: null };
  }

  return { supported: false, reason: 'Diagnostics mode supports station and zone nodes only.', focusData: null };
}

export function buildDiagnosticsLayers(context) {
  const { payload, selection, uiFlags } = context;
  const nodeContext = interpretNode(selection, payload);

  const selectionForLayers = nodeContext.supported ? selection : { ...selection, nodeId: null, nodeType: null };

  const layers = buildRFLayers(payload, {
    ...uiFlags,
    showCoverage: false,
    showCriticalObservations: false,
    showSignalLoss: true,
    showModelValidation: uiFlags.showModelValidation,
  }, selectionForLayers, { mode: 'diagnostics' });

  return { layers, nodeContext };
}
