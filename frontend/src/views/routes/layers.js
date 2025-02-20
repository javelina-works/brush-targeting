import L, { circle } from "leaflet";
import { geoJSON } from "leaflet";

// 🔹 Store layers in an object (initialized as empty)
const mapLayers = {};

// 🔹 Layer Factory: Predefines layer types
export const layerFactory = {
    region_contour: () => L.geoJSON(null, {
        style: { color: "blue", weight: 2, fill: false, fillOpacity: 0.05 },
    }),

    targets: () => L.geoJSON(null, {
        pointToLayer: (feature, latlng) => L.circleMarker(latlng, { color: "blue", radius: 5 }),
        onEachFeature: (feature, layer) => {
            layer.bindPopup(`<b>Detected Target</b><br>ID: ${feature.properties.id}`);
        },
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
                radius: radius, color: "green", weight: 1, fill: false,
                pmIgnore: false,
            });
            // radius_circle.properties = { ...feature.properties };
            // radius_circle.feature = feature;

            const marker = L.marker(latlng, {
                properties: { ...feature.properties },
                draggable: true,
                icon: L.divIcon({
                    className: "depot-center",
                    html: "●", // Unicode dot
                    iconSize: [10, 10], // Small dot size
                    iconAnchor: [5, 5] // Center alignment
                })
            });
            marker.properties = { ...feature.properties }
            marker.feature = feature;

            // 🔹 Keep both elements in sync while dragging
            marker.on("drag", (event) => {
                const newLatLng = event.target.getLatLng();
                radius_circle.setLatLng(newLatLng); // Move the circle with the marker
            });

            marker.on("dragend", (event) => {
                const newLatLng = event.target.getLatLng();
                console.log("Marker moved: ", newLatLng);
                radius_circle.setLatLng(newLatLng); // Move the circle with the marker
                marker.setLatLng(newLatLng);
                feature.geometry.coordinates = [newLatLng.lng, newLatLng.lat];
            });

            const depotGroup = L.layerGroup([radius_circle, marker]);
            marker.addTo(depotGroup);
            radius_circle.addTo(depotGroup);

            // depotGroup.pm.setOptions({syncLayersOnDrag: true});
            // depotGroup.properties = { ...feature.properties };
            // depotGroup.feature = feature;
            
            // console.log("Depot props: ", depotGroup.properties);
            // console.log("Circle props: ", radius_circle.properties);
            // console.log("Marker props: ", marker.properties);
            return depotGroup;
        },
        onEachFeature: (feature, layer) => {
            layer.bindPopup(`<b>Depot</b><br>ID: ${feature.properties.id}<br>Radius: ${feature.properties.depot_radius || 500}m`);
        },
    }),

    micro_routes: () => {
        function getRandomColor() {
            return `#${Math.floor(Math.random()*16777215).toString(16)}`; // Random hex color
        }
        const routes_geojson = L.geoJSON(null, {
            style: feature => ({ 
                color: getRandomColor(), // Random hex color
                weight: 2,
                opacity: 1,
                dashArray: (3,4),
                fill: false, 
            }),
            onEachFeature: (feature, layer) => {
                layer.on({
                    mouseover: (e) => {
                        e.target.setStyle({
                            // color: "green",
                            weight: 5, // Thicker when hovered
                            dashArray: "", // Solid line when hovered
                        });
                    },
                    mouseout: (e) => {
                        e.target.setStyle({
                            weight: 2,
                            dashArray: (3,4),
                        })
                        // routes_geojson.resetStyle(e.target); // Reset to default style
                    }
                });
            }
        });
        return routes_geojson;
    },

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
    console.log("Updating layer: ", layerKey);
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

export function getAllLayers() {
    // return mapLayers;
    const returnLayers = {};

    Object.keys(mapLayers).forEach((layerKey) => {
        const layer = mapLayers[layerKey];

        // 🔹 Extract GeoJSON, but only store the marker (not the radius circle)
        if (layerKey === "depot_points") {
            // Iterate through each depot layer group
            layer.eachLayer((group) => {
                // 🟢 Ensure we only extract the marker (not the circle)
                group.eachLayer((subLayer) => {
                    if (!subLayer.feature) {
                        // console.log("Removing layer", subLayer);
                        group.removeLayer(subLayer); // Remove layer with no features to prevent duplication
                    }
                });
            });
        }
        returnLayers[layerKey] = layer;
    });

    return returnLayers;
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
