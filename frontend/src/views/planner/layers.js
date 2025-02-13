import L from "leaflet";

// 🔹 Store layers in an object (initialized as empty)
const mapLayers = {};

// 🔹 Layer Factory: Predefines layer types
export const layerFactory = {
    region_contour: () => L.geoJSON(null, {
        style: { color: "blue", weight: 2, fill: false, fillOpacity: 0.05 },
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
    depot_points: () => L.geoJSON(null, {
        pointToLayer: (feature, latlng) => {
            const radius = feature.properties.depot_radius || 500; // Default if missing
            const radius_circle = L.circle(latlng, { 
                radius: radius, 
                color: "green",
                // fillOpacity: 0.02,
                fill: false,
            });
            // const marker = L.circleMarker(latlng, {radius: 3, color: "black", draggable: true, pmIgnore: false});
            // const marker = L.circle(latlng, {radius: 3, color: "black", draggable: true, pmIgnore: false});
            const marker = L.marker(latlng, {
                draggable: true,
                icon: L.divIcon({
                    className: "depot-center",
                    html: "●", // Unicode dot
                    iconSize: [10, 10], // Small dot size
                    iconAnchor: [5, 5] // Center alignment
                })
            });
            
            // 🔹 Keep both elements in sync while dragging
            marker.on("drag", (event) => {
                const newLatLng = event.target.getLatLng();
                radius_circle.setLatLng(newLatLng); // Move the circle with the marker
            });

            return marker;

            // radius_circle.on("dragstart", () => {
            //     marker.dragging.enable(); // Allow dragging both
            // });

            // radius_circle.on("drag", (event) => {
            //     const newLatLng = event.target.getLatLng();
            //     marker.setLatLng(newLatLng); // Move the marker with the circle
            // });

            // return L.layerGroup([radius_circle, marker]);
        },
        onEachFeature: (feature, layer) => {
            layer.bindPopup(`<b>Depot</b><br>ID: ${feature.properties.id}<br>Radius: ${feature.properties.depot_radius || 500}m`);
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

        

        // 🚫 Disable editing for region & voronoi
        if (key === "region_contour" || key === "voronoi_cells") {
            mapLayers[key].eachLayer((layer) => {
                if (layer.pm) {
                    layer.pm.setOptions({ editable: false, draggable: false, removable: false });
                }
            });
        }
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
