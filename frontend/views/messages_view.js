import { buildMessagesLayers } from '../layers/messages_layers.js';

function toMessages(modePayload) {
  return Array.isArray(modePayload?.messages) ? modePayload.messages : [];
}

export function interpretNode(selection, payload) {
  const messages = toMessages(payload);

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

function buildMessageGraph(modePayload) {
  const messages = toMessages(modePayload);
  console.log('MESSAGES RAW', messages.length, messages.length ? messages[0] : null);

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
          layerType: 'network_edge',
        };
        edgeMap.set(edgeKey, edge);
      }
      edge.message_count += 1;
      if (m.receiver_is_inferred) edge.inferred_message_count += 1;
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
    return {
      ...edge,
      inferred_message_count: inferredCount,
      inferred_ratio: Number(inferredRatio.toFixed(3)),
      receiver_is_mostly_inferred: inferredRatio >= 0.5,
    };
  });
  console.log('NODES', nodes.length);

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

