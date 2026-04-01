export const MODES = {
  RF: 'rf',
  DIAGNOSTICS: 'diagnostics',
  NETWORK: 'network',
  MESSAGES: 'messages',
  PLANNING: 'planning',
};

export const state = {
  runId: null,
  loadToken: 0,
  payload: null,
  modePayload: null,
  mode: MODES.NETWORK,
  referenceStation: null,
  viewState: { longitude: 7.273, latitude: 47.336, zoom: 9.5, pitch: 0, bearing: 0 },
  filters: {
    showCoverage: true,
    showCriticalObservations: true,
    showSignalLoss: true,
    showModelValidation: false,
    showNetworkEdges: false,
  },
  selection: {
    runId: null,
    mode: MODES.NETWORK,
    nodeId: null,
    nodeType: null, // 'station' | 'receiver' | 'zone' | null
    edgeKey: null,
    focusLocked: false,
  },
  selectedNodeMeta: null,
  selectedEdgeMeta: null,
  lastModeError: null,
  stationRegistry: [],
};
