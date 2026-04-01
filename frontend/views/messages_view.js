import { buildMessagesLayers } from '../layers/messages_layers.js';

function toMessages(modePayload) {
  return Array.isArray(modePayload?.messages) ? modePayload.messages : [];
}

function normalizeMessage(message) {
  if (!message || typeof message !== 'object') return null;

  const emitter = message.emitter && typeof message.emitter === 'object' ? message.emitter : {};
  const receiver = message.receiver && typeof message.receiver === 'object' ? message.receiver : {};
  const transport = message.transport && typeof message.transport === 'object' ? message.transport : {};
  const signal = message.signal && typeof message.signal === 'object' ? message.signal : {};

  const normalized = {
    emitter_id: typeof message.emitter_id === 'string' ? message.emitter_id : emitter.id,
    receiver_id: typeof message.receiver_id === 'string' ? message.receiver_id : receiver.id,
    emitter_lat: message.emitter_lat ?? emitter.lat,
    emitter_lon: message.emitter_lon ?? emitter.lon,
    receiver_lat: message.receiver_lat ?? receiver.lat,
    receiver_lon: message.receiver_lon ?? receiver.lon,
    receiver_is_inferred: typeof message.receiver_is_inferred === 'boolean' ? message.receiver_is_inferred : receiver.source === 'inferred',
    protocol: transport.protocol ?? null,
    network: transport.network ?? null,
    band: transport.band ?? null,
    rssi: signal.rssi ?? null,
    snr: signal.snr ?? null,
  };

  if (!normalized.emitter_id || !normalized.receiver_id) return null;
  return normalized;
}

export function interpretNode(selection, payload) {
  const messages = toMessages(payload).map(normalizeMessage).filter(Boolean);

  if (!selection?.nodeId) {
    return { supported: true, reason: null, focusData: null };
  }

  if (selection.nodeType === 'receiver' || selection.nodeType === 'station') {
    const exists = messages.some((m) => m?.receiver_id === selection.nodeId);
    if (!exists) {
      return { supported: false, reason: 'Selected receiver is not present in message stream.', focusData: null };
    }
    return { supported: true, reason: null, focusData: { receiverId: selection.nodeId } };
  }

  if (selection.nodeType === 'emitter') {
    const exists = messages.some((m) => m?.emitter_id === selection.nodeId);
    if (!exists) {
      return { supported: false, reason: 'Selected emitter is not present in message stream.', focusData: null };
    }
    return { supported: true, reason: null, focusData: { emitterId: selection.nodeId } };
  }

  return { supported: false, reason: 'Messages mode supports receiver or emitter nodes only.', focusData: null };
}

function dominantValue(counterMap) {
  if (!(counterMap instanceof Map) || !counterMap.size) return null;
  let bestKey = null;
  let bestCount = -1;
  for (const [key, count] of counterMap.entries()) {
    if (count > bestCount) {
      bestKey = key;
      bestCount = count;
    }
  }
  return bestKey;
}

function buildAnomalyLookup(modePayload) {
  const edges = Array.isArray(modePayload?.graph?.edges) ? modePayload.graph.edges : [];
  const lookup = new Map();

  for (const edge of edges) {
    const emitterId = typeof edge?.emitter_id === 'string' ? edge.emitter_id : null;
    const receiverId = typeof edge?.receiver_id === 'string' ? edge.receiver_id : null;
    if (!emitterId || !receiverId) continue;

    lookup.set(`${emitterId}->${receiverId}`, {
      anomalies: Array.isArray(edge?.anomalies) ? edge.anomalies.filter((value) => typeof value === 'string' && value) : [],
      anomaly_score: Number.isFinite(Number(edge?.anomaly_score)) ? Number(edge.anomaly_score) : 0,
    });
  }

  return lookup;
}

function buildMessageGraph(modePayload) {
  const messages = toMessages(modePayload).map(normalizeMessage).filter(Boolean);
  const anomalyLookup = buildAnomalyLookup(modePayload);

  const nodeMap = new Map();
  const edgeMap = new Map();

  for (const m of messages) {
    if (!m || typeof m !== 'object') continue;

    const receiverId = typeof m.receiver_id === 'string' ? m.receiver_id : null;
    const emitterId = typeof m.emitter_id === 'string' ? m.emitter_id : null;
    const rLat = Number(m.receiver_lat);
    const rLon = Number(m.receiver_lon);

    if (!receiverId || !Number.isFinite(rLat) || !Number.isFinite(rLon)) continue;

    const key = `${receiverId}|${rLat.toFixed(6)}|${rLon.toFixed(6)}`;
    let node = nodeMap.get(key);
    if (!node) {
      node = {
        receiver_id: receiverId,
        lat: rLat,
        lon: rLon,
        message_count: 0,
        emitters: new Set(),
        inferred_count: 0,
        layerType: 'receiver_node',
      };
      nodeMap.set(key, node);
    }

    node.message_count += 1;
    if (m.receiver_is_inferred) node.inferred_count += 1;
    if (emitterId) node.emitters.add(emitterId);

    const eLat = Number(m.emitter_lat);
    const eLon = Number(m.emitter_lon);
    if (emitterId && Number.isFinite(eLat) && Number.isFinite(eLon)) {
      const edgeKey = `${emitterId}->${receiverId}`;
      let edge = edgeMap.get(edgeKey);
      if (!edge) {
        edge = {
          emitter_id: emitterId,
          receiver_id: receiverId,
          source: [eLon, eLat],
          target: [rLon, rLat],
          message_count: 0,
          inferred_message_count: 0,
          rssi_sum: 0,
          rssi_count: 0,
          snr_sum: 0,
          snr_count: 0,
          protocol_counts: new Map(),
          network_counts: new Map(),
          band_counts: new Map(),
          layerType: 'network_edge',
        };
        edgeMap.set(edgeKey, edge);
      }
      edge.message_count += 1;
      if (m.receiver_is_inferred) edge.inferred_message_count += 1;
      if (Number.isFinite(Number(m.rssi))) {
        edge.rssi_sum += Number(m.rssi);
        edge.rssi_count += 1;
      }
      if (Number.isFinite(Number(m.snr))) {
        edge.snr_sum += Number(m.snr);
        edge.snr_count += 1;
      }
      if (typeof m.protocol === 'string' && m.protocol) {
        edge.protocol_counts.set(m.protocol, (edge.protocol_counts.get(m.protocol) || 0) + 1);
      }
      if (typeof m.network === 'string' && m.network) {
        edge.network_counts.set(m.network, (edge.network_counts.get(m.network) || 0) + 1);
      }
      if (typeof m.band === 'string' && m.band) {
        edge.band_counts.set(m.band, (edge.band_counts.get(m.band) || 0) + 1);
      }
    }
  }

  const nodes = Array.from(nodeMap.values()).map((n) => {
    const uniqueEmitters = n.emitters.size;
    const diversity = n.message_count > 0 ? uniqueEmitters / n.message_count : 0;
    return {
      receiver_id: n.receiver_id,
      lat: n.lat,
      lon: n.lon,
      message_count: n.message_count,
      unique_emitters_count: uniqueEmitters,
      inferred_messages_count: Number(n.inferred_count || 0),
      diversity_ratio: Number(diversity.toFixed(3)),
      layerType: n.layerType,
    };
  });

  const edges = Array.from(edgeMap.values()).map((edge) => {
    const inferredCount = Number(edge.inferred_message_count || 0);
    const total = Number(edge.message_count || 0);
    const inferredRatio = total > 0 ? inferredCount / total : 0;
    const avgRssi = edge.rssi_count > 0 ? edge.rssi_sum / edge.rssi_count : null;
    const avgSnr = edge.snr_count > 0 ? edge.snr_sum / edge.snr_count : null;
    const anomaly = anomalyLookup.get(`${edge.emitter_id}->${edge.receiver_id}`) || { anomalies: [], anomaly_score: 0 };
    return {
      emitter_id: edge.emitter_id,
      receiver_id: edge.receiver_id,
      source: edge.source,
      target: edge.target,
      message_count: total,
      inferred_message_count: inferredCount,
      inferred_ratio: Number(inferredRatio.toFixed(3)),
      receiver_is_mostly_inferred: inferredRatio >= 0.5,
      protocol: dominantValue(edge.protocol_counts),
      network: dominantValue(edge.network_counts),
      band: dominantValue(edge.band_counts),
      avg_rssi: avgRssi != null ? Number(avgRssi.toFixed(1)) : null,
      avg_snr: avgSnr != null ? Number(avgSnr.toFixed(1)) : null,
      has_rssi: edge.rssi_count > 0,
      has_snr: edge.snr_count > 0,
      anomalies: anomaly.anomalies,
      anomaly_score: anomaly.anomaly_score,
      layerType: edge.layerType,
    };
  });

  return { nodes, edges, raw_messages_count: messages.length };
}

export function buildMessagesViewLayers(context) {
  const { payload, modePayload, selection, uiFlags } = context;
  const graph = buildMessageGraph(modePayload);
  const nodeContext = interpretNode(selection, modePayload);

  let graphForRender = graph;

  if (selection?.nodeId && nodeContext.supported) {
    if (selection.nodeType === 'receiver' || selection.nodeType === 'station') {
      const filteredNodes = graph.nodes.filter((n) => n.receiver_id === selection.nodeId);
      const receiverIds = new Set(filteredNodes.map((n) => n.receiver_id));
      const filteredEdges = graph.edges.filter((e) => receiverIds.has(e.receiver_id));
      graphForRender = { ...graph, nodes: filteredNodes.length ? filteredNodes : graph.nodes, edges: filteredEdges };
    }

    if (selection.nodeType === 'emitter') {
      const filteredEdges = graph.edges.filter((e) => e.emitter_id === selection.nodeId);
      const receiverIds = new Set(filteredEdges.map((e) => e.receiver_id));
      const filteredNodes = graph.nodes.filter((n) => receiverIds.has(n.receiver_id));
      graphForRender = { ...graph, nodes: filteredNodes.length ? filteredNodes : graph.nodes, edges: filteredEdges };
    }
  }

  const layers = buildMessagesLayers(graphForRender, uiFlags, payload?.stations, selection);
  return { layers, nodeContext };
}

