<template>
  <div>
    <div id="map" class="map-container" ref="mapContainer"></div>
  </div>
  <!-- <h1>Testing</h1> -->
</template>

<script setup>
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

import { ref, onMounted, onUnmounted, computed } from 'vue';
import { initializeLayers, updateLayerData, getAllLayers } from "./layers";
import { useLocationStore } from '@/stores/locationStore';
import api from '@/api/axios.js';


const locationStore = useLocationStore();
const selectedLocation = computed(() => locationStore.selectedLocation);
const selectedJob = computed(() => locationStore.selectedJob);

/** Map container reference */
const mapContainer = ref(null);
const map = ref(null);
const regionTilesLoaded = ref(false);
const regionOutlineLoaded = ref(false);

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



async function loadRegionTiles() {
  try {
    const response = await api.get(`/api/get_tile_url/?location_id=${selectedLocation.value.id}&job_id=${selectedJob.value.id}`);
    console.log("Response: ", response);
    if (response.data.tile_url && map.value) {
      // const TILE_API = `${BACKEND_URL}/api/tile/${selectedLocation.value.id}/${selectedJob.value.id}/{z}/{x}/{y}.png`;
      // console.log("Adding tile layer: ", TILE_API);
      console.log("Adding region tile layer:", response.data.tile_url);
      L.tileLayer(response.data.tile_url, {
        attribution: 'COG Tiles',
        maxZoom: 21,
        timeout: 3000, // 3 seconds
        crossOrigin: true,
      }).addTo(map.value);
      regionTilesLoaded.value = true;
    }
  } catch (error) {
    console.warn("No COG tile available or error loading tiles:", error);
  }
}



async function loadGeoJson(filename) {
  try {
    // const response = await api.get(`api/files/${selectedJob.value.id}/${filename}`);
    const response = await api.get(`api/files/${selectedJob.value.id}/region_contour.geojson`);
    
    if (response.data && map.value) {
      const geoJsonLayer = L.geoJSON(response.data, {
        style: { color: "blue", weight: 2, fill: false, }
      }).addTo(map.value);
      map.value.fitBounds(geoJsonLayer.getBounds());
      regionOutlineLoaded.value = true;
    }
  } catch (error) {
    console.error("Failed to load GeoJSON:", error);
  }
}

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

  loadGeoJson();
  // loadRegionTiles();
  initializeLayers(map.value);
  
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