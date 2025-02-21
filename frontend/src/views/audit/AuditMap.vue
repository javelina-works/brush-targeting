<template>
  <div class="map-container" ref="mapContainer"></div>
  <button class="save-button" @click="saveTargets">Save Changes</button>
  <button class="refresh-button" @click="refetch">Refresh Data</button>
  <p v-if="savingStatus" class="status-message">{{ savingStatus }}</p>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue';
import L from 'leaflet';
import { useQuery, useMutation } from '@vue/apollo-composable';
import gql from 'graphql-tag';
import 'leaflet/dist/leaflet.css';
import "@geoman-io/leaflet-geoman-free"; // Import Geoman
import "@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css";

import { useLocationStore } from '@/stores/locationStore';
import { useMapData, updateMapData } from '@/api/graphql_queries';
import { 
  initializeLayers, updateLayerData, mapLayers, 
  moveFeature, getLayerProperties, getLayer,
} from '@/components/LeafletMap/layers';

/** ✅ References */
const locationStore = useLocationStore();
const locationId = computed(() => locationStore.selectedLocation?.id);
const jobId = computed(() => locationStore.selectedJob?.id);
const shouldQueryRun = computed(() => !!locationId.value && !!jobId.value);

const mapContainer = ref(null);
let map = null;
let layerControl = null;

/** API Parameters */
const layers = ref([
  "region_contour",
  "removed_targets",
  "approved_targets"
]);

/** GraphQL Query */
const { result: getResult, refetch, loading, error, onResult } = useMapData(locationId.value, jobId.value, layers.value);
const { mutate: updateMapAssets, error: updateError } = updateMapData();

const savingStatus = ref(null); // Update save message when button clicked


async function saveTargets() {
  savingStatus.value = "Saving...";
  const geojsonLayers = getAllLayers();
  const geojsonFiles = ["approved_targets", "removed_targets"]
    .filter(layerName => geojsonLayers[layerName]) // Ensure layer exists
    .map(layerName => ({
      name: layerName,
      geojson: JSON.stringify(geojsonLayers[layerName].toGeoJSON()),
    }));

  if (geojsonFiles.length === 0) {
    savingStatus.value = "⚠️ No changes to save.";
    return;
  }

  try {
    const { data } = await updateMapAssets({
      locationId: locationId.value,
      jobId: jobId.value,
      geojsonFiles: geojsonFiles
    });

    if (data.error) {
      console.error("Error saving layers:", updateError);
    }
    if (updateError.value) {
      console.error("Save API error:", updateError.value);
      savingStatus.value = `⚠️ Some files failed: ${response.data.updateMapAssets.errorMessage}`;
      alert("Failed to save layers!");
    } else {
      console.log("Layers successfully saved:", data);
      savingStatus.value = "✅ All changes saved!";
      // alert("Map layers saved successfully!");
    }
  } catch (err) {
    console.error("❌ Save API call failed:", error);
    alert("An unexpected error occurred while saving.");
  }
}


/** ✅ Initialize Leaflet Map */
const initMap = () => {
  map = L.map(mapContainer.value, {
    minZoom: 6,
    maxZoom: 21,
    zoomAnimation: false, // https://stackoverflow.com/a/66516334
  }).setView([30.2506, -103.6035], 14);

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

    removalMode: false, // We don't want to delete, just add to removed_targets
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

  map.on("dblclick", (e) => {
    // console.log("🖱️ Map clicked at:", e.latlng);
    addNewTarget(e.latlng);
  });

  initializeLayers(map);
  console.log("✅ Map Initialized, waiting for API data...");
};


// Possibly the wrong way to go about this? Should we expose from the backend?
// It feels like this is something that should by typed later on
function getTargetSchema() {
  const layersToCheck = ["approved_targets", "removed_targets"];

  for (let layerName of layersToCheck) {
    let schemaExample = getLayerProperties(layerName);
    if (schemaExample !== {}) return schemaExample; // Return first found schema
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
  const approvedTargetsLayer = getLayer("approved_targets");
  approvedTargetsLayer.addData(newFeature);
  console.log(`✅ Added new target at ${latlng.lat}, ${latlng.lng}`);

  // TODO: Send to backend for persistence
  //   updateBackend(newFeature, "approved_targets");
}

// For our rectangle selection
// Swap layers of all targets in selected region
function toggleTargetsInRegion(bounds) {
  const featuresToMove = []; // Store features and their target layers
  const layersToCheck = ["approved_targets", "removed_targets"];

  layersToCheck.forEach((fromLayer) => {
    const checkLayer = getLayer(fromLayer);
    if (!checkLayer) {
      console.warn("Cannot move targets from layer: ", fromLayer);
      return;
    } 

    const toLayer = (fromLayer === "approved_targets") ? "removed_targets" : "approved_targets";
    checkLayer.eachLayer((layer) => {
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



/** ✅ Watch for API Data and Update Layers */
onResult((newAssets) => {
  console.log("📡 API Data Received:", newAssets);
  
  if (error.value) {
    console.error("GraphQL error:", error.value);
  }
  if (loading.value) {
    console.log("Data is still loading...");
  }

  if (!newAssets.data || !newAssets.data.mapAssets) return;
  if (shouldQueryRun.value && newAssets) {
    newAssets.data.mapAssets.forEach((asset) => {
      layerControl.removeLayer(mapLayers[asset.name]); // Don't duplicate!
      updateLayerData(asset.name, asset.geojson);
      layerControl.addOverlay(mapLayers[asset.name], asset.name); // TODO: not sure we want to export mapLayers const
    });
  }
});


onMounted(initMap);
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 75vh;
}

.save-button {
  padding: 8px 12px;
  background-color: #28a745;
  color: white;
  border: none;
  cursor: pointer;
  font-size: 14px;
}

.save-button:hover {
  background-color: #218838;
}

.status-message {
  font-size: 14px;
  color: white;
  background-color: rgba(0, 0, 0, 0.7);
  padding: 5px 10px;
  border-radius: 5px;
}
</style>