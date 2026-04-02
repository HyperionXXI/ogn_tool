import { state, MODES } from './state.js';
import { executeRun, fetchModePayload, fetchRunPayload, fetchRuns, fetchRuntimeStatus, fetchStations } from './api.js';
import { buildRFViewLayers } from '../views/rf_view.js';
import { buildDiagnosticsLayers } from '../views/diagnostics_view.js';
import { buildNetworkViewLayers } from '../views/network_view.js';
import { buildMessagesViewLayers } from '../views/messages_view.js';
import { buildPlanningView } from '../views/planning_view.js';

const BASEMAP_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';
let deckInstance = null;
let deckUnavailable = false;
let runsCache = [];
let webglRejectionHandlerInstalled = false;
let runtimeRefreshHandle = null;

function isWebGLInitError(error) {
  const message = typeof error?.message === 'string' ? error.message : '';
  const statusMessage = typeof error?.statusMessage === 'string' ? error.statusMessage : '';
  return (
    message.includes('Failed to initialize WebGL') ||
    message.includes('WebGL creation failed') ||
    statusMessage.includes('WebGL creation failed')
  );
}

function installWebGLRejectionHandler() {
  if (webglRejectionHandlerInstalled || typeof window === 'undefined') return;

  window.addEventListener('unhandledrejection', (event) => {
    const reason = event?.reason;
    if (!isWebGLInitError(reason)) return;

    event.preventDefault();
    console.warn('[WebGL] Deck initialization failed (handled)', reason);
    deckUnavailable = true;
    showWebGLUnavailable(reason);
  });

  webglRejectionHandlerInstalled = true;
}

function $(id) {
  return document.getElementById(id);
}

function setFeedback(message, running = false) {
  const el = $('command-feedback');
  if (!el) return;
  el.textContent = message;
  el.classList.toggle('running', !!running);
}

function setStatusBanner(message) {
  showNoData(true, message);
}

function setWarning(message) {
  showModeWarning(true, message);
}

function clearWarning() {
  showModeWarning(false);
}

function setReadyFeedback({ webglAvailable }) {
  if (!webglAvailable) {
    setFeedback('WebGL unavailable');
    setStatusBanner('MAP UNAVAILABLE: WebGL could not be initialized');
    setWarning('Map rendering unavailable on this device/browser');
    return;
  }

  setFeedback('Idle');
  clearWarning();
  if (state.payload) {
    showNoData(false);
  } else {
    setStatusBanner('NO DATA IN VIEW');
  }
}

function setLoading(isLoading, message = 'Loading dataset...') {
  if (isLoading) {
    setFeedback(message, true);
    return;
  }
  setReadyFeedback({ webglAvailable: !deckUnavailable });
}

function setErrorState(error, banner = 'FAILED TO LOAD RUN') {
  console.error('[LOAD] failed', error);
  setStatusBanner(banner);
  setFeedback('Load failed');
}

function showNoData(show, text = 'NO DATA IN VIEW') {
  const el = $('no-data-banner');
  if (!el) return;
  el.textContent = text;
  el.style.display = show ? 'block' : 'none';
}

function showModeWarning(show, text = '') {
  const el = $('mode-warning');
  if (!el) return;
  el.textContent = text;
  el.style.display = show ? 'block' : 'none';
}

function showWebGLUnavailable(error) {
  if (error) console.error('WebGL initialization failed', error);
  setReadyFeedback({ webglAvailable: false });
}

function formatRuntimeTimestamp(value) {
  if (value == null) return 'n/a';
  if (typeof value === 'number' && Number.isFinite(value)) {
    const dt = new Date(value * 1000);
    return Number.isNaN(dt.getTime()) ? String(value) : dt.toISOString().replace('T', ' ').replace('.000Z', ' UTC');
  }
  return String(value);
}

function updateRuntimeStatusPanel(status) {
  const summaryEl = $('runtime-summary');
  const hintEl = $('runtime-hint');
  if (!summaryEl) return;

  if (!status || typeof status !== 'object') {
    summaryEl.innerHTML = 'Runtime status unavailable';
    if (hintEl) hintEl.textContent = 'Unable to load runtime status.';
    return;
  }

  const collectorRunning = status.collector?.running === true ? 'yes' : status.collector?.running === false ? 'no' : 'unknown';
  const collectorPid = status.collector?.pid ?? 'n/a';
  const collectorUser = status.collector?.user || 'n/a';
  const collectorFilter = status.collector?.filter || 'none';
  const dbPath = status.db?.path || 'n/a';
  const sizeMb = status.db?.size_mb ?? 'n/a';
  const mode = status.db?.mode || 'unknown';
  const lastTs = formatRuntimeTimestamp(status.packets?.last_ts);
  const last5 = status.packets?.last_5min ?? 'n/a';
  const last1h = status.packets?.last_1h ?? 'n/a';

  summaryEl.innerHTML = [
    `Collector: ${collectorRunning} (pid ${collectorPid})`,
    `User: ${collectorUser}`,
    `Filter: ${collectorFilter}`,
    `DB: ${dbPath}`,
    `Size: ${sizeMb} MB`,
    `Mode: ${mode}`,
    `Last packet: ${lastTs}`,
    `Packets (5 min): ${last5}`,
    `Packets (1h): ${last1h}`,
  ].join('<br>');

  if (!hintEl) return;
  if (status.error) {
    hintEl.textContent = `Runtime status error: ${status.error}`;
    return;
  }

  if (typeof status.packets?.last_5min === 'number' && status.packets.last_5min > 0) {
    hintEl.textContent = 'Ingestion active in the last 5 minutes.';
  } else if (typeof status.packets?.last_1h === 'number' && status.packets.last_1h > 0) {
    hintEl.textContent = 'No packets in the last 5 minutes. Ingestion may be slow or intermittent.';
  } else {
    hintEl.textContent = 'No packets observed in the last hour. Ingestion may be inactive.';
  }
}

async function loadRuntimeStatus() {
  try {
    const status = await fetchRuntimeStatus();
    updateRuntimeStatusPanel(status);
  } catch (error) {
    updateRuntimeStatusPanel(null);
    const hintEl = $('runtime-hint');
    if (hintEl) hintEl.textContent = 'Error loading runtime status';
  }
}

function deriveRunExecuteErrorMessage(error) {
  const raw = typeof error?.message === 'string' ? error.message : '';

  const detailIndex = raw.indexOf(': ');
  const detailText = detailIndex >= 0 ? raw.slice(detailIndex + 2) : raw;

  try {
    const parsed = JSON.parse(detailText);
    const detail = Array.isArray(parsed) ? parsed : parsed?.detail;

    if (Array.isArray(detail)) {
      for (const item of detail) {
        const loc = Array.isArray(item?.loc) ? item.loc.join('.') : '';
        if (loc.includes('window_hours')) {
          return 'Invalid time window: maximum allowed is 168 hours';
        }
      }
    }

    if (typeof detail === 'string' && detail.trim()) {
      return detail.trim();
    }
  } catch (_) {
    // Keep fallback parsing below when detail is not JSON.
  }

  if (detailText.includes('window_hours')) {
    return 'Invalid time window: maximum allowed is 168 hours';
  }

  if (detailText && detailText !== raw) {
    return detailText;
  }

  return 'Run failed';
}

function getObservedDataHint(mode) {
  if (mode !== 'predicted') return '';
  return 'No observed data: this station has no igate receptions in the selected time window.';
}

function setStationValidationMessage(message = '', level = 'muted') {
  const el = $('station-validation-message');
  if (!el) return;
  if (!message) {
    el.textContent = '';
    el.style.display = 'none';
    el.style.color = 'var(--muted)';
    return;
  }

  el.textContent = message;
  el.style.display = 'block';
  el.style.color = level === 'error' ? 'var(--poor)' : level === 'limited' ? 'var(--limited)' : 'var(--muted)';
}

function confidenceBadge(type) {
  if (!type) return '';
  return `<span class="confidence-badge badge-${type}">${String(type).toUpperCase()}</span>`;
}

function rfDataBadge(modePayload) {
  const messages = Array.isArray(modePayload?.messages) ? modePayload.messages : [];
  if (!messages.length) return '';

  let rfCount = 0;
  for (const message of messages) {
    const signal = message?.signal && typeof message.signal === 'object' ? message.signal : null;
    const rssi = signal?.rssi;
    const snr = signal?.snr;
    if (rssi != null || snr != null) rfCount += 1;
  }

  const ratio = messages.length > 0 ? rfCount / messages.length : 0;
  if (ratio > 0.8) return '<span class="confidence-badge badge-rf-available">RF: AVAILABLE</span>';
  if (ratio >= 0.2) return '<span class="confidence-badge badge-rf-partial">RF: PARTIAL</span>';
  return '<span class="confidence-badge badge-rf-missing">RF: MISSING</span>';
}

function getEffectiveAnalysisMode(state, payload) {
  if (state.mode === MODES.PLANNING) return 'planning';
  if (payload?.analysis_mode === 'predicted') return 'predicted';
  return 'observed';
}

function getModeDisplay(mode) {
  switch (mode) {
    case 'planning':
      return {
        label: 'Planning view',
        badge: 'heuristic',
        color: '#94a3b8',
        title: 'Station placement planning based on spatial proximity, not RF observations',
      };
    case 'predicted':
      return {
        label: 'Predicted RF planning',
        badge: 'estimated',
        color: '#f59e0b',
        title: 'No observations found - using estimated planning mode',
      };
    default:
      return {
        label: 'Observed RF analysis',
        badge: 'observed',
        color: '#22c55e',
        title: 'Analysis based on recorded RF observations',
      };
  }
}

function applyModeClass(mode) {
  const root = document.body;
  if (!root) return;

  root.classList.remove('mode-observed', 'mode-estimated', 'mode-heuristic');

  if (mode === 'planning') {
    root.classList.add('mode-heuristic');
  } else if (mode === 'predicted') {
    root.classList.add('mode-estimated');
  } else {
    root.classList.add('mode-observed');
  }
}

function getKnownStationIds() {
  const ids = new Set();

  for (const row of Array.isArray(state.stationRegistry) ? state.stationRegistry : []) {
    const stationId = row?.station_id;
    if (typeof stationId === 'string' && stationId.trim()) ids.add(stationId.trim().toUpperCase());
  }

  for (const run of runsCache) {
    if (typeof run?.station === 'string' && run.station.trim()) ids.add(run.station.trim().toUpperCase());
    if (typeof run?.station_id === 'string' && run.station_id.trim()) ids.add(run.station_id.trim().toUpperCase());
  }

  const payloadStations = Array.isArray(state.payload?.stations) ? state.payload.stations : [];
  for (const station of payloadStations) {
    const candidate = station?.station_id || station?.id || station?.name;
    if (typeof candidate === 'string' && candidate.trim()) ids.add(candidate.trim().toUpperCase());
  }

  if (typeof state.payload?.reference_station_id === 'string' && state.payload.reference_station_id.trim()) {
    ids.add(state.payload.reference_station_id.trim().toUpperCase());
  }

  return ids;
}

function validateStationInput() {
  const input = $('station-input');
  if (!input) return { valid: false, stationId: '', knownStations: [] };

  const stationId = input.value.trim();
  const knownStations = Array.from(getKnownStationIds());

  if (!stationId) {
    setStationValidationMessage('');
    return { valid: false, stationId: '', knownStations };
  }

  const normalized = stationId.toUpperCase();
  const valid = knownStations.includes(normalized);

  if (!valid) {
    console.log(`Unknown station ID: ${stationId}`);
    setStationValidationMessage(
      'This station is not available in the station registry. Dataset stations and registered external stations can be analyzed. If you want to analyze a new station, add it to the station registry first.',
      'error',
    );
  } else {
    setStationValidationMessage('');
  }

  return { valid, stationId, knownStations };
}

function updateSelectedNodeDisplay() {
  const el = $('focus-node-summary');
  if (!el) return;

  if (state.selectedEdgeMeta && state.selection.edgeKey) {
    const edge = state.selectedEdgeMeta;
    const protocol = (edge.protocol || 'unknown').toUpperCase();
    const snrValue = Number(edge.avg_snr);
    const snr = Number.isFinite(snrValue) ? `${snrValue.toFixed(1)} dB` : 'n/a';
    const anomaly = Number(edge.anomaly_score || 0) > 0 ? 'yes' : 'no';
    const anomalies = Array.isArray(edge.anomalies) && edge.anomalies.length ? edge.anomalies.join(', ') : 'none';
    el.innerHTML = [
      `Edge: ${edge.emitter_id} -> ${edge.receiver_id}`,
      `Protocol: ${protocol}`,
      `Messages: ${edge.message_count || 0}`,
      `Avg SNR: ${snr}`,
      `RF anomaly: ${anomaly}`,
      `Anomalies: ${anomalies}`,
    ].join('<br>');
    return;
  }

  if (!state.selection.nodeId) {
    el.textContent = 'Focus node: None';
    return;
  }
  const type = state.selection.nodeType ? state.selection.nodeType.charAt(0).toUpperCase() + state.selection.nodeType.slice(1) : 'Node';
  el.textContent = `Focus node: ${type} ${state.selection.nodeId}`;
}

function updateDatasetSummary() {
  const el = $('dataset-summary');
  const modeEl = $('dataset-mode-summary');
  if (!el) return;
  if (!state.runId) {
    el.textContent = '-';
    if (modeEl) {
      modeEl.textContent = 'Analysis mode: -';
      modeEl.style.color = 'var(--muted)';
    }
    return;
  }
  const payload = state.payload;
  const generatedAt = payload?.meta?.generated_at || 'unknown time';
  const planningHintEl = $('planning-summary');
  el.textContent = `Run ID: ${state.runId} · ${generatedAt}`;

  if (!modeEl) return;

  const mode = getEffectiveAnalysisMode(state, payload);
  const { label, badge, color } = getModeDisplay(mode);
  modeEl.innerHTML = `Analysis mode: ${label} ${confidenceBadge(badge)}`;
  modeEl.style.color = color;

  if (planningHintEl) {
    const observedDataHint = getObservedDataHint(mode);
    if (observedDataHint) {
      planningHintEl.textContent = observedDataHint;
      planningHintEl.style.display = 'block';
    } else if (state.mode !== MODES.PLANNING) {
      planningHintEl.textContent = '';
      planningHintEl.style.display = 'none';
    }
  }
}

function updateReferenceSummary() {
  const el = $('reference-station-summary');
  if (!el) return;
  const station = state.referenceStation || '-';
  el.textContent = `Station: ${station}`;
}

function updatePlanningSummary(summary) {
  const el = $('planning-summary');
  if (!el) return;

  const observedDataHint = getObservedDataHint(getEffectiveAnalysisMode(state, state.payload));
  if (observedDataHint) {
    el.textContent = observedDataHint;
    el.style.display = 'block';
    return;
  }

  if (state.mode !== MODES.PLANNING || !summary) {
    el.textContent = '';
    el.style.display = 'none';
    return;
  }

  const lines = [
    `Nearby stations: ${summary.neighborCount}`,
  ];

  if (summary.closest) {
    lines.push(`Closest: ${summary.closest.station_id} (${Number(summary.closest.distance_km).toFixed(1)} km)`);
  }

  if (summary.avgDistance !== null && summary.avgDistance !== undefined) {
    lines.push(`Avg spacing: ${Number(summary.avgDistance).toFixed(1)} km`);
  }

  lines.push(`Placement score: ${Number(summary.score).toFixed(2)} (${summary.scoreLabel})`);

  el.textContent = lines.join('\n');
  el.style.display = 'block';
}

function updateAnalysisMode(payload) {
  const modeEl = $('mode');
  if (!modeEl) return;

  const mode = getEffectiveAnalysisMode(state, payload);
  const { label, badge, color, title } = getModeDisplay(mode);
  const rfBadge = state.mode === MODES.MESSAGES ? rfDataBadge(state.modePayload) : '';
  modeEl.innerHTML = `${label} ${confidenceBadge(badge)}${rfBadge ? ` ${rfBadge}` : ''}`;
  modeEl.style.color = color;
  modeEl.title = title;
}

function createViewContext() {
  return {
    payload: state.payload,
    modePayload: state.modePayload,
    selection: state.selection,
    uiFlags: state.filters,
    stationRegistry: state.stationRegistry,
    referenceStationId: state.referenceStation,
  };
}

function resetStateForNewRun() {
  state.payload = null;
  state.modePayload = null;
  state.selectedNodeMeta = null;

  state.selection.nodeId = null;
  state.selection.nodeType = null;
  state.selection.edgeKey = null;
  state.selection.focusLocked = false;

  state.referenceStation = null;
  state.selectedEdgeMeta = null;

  if (deckInstance) {
    deckInstance.setProps({ layers: [] });
  }

  if (deckUnavailable) {
    showWebGLUnavailable();
  } else {
    showNoData(false);
    clearWarning();
  }

  setStationValidationMessage('');
}

function resolveViewResult() {
  const context = createViewContext();
  switch (state.mode) {
    case MODES.RF:
      return buildRFViewLayers(context);
    case MODES.DIAGNOSTICS:
      return buildDiagnosticsLayers(context);
    case MODES.NETWORK:
      return buildNetworkViewLayers(context);
    case MODES.MESSAGES:
      return buildMessagesViewLayers(context);
    case MODES.PLANNING:
      return buildPlanningView(context);
    default:
      return {
        layers: [],
        nodeContext: { supported: true, reason: null, focusData: null },
      };
  }
}

function setTopBar(payload) {
  const gridMeta = payload?.metrics?.spatial_network_features?.grid_meta || {};
  $('context').textContent = payload?.meta?.region || payload?.reference_station_id || '-';
  $('last-data').textContent = payload?.meta?.generated_at || '-';
  $('window').textContent = gridMeta?.window_hours ? `${gridMeta.window_hours}h` : '-';
  const stationCount = Array.isArray(payload?.stations) ? payload.stations.length : 0;
  $('stations').textContent = `${stationCount} station${stationCount === 1 ? '' : 's'}`;
  updateAnalysisMode(payload);
}

function renderKpis(payload) {
  const network = payload?.network_summary || {};
  const features = payload?.metrics?.spatial_network_features || {};
  const isPredicted = payload?.analysis_mode === 'predicted';

  const coverageValue = network?.coverage_score ?? '-';
  const uniqueValue = Array.isArray(features?.unique_coverage) ? features.unique_coverage.length : '-';
  const gapsValue = Array.isArray(features?.blind_problematic)
    ? features.blind_problematic.length
    : (Array.isArray(features?.blind_zones_masked) ? features.blind_zones_masked.length : '-');
  const redundancyValue = Number.isFinite(Number(features?.shared_overlap_ratio_active))
    ? `${Math.round(Number(features.shared_overlap_ratio_active) * 100)}%`
    : '-';

  $('kpi-network').innerHTML = `
    <div class="line"><span>Coverage (estimated)</span><strong>${coverageValue}</strong></div>
    <div class="line"><span>Analyzed locations</span><strong>${uniqueValue}</strong></div>
    <div class="line"><span>Uncovered zones</span><strong>${gapsValue}</strong></div>
    <div class="line"><span>Network redundancy</span><strong>${redundancyValue}</strong></div>
  `;

  const summaryEl = $('network-summary-text');
  if (summaryEl) {
    summaryEl.textContent = isPredicted
      ? 'Estimated network coverage based on station positions.'
      : 'Network is partially covered. Several areas lack signal.';
  }
}

function renderDecision(payload) {
  const diagnosis = payload?.intelligence?.decision || payload?.decision || {};
  const effectiveMode = getEffectiveAnalysisMode(state, payload);
  const isPredicted = effectiveMode === 'predicted';
  const isPlanning = effectiveMode === 'planning';
  const { badge } = getModeDisplay(effectiveMode);
  const intelligenceBadgeEl = $('intelligence-confidence');
  if (intelligenceBadgeEl) intelligenceBadgeEl.innerHTML = confidenceBadge(badge);
  const status = typeof diagnosis?.status === 'string' ? diagnosis.status.toUpperCase() : '-';
  $('status').textContent = status;
  $('status').className = status === 'GOOD' ? 'badge-good' : status === 'POOR' ? 'badge-poor' : 'badge-limited';
  $('issue-label').textContent = isPlanning ? 'Potential issue' : (isPredicted ? 'Potential issue' : 'Issue');
  $('cause-label').textContent = isPlanning ? 'Possible cause' : (isPredicted ? 'Possible cause' : 'Cause');
  $('action-label').textContent = isPlanning ? 'Suggested action' : (isPredicted ? 'Suggested action' : 'Action');
  $('issue').textContent = diagnosis?.issue ?? '-';
  $('cause').textContent = diagnosis?.cause ?? '-';
  $('action').textContent = diagnosis?.action ?? '-';
  $('severity').textContent = diagnosis?.severity ?? '-';
}

function renderLegend() {
  const el = $('field-legend-body');
  if (!el) return;

  const rows = [];
  if (state.mode === MODES.PLANNING) {
    rows.push('<div class="legend-row"><span class="sw dot" style="background:#f59e0b"></span>Candidate station</div>');
    rows.push('<div class="legend-row"><span class="sw dot" style="background:#22c55e"></span>Nearby station</div>');
    rows.push('<div class="legend-row"><span class="sw line" style="background:#cbd5e1"></span>Neighbor link</div>');
  } else if (state.mode === MODES.MESSAGES) {
    rows.push('<div class="legend-row"><span class="sw dot" style="background:#7dd3fc"></span>Receiver</div>');
    rows.push('<div class="legend-row"><span class="sw dot" style="background:#22c55e"></span>Station</div>');
    rows.push('<div class="legend-row"><span class="sw dot" style="background:#fb923c"></span>Emitter</div>');
    if (state.filters.showNetworkEdges) {
      rows.push('<div class="legend-row"><span class="sw line" style="background:#cbd5e1"></span>Message path</div>');
    }
    rows.push('<div class="legend-row" style="color: var(--muted);">RF strength based on SNR</div>');
    rows.push('<div class="legend-row" style="color: var(--muted);">Low-quality RF links highlighted</div>');
  } else {
    rows.push('<div class="legend-row"><span class="sw dot" style="background:#22c55e"></span>Station</div>');
    if (state.filters.showCoverage) rows.push('<div class="legend-row"><span class="sw circle" style="background:rgba(125,211,252,0.35)"></span>Signal coverage radius</div>');
    if (state.filters.showCriticalObservations) rows.push('<div class="legend-row"><span class="sw dot" style="background:#7dd3fc"></span>Receiver</div>');
    if (state.filters.showSignalLoss) rows.push('<div class="legend-row"><span class="sw" style="background:rgba(239,68,68,0.45)"></span>Coverage gap area</div>');
    if (state.filters.showModelValidation) rows.push('<div class="legend-row"><span class="sw dot" style="background:#ef4444"></span>Model validation point</div>');
  }

  el.innerHTML = rows.join('');
}

function setSelectedNode(nodeId, nodeType, nodeMeta = null) {
  state.selection.nodeId = nodeId || null;
  state.selection.nodeType = nodeType || null;
  state.selection.focusLocked = Boolean(nodeId);
  state.selectedNodeMeta = nodeMeta || null;
  updateSelectedNodeDisplay();
  refreshView();
}

function setSelectedEdge(edge) {
  if (!edge) return;
  state.selection.nodeId = null;
  state.selection.nodeType = null;
  state.selection.edgeKey = `${edge.emitter_id}->${edge.receiver_id}`;
  state.selection.focusLocked = true;
  state.selectedNodeMeta = null;
  state.selectedEdgeMeta = { ...edge };
  updateSelectedNodeDisplay();
  refreshView();
}

function clearSelectedNode() {
  state.selection.nodeId = null;
  state.selection.nodeType = null;
  state.selection.edgeKey = null;
  state.selection.focusLocked = false;
  state.selectedNodeMeta = null;
  state.selectedEdgeMeta = null;
  updateSelectedNodeDisplay();
  refreshView();
}

function handleMapClick({ object, layer }) {
  if (!object || !layer?.id) {
    clearSelectedNode();
    return;
  }

  if (layer.id === 'messages-network-edges' && object.emitter_id && object.receiver_id) {
    setSelectedEdge(object);
    return;
  }

  if ((layer.id === 'rf-stations' || layer.id === 'messages-stations') && object.station_id) {
    setSelectedNode(object.station_id, 'station', { lat: Number(object.lat), lon: Number(object.lon ?? object.lng) });
    return;
  }

  if (layer.id === 'messages-network-nodes' && object.receiver_id) {
    setSelectedNode(object.receiver_id, 'receiver', { lat: Number(object.lat), lon: Number(object.lon) });
    return;
  }

  if (layer.id === 'messages-emitters' && object.emitter_id) {
    setSelectedNode(object.emitter_id, 'emitter', { lat: Number(object.lat), lon: Number(object.lon) });
    return;
  }

  if ((layer.id === 'rf-signal-loss' || layer.id === 'rf-critical-observations' || layer.id === 'rf-coverage')
    && Number.isFinite(Number(object.lat))
    && Number.isFinite(Number(object.lon))) {
    const nodeId = `${Number(object.lat).toFixed(6)}|${Number(object.lon).toFixed(6)}`;
    setSelectedNode(nodeId, 'zone', { lat: Number(object.lat), lon: Number(object.lon) });
    return;
  }

  clearSelectedNode();
}

function getTooltip({ object, layer }) {
  if (!object) return null;

  if (layer?.id === 'planning-candidate') {
    return {
      text:
        `Candidate station
` +
        `ID: ${object.station_id || 'N/A'}
` +
        `Lat: ${Number(object.lat).toFixed(5)}
` +
        `Lon: ${Number(object.lon).toFixed(5)}`,
    };
  }

  if (layer?.id === 'planning-neighbors') {
    return {
      text:
        `Known station
` +
        `ID: ${object.station_id}
` +
        `Distance: ${Number(object.distance_km).toFixed(1)} km`,
    };
  }

  if (layer?.id === 'messages-network-nodes') {
    const inferred = object.inferred_messages_count > 0 ? 'yes' : 'no';
    return {
      text:
        `Receiver\n` +
        `ID: ${object.receiver_id}\n` +
        `Messages received: ${object.message_count}\n` +
        `Unique emitters: ${object.unique_emitters_count}\n` +
        `Receiver position inferred: ${inferred}\n` +
        `Protocol: unknown`,
    };
  }

  if (layer?.id === 'messages-stations' || layer?.id === 'rf-stations') {
    return {
      text:
        `Station\n` +
        `ID: ${object.station_id || 'unknown'}\n` +
        `Status: active`,
    };
  }

  if (layer?.id === 'messages-emitters') {
    return {
      text:
        `Emitter\n` +
        `ID: ${object.emitter_id}\n` +
        `Observed paths: ${object.path_count}\n` +
        `Protocol: unknown`,
    };
  }

  if (layer?.id === 'messages-network-edges') {
      const inferredRatio = Number(object.inferred_ratio || 0);
      const inferredPercent = Math.round(inferredRatio * 100);
      const protocol = (object.protocol || 'unknown').toUpperCase();
      const snrValue = Number(object.avg_snr);
      const snr = Number.isFinite(snrValue) ? `${snrValue.toFixed(1)} dB` : 'n/a';
      const anomalyScore = Number(object.anomaly_score || 0);
      const anomaly = anomalyScore > 0;
      const anomalyList = Array.isArray(object.anomalies) && object.anomalies.length ? object.anomalies.join(', ') : 'none';
      return {
        text:
          `Message path
` +
          `Direction: ${object.emitter_id} -> ${object.receiver_id}
` +
          `Messages: ${object.message_count}
` +
          `Receiver position inferred: ${inferredPercent > 0 ? `${inferredPercent}%` : 'no'}
` +
          `Protocol: ${protocol}
` +
          `Avg SNR: ${snr}
` +
          `RF anomaly: ${anomaly ? 'yes' : 'no'}
` +
          `Anomalies: ${anomalyList}`,
      };
    }

  if (layer?.id === 'rf-coverage') {
    return {
      text:
        `Zone\n` +
        `Type: Signal coverage radius\n` +
        `Coverage value: ${Number(object.value).toFixed(3)}`,
    };
  }

  if (layer?.id === 'rf-critical-observations') {
    return {
      text:
        `Receiver\n` +
        `Type: Critical observation\n` +
        `Coverage value: ${Number(object.value).toFixed(3)}`,
    };
  }

  if (layer?.id === 'rf-signal-loss') {
    return {
      text:
        `Zone\n` +
        `Type: Coverage gap area\n` +
        `Severity value: ${Number(object.value || 1).toFixed(3)}`,
    };
  }

  if (layer?.id === 'rf-model-validation') {
    return {
      text:
        `Zone\n` +
        `Type: Model validation\n` +
        `Status: sampled`,
    };
  }

  if (object.station_id) return { text: `Station\nID: ${object.station_id}` };
  if (object.receiver_id) return { text: `Receiver\nID: ${object.receiver_id}` };
  if (Number.isFinite(Number(object.value))) return { text: `Zone\nValue: ${Number(object.value).toFixed(3)}` };

  return null;
}

function ensureDeck() {
  if (deckInstance) return true;
  if (deckUnavailable) return false;

  try {
    if (typeof deck === 'undefined') throw new Error('deck.gl not loaded');

    const DeckCtor = deck.DeckGL || deck.Deck;
    if (!DeckCtor) throw new Error('Deck constructor unavailable');

    const config = {
      container: 'map',
      views: [new deck.MapView({ repeat: true })],
      mapStyle: BASEMAP_STYLE,
      mapLib: typeof maplibregl !== 'undefined' ? maplibregl : undefined,
      initialViewState: state.viewState,
      controller: true,
      layers: [],
      getTooltip,
      onClick: handleMapClick,
      onError: (error) => {
        console.warn('[Deck] runtime error', error);
      },
    };

    try {
      deckInstance = DeckCtor === deck.DeckGL
        ? new DeckCtor(config)
        : new DeckCtor({ ...config, parent: $('map') });
    } catch (error) {
      console.warn('[WebGL] Deck constructor failed', error);
      throw error;
    }

    return true;
  } catch (error) {
    deckUnavailable = true;
    showWebGLUnavailable(error);
    return false;
  }
}

function refreshView() {
  const hasDeck = ensureDeck();

  const viewResult = resolveViewResult() || {
    layers: [],
    nodeContext: { supported: true, reason: null, focusData: null },
  };
  const layers = Array.isArray(viewResult.layers) ? viewResult.layers : [];
  const nodeContext = viewResult.nodeContext || { supported: true, reason: null, focusData: null };

  const stationCount = Array.isArray(state.payload?.stations) ? state.payload.stations.length : 0;
  const limitedNetworkView = state.mode === MODES.MESSAGES && stationCount <= 1;
  const unsupportedText = !nodeContext.supported
    ? `NODE NOT APPLICABLE IN CURRENT MODE${nodeContext.reason ? ` — ${nodeContext.reason}` : ''}`
    : '';
  const modeBanner = unsupportedText || (limitedNetworkView ? 'Network view limited (single-station dataset)' : '');

  if (deckUnavailable) {
    showWebGLUnavailable();
  } else {
    showModeWarning(Boolean(modeBanner), modeBanner);
  }

  console.log('[STATE]', {
    loadToken: state.loadToken,
    runId: state.runId,
    mode: state.mode,
    referenceStation: state.referenceStation,
    payloadRun: state.payload?.run_id,
    hasModePayload: !!state.modePayload,
    selectedNode: state.selection.nodeId,
  });

  if (hasDeck && deckInstance) {
    deckInstance.setProps({ layers, initialViewState: state.viewState });
  }
  if (deckUnavailable) {
    setReadyFeedback({ webglAvailable: false });
  } else if (!state.payload) {
    setStatusBanner('NO DATA IN VIEW');
  } else {
    showNoData(false);
  }

  if (state.payload) {
    const effectiveMode = getEffectiveAnalysisMode(state, state.payload);
    applyModeClass(effectiveMode);
    setTopBar(state.payload);
    renderKpis(state.payload);
    renderDecision(state.payload);
    renderLegend();
  } else {
    applyModeClass('observed');
  }

  updateDatasetSummary();
  updateReferenceSummary();
  updatePlanningSummary(viewResult.summary || null);
  updateSelectedNodeDisplay();
}

async function loadRun(runId) {
  const token = ++state.loadToken;
  const mode = state.mode;

  resetStateForNewRun();

  state.runId = runId;
  state.selection.runId = runId;

  console.log('[LOAD] start', { runId, mode });
  setLoading(true, 'Loading dataset...');

  try {
    const payload = await fetchRunPayload(runId);
    if (token !== state.loadToken) return;

    const modePayload = await fetchModePayload(runId, mode);
    if (token !== state.loadToken) return;
    if (mode !== state.mode) return;

    state.payload = payload;
    state.modePayload = modePayload;

    state.referenceStation = payload?.reference_station_id || null;

    refreshView();
    console.log('[LOAD] done', { runId, mode });
  } catch (error) {
    if (token !== state.loadToken) return;
    setErrorState(error, 'FAILED TO LOAD RUN');
    refreshView();
  } finally {
    if (token === state.loadToken) setLoading(false);
  }
}

async function setMode(mode) {
  state.mode = mode;
  state.selection.mode = mode;

  bindLayerControls();
  bindModeControls();
  renderLegend();

  const token = ++state.loadToken;
  console.log('[LOAD] start', { runId: state.runId, mode });
  setLoading(true, `Loading ${mode}...`);

  try {
    if (state.runId) {
      const modePayload = await fetchModePayload(state.runId, state.mode);
      if (token !== state.loadToken) return;
      state.modePayload = modePayload;
    }

    refreshView();
    console.log('[LOAD] done', { runId: state.runId, mode });
  } catch (error) {
    if (token !== state.loadToken) return;
    state.modePayload = null;
    setErrorState(error, 'MODE PAYLOAD UNAVAILABLE');
    refreshView();
  } finally {
    if (token === state.loadToken) setLoading(false);
  }
}

function selectedRunId() {
  return $('run-list')?.value || state.runId;
}

function bindLayerControls() {
  const root = $('layer-controls');
  if (!root) return;

  const controls = state.mode === MODES.MESSAGES
    ? [
        ['showNetworkEdges', 'Show network edges'],
      ]
    : state.mode === MODES.PLANNING
      ? []
      : [
          ['showCoverage', 'Display Signal Field'],
          ['showCriticalObservations', 'Display Critical Observations'],
          ['showSignalLoss', 'Display Signal Loss Areas'],
          ['showModelValidation', 'Display Model Validation'],
        ];

  root.innerHTML = '';
  for (const [key, label] of controls) {
    const row = document.createElement('div');
    row.className = 'toggle';
    row.innerHTML = `<span>${label}</span><input type="checkbox" ${state.filters[key] ? 'checked' : ''} />`;
    row.querySelector('input').addEventListener('change', (e) => {
      state.filters[key] = Boolean(e.target.checked);
      refreshView();
    });
    root.appendChild(row);
  }
}

function bindModeControls() {
  const root = $('mode-controls');
  if (!root) return;
  root.innerHTML = '';

  const modes = [
    [MODES.RF, 'RF Field'],
    [MODES.DIAGNOSTICS, 'Diagnostics'],
    [MODES.NETWORK, 'Network'],
    [MODES.MESSAGES, 'Messages'],
    [MODES.PLANNING, 'Station Planning'],
  ];

  for (const [mode, label] of modes) {
    const btn = document.createElement('button');
    btn.className = `cmd ${state.mode === mode ? 'primary' : 'ghost'}`;
    btn.innerHTML = `<span class="cmd-label">${label}</span><span class="cmd-desc">Mode view</span>`;
    btn.addEventListener('click', async () => {
      await setMode(mode);
    });
    root.appendChild(btn);
  }
}

function populateRuns(runs) {
  const select = $('run-list');
  if (!select) return;
  select.innerHTML = '';

  runs.forEach((run) => {
    const option = document.createElement('option');
    option.value = run.run_id;
    option.textContent = `${run.station || 'UNKNOWN'} · ${run.run_id}`;
    select.appendChild(option);
  });

  if (runs.length) {
    state.runId = runs[0].run_id;
    state.selection.runId = runs[0].run_id;
    select.value = state.runId;
  }
}

function bindActions() {
  $('station-input')?.addEventListener('input', () => {
    validateStationInput();
    updateReferenceSummary();
  });

  $('btn-load-run')?.addEventListener('click', async () => {
    try {
      const runId = selectedRunId();
      if (!runId) return;
      await loadRun(runId);
    } catch (error) {
      console.error(error);
      showNoData(true, 'FAILED TO LOAD RUN');
      setFeedback('Load failed');
    }
  });

  $('btn-execute-run')?.addEventListener('click', async () => {
    const stationCheck = validateStationInput();
    if (!stationCheck.valid) {
      showModeWarning(
        true,
        'This station is not available in the station registry. Dataset stations and registered external stations can be analyzed.',
      );
      setFeedback('Station unavailable');
      return;
    }

    console.log('[LOAD] start', { station: stationCheck.stationId, mode: 'execute-run' });
    setLoading(true, 'Running RF analysis...');

    try {
      const result = await executeRun({
        station: stationCheck.stationId,
        windowHours: Number($('window-input')?.value || 6),
        endOffsetHours: Number($('offset-input')?.value || 0),
      });
      runsCache = await fetchRuns();
      populateRuns(runsCache);
      if (result?.run_id) {
        $('run-list').value = result.run_id;
        await loadRun(result.run_id);
      }
      console.log('[LOAD] done', { station: stationCheck.stationId, mode: 'execute-run' });
    } catch (error) {
      const message = deriveRunExecuteErrorMessage(error);
      setErrorState(error, 'RUN UNAVAILABLE');
      showModeWarning(true, message);
      setStationValidationMessage(message, 'error');
      setFeedback('Run unavailable');
    } finally {
      setLoading(false);
    }
  });

  $('btn-reset-view')?.addEventListener('click', () => {
    state.viewState = { longitude: 7.273, latitude: 47.336, zoom: 9.5, pitch: 0, bearing: 0 };
    refreshView();
  });

  $('btn-focus-problem')?.addEventListener('click', () => {
    const rows = state.payload?.metrics?.spatial_network_features?.blind_problematic;
    const first = Array.isArray(rows) && rows.length ? rows[0] : null;
    if (first) {
      state.viewState = { longitude: Number(first.lon), latitude: Number(first.lat), zoom: 11.5, pitch: 0, bearing: 0 };
      refreshView();
    }
  });

  $('btn-clear-node-focus')?.addEventListener('click', () => {
    clearSelectedNode();
  });
}

export async function bootstrap() {
  setFeedback('Initializing...', true);
  installWebGLRejectionHandler();
  try {
    ensureDeck();
  } catch (error) {
    console.warn('[WebGL] Deck initialization failed (handled)', error);
    showWebGLUnavailable(error);
  }
  bindActions();
  bindModeControls();
  bindLayerControls();
  updateDatasetSummary();
  updateReferenceSummary();
  updateSelectedNodeDisplay();
  await loadRuntimeStatus();
  if (runtimeRefreshHandle == null) {
    runtimeRefreshHandle = window.setInterval(loadRuntimeStatus, 10000);
  }

  try {
    state.stationRegistry = await fetchStations();
    runsCache = await fetchRuns();
    populateRuns(runsCache);
    validateStationInput();

    if (!runsCache.length) {
      showNoData(true, 'NO RUNS AVAILABLE');
      setFeedback('No runs available');
      refreshView();
      return;
    }

    await loadRun(runsCache[0].run_id);
  } catch (error) {
    console.error(error);
    showNoData(true, 'API UNAVAILABLE');
    setFeedback('API unavailable');
    refreshView();
  }
}
