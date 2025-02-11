<template>
    <div class="map-container" ref="mapContainer"></div>
</template>
  
<script setup>
  import { ref, watch, onMounted } from 'vue';
  import L from 'leaflet';
  import { useQuery } from '@vue/apollo-composable';
  import gql from 'graphql-tag';
  import 'leaflet/dist/leaflet.css';
  import "@geoman-io/leaflet-geoman-free"; // Import Geoman
  import "@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css";
  
  /** ✅ References */
  const mapContainer = ref(null);
  let map = null;
  const geojsonLayers = {}; // Dictionary to store actual Leaflet layers
  let layerControl = null;
  
  /** API Parameters */
  const locationId = ref("6a9b0014-fa87-463d-9767-46cf5c762b9f");
  const jobId = ref("0b8dd912-c4a6-4bd1-882e-c182bf120065");
  const layers = ref([
    "region_contour", 
    "removed_targets",
    "approved_targets"
    ]);
  
  /** GraphQL Query */
  const GET_MAP_ASSETS = gql`
    query GetMapAssets($locationId: String!, $jobId: String!, $layers: [String!]) {
      mapAssets(locationId: $locationId, jobId: $jobId, layers: $layers) {
        id
        name
        geojson
      }
    }
  `;

    /** Fetch GeoJSON Data */
    const { result } = useQuery(GET_MAP_ASSETS, {
        locationId: locationId.value,
        jobId: jobId.value,
        layers: layers.value
    });
  
  /** ✅ Initialize Leaflet Map */
  onMounted(() => {
    map = L.map(mapContainer.value).setView([30.2506, -103.6035], 14);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);
  
    L.control.scale().addTo(map);

    layerControl = L.control.layers(null, {}, {
        sortLayers: true, // Custom sort for our layers
        sortFunction: (a, b, a_name, b_name) => {
            const layerPriority = ["region_contour", "approved_targets", "removed_targets"];

            const indexA = layerPriority.indexOf(a_name);
            const indexB = layerPriority.indexOf(b_name);
            return (indexA === -1 ? Infinity : indexA) - (indexB === -1 ? Infinity : indexB);
        }
    }).addTo(map);

    map.pm.addControls({
        position: "topleft",
        drawRectangle: true,
        drawMarker: false, 
        
        drawCircleMarker: false, 
        drawCircle: false,
        drawPolygon: false, 
        drawPolyline: false, 
        drawText: false,

        removalMode: true,
        dragMode: false, 
        editMode: false,
        rotateMode: false,
        cutPolygon: false,
    });

    map.on("pm:create", (e) => {
        if (e.shape === "Rectangle") {
            const bounds = e.layer.getBounds(); // Get bounding box
            toggleTargetsInRegion(bounds);
            map.removeLayer(e.layer); // Remove rectangle after selection
        }
    });

    map.on("click", (e) => {
        console.log("🖱️ Map clicked at:", e.latlng);
        addNewTarget(e.latlng);
    });

    console.log("✅ Map Initialized, waiting for API data...");
  });


// Possibly the wrong way to go about this? Should we expose from the backend?
// It feels like this is something that should by typed later on
function getTargetSchema() {
  const layersToCheck = ["approved_targets", "removed_targets"];

  for (let layerName of layersToCheck) {
    if (!geojsonLayers[layerName]) continue;

    let schemaExample = null;
    geojsonLayers[layerName].eachLayer((layer) => {
      if (layer.feature) {
        schemaExample = { ...layer.feature.properties };
      }
    });

    if (schemaExample) return schemaExample; // Return first found schema
  }

  return {}; // Default if no schema is found
}

  function addNewTarget(latlng) {
    const schema = getTargetSchema(); // Get existing properties structure
    const newId = crypto.randomUUID(); // Generate a new UUID for target_id

    const newFeature = {
        type: "Feature",
        properties: { 
            ...schema, // Copy all properties from existing targets
            target_id: newId, // Ensure unique ID
            addedByUser: true, // Optional flag
        },
        geometry: {
            type: "Point",
            coordinates: [latlng.lng, latlng.lat],
        },
    };

  // Add to the approved_targets layer
  geojsonLayers["approved_targets"].addData(newFeature);
  console.log(`✅ Added new target at ${latlng.lat}, ${latlng.lng}`);

  // TODO: Send to backend for persistence
//   updateBackend(newFeature, "approved_targets");
}

function toggleTargetsInRegion(bounds) {
  const featuresToMove = []; // Store features and their target layers
  const layersToCheck = ["approved_targets", "removed_targets"];

  layersToCheck.forEach((fromLayer) => {
    if (!geojsonLayers[fromLayer]) return;

    const toLayer = (fromLayer === "approved_targets") ? "removed_targets" : "approved_targets";
    geojsonLayers[fromLayer].eachLayer((layer) => {
      if (layer.feature && layer.getLatLng) {
        const latlng = layer.getLatLng();
        if (bounds.contains(latlng)) {
            featuresToMove.push({ feature: layer.feature, fromLayer, toLayer });
        }
      }
    });
  });

  // Now move all collected features in one step
  featuresToMove.forEach(({ feature, fromLayer, toLayer }) => {
    moveFeature(feature, fromLayer, toLayer);
  });
}


function moveFeature(feature, fromLayer, toLayer) {
    if (!geojsonLayers[fromLayer] || !geojsonLayers[toLayer]) return;

    // Remove from current layer
    geojsonLayers[fromLayer].eachLayer(layer => {
        if (layer.feature === feature) {
            geojsonLayers[fromLayer].removeLayer(layer);
        }
    });

    geojsonLayers[toLayer].addData(feature); // Add to the new layer
    // console.log(`🔄 Moved feature ${feature.properties.target_id} from ${fromLayer} to ${toLayer}`);

    // TODO: Send update to backend so this persists
    // updateBackend(feature, toLayer);
}

const layerFactory = {
    region_contour: () => L.geoJSON(null, {
        style: { color: "blue", weight: 2, fillOpacity: 0.1 },
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
    default: () => L.geoJSON(null, {
        pointToLayer: (feature, latlng) => L.circleMarker(latlng, { color: "gray", radius: 5 }),
        onEachFeature: (feature, layer) => {
        layer.bindPopup(`<b>Unknown Layer</b><br>ID: ${feature.properties?.id || "N/A"}`);
        },
    }),
};

// Function to initialize layers
function initLayers() {
  Object.keys(layerFactory).forEach(name => {
    geojsonLayers[name] = layerFactory[name]();
    geojsonLayers[name].addTo(map); // Assuming `map` is your Leaflet instance
  });
}

// Function to update a specific layer with new data
function updateLayer(name, geojsonData) {
  if (geojsonLayers[name]) {
    geojsonLayers[name].clearLayers(); // Clear existing features
    geojsonLayers[name].addData(geojsonData);

    if (geojsonLayers["region_contour"]) {
        geojsonLayers["region_contour"].bringToBack();
    }
  }
}

/** ✅ Watch for API Data and Update Layers */
watch(result, (newData) => {
  if (!newData || !newData.mapAssets) return;
  console.log("📡 API Data Received:", newData.mapAssets);

  newData.mapAssets.forEach(asset => {
    try {
      const parsedGeoJson = JSON.parse(asset.geojson); // ✅ Convert JSON string to object
      const name = asset.name

      if (geojsonLayers[name]) {
        updateLayer(name, parsedGeoJson);
      } else {
        // If a new layer type appears, initialize it dynamically
        geojsonLayers[name] = (layerFactory[name] || layerFactory.default)();
        geojsonLayers[name].addTo(map);
        updateLayer(name, parsedGeoJson);
        layerControl.addOverlay(geojsonLayers[name], name);
      }
    } catch (error) {
      console.error(`❌ Error parsing GeoJSON for ${asset.name}:`, error);
    }
  });
});

</script>



<style scoped>

.map-container {
    width: 100%;
    height: 100vh;
}

</style>
  