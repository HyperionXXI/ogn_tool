export async function fetchRuns() {
  const res = await fetch('/api/runs');
  if (!res.ok) throw new Error(`Failed to fetch runs (${res.status})`);
  return res.json();
}

export async function fetchRunPayload(runId) {
  const res = await fetch(`/api/runs/${encodeURIComponent(runId)}`);
  if (!res.ok) throw new Error(`Failed to fetch run payload (${res.status})`);
  return res.json();
}

export async function fetchModePayload(runId, mode) {
  const endpointByMode = {
    rf: 'rf-field',
    diagnostics: 'directional',
    network: 'visibility',
    messages: 'messages_v2',
    planning: null,
  };

  const endpoint = endpointByMode[mode];
  if (!endpoint) return {};

  const res = await fetch(`/analysis/${encodeURIComponent(runId)}/${endpoint}`);
  if (!res.ok) throw new Error(`Failed to fetch mode payload (${res.status})`);
  return res.json();
}

export async function executeRun({ station, windowHours, endOffsetHours }) {
  const res = await fetch('/api/runs/execute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      station,
      window_hours: windowHours,
      end_offset_hours: endOffsetHours,
    }),
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Run execution failed (${res.status}): ${detail}`);
  }
  return res.json();
}

export async function fetchStations() {
  const res = await fetch('/api/stations');
  if (!res.ok) throw new Error(`Failed to fetch stations (${res.status})`);
  return res.json();
}

export async function fetchRuntimeStatus() {
  const res = await fetch('/api/runtime/status');
  if (!res.ok) throw new Error(`Failed to fetch runtime status (${res.status})`);
  return res.json();
}
