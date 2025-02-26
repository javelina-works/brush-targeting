<template>
  <BaseLeafletMap ref="baseMap" :layers="layers" />
  <RefreshMapData :baseMap="baseMap" />
  <SaveMapLayers :baseMap="baseMap" :locationId="locationId" :jobId="jobId" :layersToSave="saveLayers" />
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue';
import "@geoman-io/leaflet-geoman-free"; // Import Geoman
import "@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css";

import { useLocationStore } from '@/stores/locationStore';
import {
  moveFeature, getLayerProperties, getLayer,
} from '@/components/LeafletMap/layers/layers';

import BaseLeafletMap from '@/components/LeafletMap/BaseLeafletMap.vue';
import SaveMapLayers from '@/components/LeafletMap/SaveMapLayers.vue';
import RefreshMapData from '@/components/LeafletMap/RefreshMapData.vue';

/** ✅ Reference to the Base Map Component */
const baseMap = ref(null);

/** ✅ Wait for `BaseLeafletMap` to be ready */
const map = computed(() => baseMap.value?.map);
const mapLayers = computed(() => baseMap.value?.mapLayers);
const layerControl = computed(() => baseMap.value?.layerControl);

/** ✅ References */
const locationStore = useLocationStore();
const locationId = computed(() => locationStore.selectedLocation?.id);
const jobId = computed(() => locationStore.selectedJob?.id);

/** API Parameters */
const layers = ref([
  "region_contour",
  "removed_targets",
  "approved_targets"
]);

const saveLayers = ref([
  "approved_targets",
  "removed_targets"
]);


const addMapControls = () => {
  if (!map.value || !layerControl.value) {
    console.warn("⏳ Waiting for map to be ready...");
    return;
  }

  // // map.value.removeLayer(layerControl.value);
  // layerControl.value = L.control.layers(null, {}, {
  //   sortLayers: true, // Custom sort for our layers
  //   sortFunction: (a, b, a_name, b_name) => {
  //     const layerPriority = ["region_contour", "approved_targets", "removed_targets"];

  //     const indexA = layerPriority.indexOf(a_name);
  //     const indexB = layerPriority.indexOf(b_name);
  //     return (indexA === -1 ? Infinity : indexA) - (indexB === -1 ? Infinity : indexB);
  //   }
  // }).addTo(map.value);

  map.value.pm.addControls({
    position: "topleft",
    drawRectangle: true,

    drawCircleMarker: false, drawCircle: false, drawPolygon: false,
    drawPolyline: false, drawText: false, drawMarker: false,
    removalMode: false, // We don't want to delete, just add to removed_targets
    dragMode: false, editMode: false, rotateMode: false, cutPolygon: false,
  });

  map.value.on("pm:create", (e) => {
    if (e.shape === "Rectangle") {
      const bounds = e.layer.getBounds(); // Get bounding box
      toggleTargetsInRegion(bounds);
      map.removeLayer(e.layer); // Remove rectangle after selection
    }
  });

  map.value.on("dblclick", (e) => {
    // console.log("🖱️ Map clicked at:", e.latlng);
    addNewTarget(e.latlng);
  });

  console.log("✅ Map Initialized, waiting for API data...");
}


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

onMounted(() => {
  if (!map.value) {
    console.warn("Child map component is not ready!");
    return;
  }

  addMapControls();
});

</script>

<style scoped></style>