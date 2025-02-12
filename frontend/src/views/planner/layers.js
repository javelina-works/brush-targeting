import L from "leaflet";

// 🔹 Store layers in an object (initialized as empty)
const mapLayers = {};

// 🔹 Layer Factory: Predefines layer types
export const layerFactory = {
    region_contour: () => L.geoJSON(null, {
        style: { color: "blue", weight: 2, fillOpacity: 0.05 },
    }),
    approved_targets: () => L.geoJSON(null, {
        pointToLayer: (feature, latlng) => L.circleMarker(latlng, { color: "blue", radius: 5 }),
        onEachFeature: (feature, layer) => {
            layer.bindPopup(`<b>Approved Target</b><br>ID: ${feature.properties.id}`);
            layer.on("click", () => moveFeature(feature, "approved_targets", "removed_targets"));
        },
    }),
    removed_targets: () => L.geoJSON(null, {
        pointToLayer: (feature, latlng) => L.circleMarker(latlng, { color: "red", radius: 5 }),
        onEachFeature: (feature, layer) => {
            layer.bindPopup(`<b>Removed Target</b><br>ID: ${feature.properties.id}`);
            layer.on("click", () => moveFeature(feature, "removed_targets", "approved_targets"));
        },
    }),
    voronoi_cells: () => L.geoJSON(null, {
        style: { color: "purple", weight: 1, fill: false, fillOpacity: 0.1, },
    }),
    depot_locations: () => L.geoJSON(null, {
        pointToLayer: (feature, latlng) => L.circleMarker(latlng, { color: "green", radius: 6 }),
        onEachFeature: (feature, layer) => {
            layer.bindPopup(`<b>Depot</b><br>ID: ${feature.properties.id}`);
        },
    }),
    default: () => L.geoJSON(null, {
        pointToLayer: (feature, latlng) => L.circleMarker(latlng, { color: "gray", radius: 5 }),
        onEachFeature: (feature, layer) => {
            layer.bindPopup(`<b>Unknown Layer</b><br>ID: ${feature.properties?.id || "N/A"}`);
        },
    }),
};

// 🔹 Initialize Layers: Prepares layers before data is fetched
export function initializeLayers(map) {
    Object.keys(layerFactory).forEach((key) => {
        mapLayers[key] = layerFactory[key]();
        mapLayers[key].addTo(map); // Attach to map immediately (even empty)
    });
}

// 🔹 Update Layer Data: Populates a layer without replacing it
export function updateLayerData(layerKey, geojson) {
    if (mapLayers[layerKey]) {
        mapLayers[layerKey].clearLayers(); // Remove old data
        mapLayers[layerKey].addData(JSON.parse(geojson)); // Add new data

    } else {
        console.warn(`Layer "${layerKey}" not found.`);
    }
}

// 🔹 Get a Specific Layer
export function getLayer(layerKey) {
    return mapLayers[layerKey] || null;
}

// 🔹 Move Feature Between Layers (Example: Approved → Removed Targets)
export function moveFeature(feature, fromLayer, toLayer) {
    if (mapLayers[fromLayer]) {
        mapLayers[fromLayer].removeLayer(feature);
    }
    if (mapLayers[toLayer]) {
        mapLayers[toLayer].addData(feature);
    }
}
