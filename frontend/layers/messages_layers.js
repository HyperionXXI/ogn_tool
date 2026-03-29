const FOCUS_DIM_ALPHA = 26;
const FOCUS_NEIGHBOR_ALPHA = 204;
const FOCUS_SELECTED_ALPHA = 255;

function getMaxMessageCount(nodes) {
  let max = 0;
  for (const n of nodes) {
    const c = Number(n?.message_count);
    if (Number.isFinite(c) && c > max) max = c;
  }
  return max > 0 ? max : 1;
}

function buildEmitterNodes(graph) {
  const edges = Array.isArray(graph?.edges) ? graph.edges : [];
  const emitterMap = new Map();

  for (const edge of edges) {
    const emitterId = typeof edge?.emitter_id === 'string' ? edge.emitter_id : null;
    const source = Array.isArray(edge?.source) ? edge.source : null;
    if (!emitterId || !source || !Number.isFinite(Number(source[0])) || !Number.isFinite(Number(source[1]))) continue;

    const key = `${emitterId}|${Number(source[1]).toFixed(6)}|${Number(source[0]).toFixed(6)}`;
    let row = emitterMap.get(key);
    if (!row) {
      row = {
        emitter_id: emitterId,
        lon: Number(source[0]),
        lat: Number(source[1]),
        path_count: 0,
        layerType: 'emitter_node',
      };
      emitterMap.set(key, row);
    }
    row.path_count += Number(edge?.message_count || 0);
  }

  return Array.from(emitterMap.values());
}

function buildFocusState(graph, selection, stations = []) {
  const state = {
    selectedReceiverIds: new Set(),
    selectedEmitterIds: new Set(),
    selectedStationIds: new Set(),
    neighborReceiverIds: new Set(),
    neighborEmitterIds: new Set(),
    associatedEdgeKeys: new Set(),
  };

  if (!selection?.nodeId) return state;

  const edges = Array.isArray(graph?.edges) ? graph.edges : [];

  if (selection.nodeType === 'receiver' || selection.nodeType === 'station') {
    state.selectedReceiverIds.add(selection.nodeId);
    if (selection.nodeType === 'station') state.selectedStationIds.add(selection.nodeId);

    for (const edge of edges) {
      if (edge?.receiver_id === selection.nodeId) {
        state.associatedEdgeKeys.add(`${edge.emitter_id}->${edge.receiver_id}`);
        if (edge?.emitter_id) state.neighborEmitterIds.add(edge.emitter_id);
      }
    }
  }

  if (selection.nodeType === 'emitter') {
    state.selectedEmitterIds.add(selection.nodeId);
    for (const edge of edges) {
      if (edge?.emitter_id === selection.nodeId) {
        state.associatedEdgeKeys.add(`${edge.emitter_id}->${edge.receiver_id}`);
        if (edge?.receiver_id) state.neighborReceiverIds.add(edge.receiver_id);
      }
    }
  }

  for (const station of Array.isArray(stations) ? stations : []) {
    if (station?.station_id && state.selectedReceiverIds.has(station.station_id)) {
      state.selectedStationIds.add(station.station_id);
    }
  }

  return state;
}

function resolveNodeOpacity(type, id, focusState) {
  const hasFocus =
    focusState.selectedReceiverIds.size > 0 ||
    focusState.selectedEmitterIds.size > 0 ||
    focusState.selectedStationIds.size > 0;

  if (!hasFocus) {
    if (type === 'receiver') return 0.3;
    if (type === 'emitter') return 0.34;
    if (type === 'station') return 0.75;
    return 1.0;
  }

  if (type === 'receiver') {
    if (focusState.selectedReceiverIds.has(id)) return 1.0;
    if (focusState.neighborReceiverIds.has(id)) return 0.8;
    return 0.1;
  }

  if (type === 'emitter') {
    if (focusState.selectedEmitterIds.has(id)) return 1.0;
    if (focusState.neighborEmitterIds.has(id)) return 0.8;
    return 0.1;
  }

  if (type === 'station') {
    if (focusState.selectedStationIds.has(id)) return 1.0;
    if (focusState.selectedReceiverIds.has(id)) return 1.0;
    return 0.18;
  }

  return 1.0;
}

export function createReceiverNodesLayer(graph, focusState = {}) {
  const nodes = Array.isArray(graph?.nodes) ? graph.nodes : [];
  if (!nodes.length) return null;

  const maxCount = getMaxMessageCount(nodes);

  return new deck.ScatterplotLayer({
    id: 'messages-network-nodes',
    data: nodes,
    pickable: true,
    radiusUnits: 'meters',
    getPosition: (d) => [d.lon, d.lat],
    getRadius: (d) => {
      const c = Number(d?.message_count || 0);
      return Math.max(52, (Math.log1p(Math.max(c, 1)) * 34) * 0.8);
    },
    getFillColor: (d) => {
      const c = Number(d?.message_count || 0);
      const t = Math.max(0, Math.min(1, c / maxCount));
      const opacity = resolveNodeOpacity('receiver', d?.receiver_id, focusState);
      const alpha = Math.round((58 + t * 72) * opacity);
      return [125, 211, 252, alpha];
    },
    getLineColor: (d) => {
      const opacity = resolveNodeOpacity('receiver', d?.receiver_id, focusState);
      return [226, 232, 240, Math.round(150 * opacity)];
    },
    lineWidthMinPixels: 1,
    stroked: true,
  });
}

export function createStationHaloLayer(stations, focusState = {}, layerId = 'messages-station-halo') {
  const rows = Array.isArray(stations)
    ? stations.filter((row) => Number.isFinite(Number(row?.lat)) && Number.isFinite(Number(row?.lon ?? row?.lng)))
    : [];
  if (!rows.length) return null;

  return new deck.ScatterplotLayer({
    id: layerId,
    data: rows,
    pickable: false,
    radiusUnits: 'meters',
    getPosition: (d) => [Number(d.lon ?? d.lng), Number(d.lat)],
    getRadius: 0,
    getFillColor: (d) => {
      const opacity = resolveNodeOpacity('station', d?.station_id, focusState);
      return [34, 197, 94, Math.round(46 * opacity)];
    },
    getLineColor: [0, 0, 0, 0],
    stroked: false,
  });
}

export function createStationNodesLayer(stations, focusState = {}, layerId = 'messages-stations') {
  const rows = Array.isArray(stations)
    ? stations.filter((row) => Number.isFinite(Number(row?.lat)) && Number.isFinite(Number(row?.lon ?? row?.lng)))
    : [];
  if (!rows.length) return null;

  return new deck.ScatterplotLayer({
    id: layerId,
    data: rows,
    pickable: true,
    radiusUnits: 'meters',
    getPosition: (d) => [Number(d.lon ?? d.lng), Number(d.lat)],
    getRadius: 180,
    getFillColor: (d) => {
      const opacity = resolveNodeOpacity('station', d?.station_id, focusState);
      return [22, 163, 74, Math.round(190 * opacity)];
    },
    getLineColor: (d) => {
      const opacity = resolveNodeOpacity('station', d?.station_id, focusState);
      return [240, 253, 244, Math.round(255 * opacity)];
    },
    lineWidthMinPixels: 2.5,
    stroked: true,
  });
}

export function createEmitterNodesLayer(graph, focusState = {}) {
  const rows = buildEmitterNodes(graph);
  if (!rows.length) return null;

  return new deck.ScatterplotLayer({
    id: 'messages-emitters',
    data: rows,
    pickable: true,
    radiusUnits: 'meters',
    getPosition: (d) => [d.lon, d.lat],
    getRadius: (d) => Math.max(42, Math.log1p(Math.max(Number(d?.path_count || 1), 1)) * 18),
    getFillColor: (d) => {
      const opacity = resolveNodeOpacity('emitter', d?.emitter_id, focusState);
      return [251, 146, 60, Math.round(150 * opacity)];
    },
    getLineColor: (d) => {
      const opacity = resolveNodeOpacity('emitter', d?.emitter_id, focusState);
      return [255, 237, 213, Math.round(230 * opacity)];
    },
    lineWidthMinPixels: 1,
    stroked: true,
  });
}

export function createNetworkEdgesLayer(graph, { enabled = false, maxEdges = 30, focusState = {} } = {}) {
  if (!enabled) return null;

  const allEdges = Array.isArray(graph?.edges) ? graph.edges : [];
  if (!allEdges.length) return null;

  const edges = [...allEdges]
    .sort((a, b) => Number(b?.message_count || 0) - Number(a?.message_count || 0))
    .slice(0, maxEdges);

  return new deck.ArcLayer({
    id: 'messages-network-edges',
    data: edges,
    pickable: true,
    getSourcePosition: (d) => d.source,
    getTargetPosition: (d) => d.target,
    getSourceColor: (d) => {
      const key = `${d?.emitter_id}->${d?.receiver_id}`;
      const isFocused = focusState.associatedEdgeKeys?.has(key);
      const inferredRatio = Math.max(0, Math.min(1, Number(d?.inferred_ratio || 0)));
      const alpha = isFocused ? 230 : Math.round(190 - inferredRatio * 90);
      return [180, 220, 255, alpha];
    },
    getTargetColor: (d) => {
      const key = `${d?.emitter_id}->${d?.receiver_id}`;
      const isFocused = focusState.associatedEdgeKeys?.has(key);
      const inferredRatio = Math.max(0, Math.min(1, Number(d?.inferred_ratio || 0)));
      const alpha = isFocused ? 110 : Math.round(88 - inferredRatio * 44);
      return [180, 220, 255, Math.max(28, alpha)];
    },
    getWidth: (d) => {
      const c = Number(d?.message_count || 1);
      const key = `${d?.emitter_id}->${d?.receiver_id}`;
      const isFocused = focusState.associatedEdgeKeys?.has(key);
      const base = Math.max(1.1, Math.log1p(c) * 0.78);
      return isFocused ? base * 1.45 : base;
    },
  });
}

export function buildMessagesLayers(graph, filters, stations = [], selection = null) {
  const focusState = buildFocusState(graph, selection, stations);
  const layers = [];
  layers.push(createNetworkEdgesLayer(graph, { enabled: Boolean(filters?.showNetworkEdges), maxEdges: 30, focusState }));
  layers.push(createEmitterNodesLayer(graph, focusState));
  layers.push(createReceiverNodesLayer(graph, focusState));
  layers.push(createStationHaloLayer(stations, focusState));
  layers.push(createStationNodesLayer(stations, focusState));
  return layers.filter(Boolean);
}
