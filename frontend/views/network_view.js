import { buildRFLayers } from '../layers/rf_layers.js';

function nodeInMessages(payload, nodeId, nodeType) {
  const messages = Array.isArray(payload?.metrics?.aircraft_positions) ? payload.metrics.aircraft_positions : [];
  if (!messages.length) return false;

  if (nodeType === 'receiver' || nodeType === 'station') {
    return messages.some((m) => Array.isArray(m?.seen_by) && m.seen_by.includes(nodeId));
  }

  if (nodeType === 'emitter') {
    return messages.some((m) => String(m?.src || m?.aircraft_id || '') === String(nodeId));
  }

  return false;
}

export function interpretNode(selection, payload) {
  if (!selection?.nodeId) {
    return { supported: true, reason: null, focusData: null };
  }

  if (selection.nodeType === 'zone') {
    return { supported: true, reason: null, focusData: null };
  }

  if (selection.nodeType === 'receiver' || selection.nodeType === 'emitter' || selection.nodeType === 'station') {
    const exists = nodeInMessages(payload, selection.nodeId, selection.nodeType);
    if (!exists) {
      return { supported: false, reason: 'Selected node is not present in current network graph.', focusData: null };
    }
    return { supported: true, reason: null, focusData: null };
  }

  return { supported: false, reason: 'Node type is not supported in Network mode.', focusData: null };
}

export function buildNetworkViewLayers(context) {
  const { payload, selection, uiFlags } = context;
  const nodeContext = interpretNode(selection, payload);
  const selectionForLayers = nodeContext.supported ? selection : { ...selection, nodeId: null, nodeType: null };

  const layers = buildRFLayers(payload, {
    ...uiFlags,
    showCoverage: true,
    showCriticalObservations: true,
    showSignalLoss: true,
  }, selectionForLayers, { mode: 'network' });

  return { layers, nodeContext };
}
