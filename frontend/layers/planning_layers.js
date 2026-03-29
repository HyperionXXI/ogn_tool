
function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

const supportsDashed =
  typeof deck !== 'undefined' &&
  typeof deck.PathStyleExtension !== 'undefined';

if (!supportsDashed) {
  console.warn('[planning] PathStyleExtension not available -> using fallback solid lines');
}

const pathExtensions = supportsDashed
  ? [new deck.PathStyleExtension({ dash: true })]
  : [];

const lineStyle = supportsDashed
  ? {
      getDashArray: () => [2, 2],
      dashJustified: true,
    }
  : {};

const fallbackStyle = !supportsDashed
  ? {
      getWidth: () => 1,
      opacity: 0.35,
    }
  : {};

export function buildPlanningLayers(viewModel, _state) {
  const candidate = viewModel?.candidate_station;
  const planning = viewModel?.planning || {};
  const neighbors = Array.isArray(planning?.nearby_stations) ? planning.nearby_stations : [];

  if (!candidate || !Number.isFinite(Number(candidate?.lat)) || !Number.isFinite(Number(candidate?.lon))) {
    return [];
  }

  const candidateHaloLayer = new deck.ScatterplotLayer({
    id: 'planning-candidate-halo',
    data: [candidate],
    getPosition: (d) => [Number(d.lon), Number(d.lat)],
    getFillColor: [245, 158, 11, 42],
    getRadius: 2200,
    radiusUnits: 'meters',
    pickable: false,
    stroked: false,
  });

  const candidateLayer = new deck.ScatterplotLayer({
    id: 'planning-candidate',
    data: [candidate],
    getPosition: (d) => [Number(d.lon), Number(d.lat)],
    getFillColor: [245, 158, 11, 245],
    getLineColor: [255, 247, 237, 255],
    getRadius: 1450,
    radiusUnits: 'meters',
    radiusMinPixels: 10,
    lineWidthMinPixels: 2,
    stroked: true,
    pickable: true,
  });

  const neighborLayer = new deck.ScatterplotLayer({
    id: 'planning-neighbors',
    data: neighbors,
    getPosition: (d) => [Number(d.lon), Number(d.lat)],
    getFillColor: [34, 197, 94, 188],
    getLineColor: [240, 253, 244, 255],
    getRadius: 520,
    radiusUnits: 'meters',
    radiusMinPixels: 6,
    lineWidthMinPixels: 1.5,
    stroked: true,
    pickable: true,
  });

  const linkData = neighbors
    .filter((n) => Number.isFinite(Number(n?.lat)) && Number.isFinite(Number(n?.lon)))
    .map((n) => ({
      path: [[Number(candidate.lon), Number(candidate.lat)], [Number(n.lon), Number(n.lat)]],
      distance_km: Number(n.distance_km || 0),
    }));

  const linksLayer = new deck.PathLayer({
    id: 'planning-links',
    data: linkData,
    getPath: (d) => d.path,
    getColor: [148, 163, 184, 150],
    widthUnits: 'pixels',
    getWidth: supportsDashed ? 1 : 1,
    opacity: supportsDashed ? 0.6 : 0.35,
    ...lineStyle,
    ...fallbackStyle,
    extensions: pathExtensions,
    pickable: false,
  });

  return [linksLayer, neighborLayer, candidateHaloLayer, candidateLayer].filter(Boolean);
}
