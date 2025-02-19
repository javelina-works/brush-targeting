<template>
  <div>
    <div id="map" class="map-container" ref="mapContainer"></div>
  </div>
  <!-- <h1>Testing</h1> -->
</template>

<script setup>
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

import { ref, onMounted, onUnmounted } from 'vue';
import { initializeLayers, updateLayerData, getAllLayers } from "./layers";


/** Map container reference */
const mapContainer = ref(null);
const map = ref(null);

const props = defineProps({
  center: {
    type: Array,
    default: () => [30.25065, -103.60355], // Default: Out in Alpine
  },
  zoom: {
    type: Number,
    default: 14,
  },
});


/** Initialize Leaflet Map */
const initMap = () => {
  map.value = L.map(mapContainer.value, {
    center: props.center,
    zoom: props.zoom,
    maxZoom: 21,
    zoomAnimation: false, // https://stackoverflow.com/a/66516334
    preferCanvas: true,
  });

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    crossOrigin: true,
  }).addTo(map.value);
  L.control.scale().addTo(map.value);

  initializeLayers(map.value);
  console.log("✅ Map Initialized, waiting for API data...");

  // Fix map sizing issues after a short delay
  setTimeout(() => {
    map.value.invalidateSize();
  }, 300);
}


onMounted(() => {
  initMap();
});

onUnmounted(() => {
  if (map.value) {
    map.value.remove();
    map.value = null;
  }
});

/** Expose map instance */
defineExpose({ map });
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 500px;
  border: 2px solid #ccc;
  border-radius: 8px;
}
</style>