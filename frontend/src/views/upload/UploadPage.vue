<template>
  <div class="upload-container">
    <h1>Upload Files</h1>

    <!-- Display Selected Project & Job -->
    <p><strong>Project ID:</strong> {{ selectedLocation?.id || 'Not Found' }}</p>
    <p><strong>Job ID:</strong> {{ selectedJob?.id || 'Not Found' }}</p>

    <!-- File Upload Components -->
    <OrthophotoUploader @upload-success="onOrthophotoUpload" :jobId="selectedJob.id" />
    <GeoJsonUploader @upload-success="onGeoJsonUpload" :jobId="selectedJob.id" />

    <!-- Leaflet Map -->
    <div>
      <h2>Region Map</h2>
      <BaseLeafletMap ref="baseMap" :layers="layers" />
      <RefreshMapData :baseMap="baseMap" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, } from 'vue';
import api from '@/api/axios.js';
import { useLocationStore } from '@/stores/locationStore';

import BaseLeafletMap from '@/components/LeafletMap/BaseLeafletMap.vue';
import RefreshMapData from '@/components/LeafletMap/RefreshMapData.vue';
import GeoJsonUploader from './GeoJsonUploader.vue';
import OrthophotoUploader from './OrthophotoUploader.vue';

/** References */
const locationStore = useLocationStore();
const selectedLocation = computed(() => locationStore.selectedLocation);
const selectedJob = computed(() => locationStore.selectedJob);

/** Reference to the Base Map Component */
const baseMap = ref(null);

/** 🚥 Wait for `BaseLeafletMap` to be ready */
const map = computed(() => baseMap.value?.map);
const refetch = computed(() => baseMap.value?.refetch);
// const mapLayers = computed(() => baseMap.value?.mapLayers);
// const layerControl = computed(() => baseMap.value?.layerControl);

const layers = ref([
  "region_contour",
]);


function onOrthophotoUpload(filename) {
  // console.log("Uploaded orthophoto: ", filename);
  loadRegionTiles();
}

// TODO: exactly the same as in BaseLeafletMap; pull into layers.js and call from there
async function loadRegionTiles() {
  try {
    const response = await api.get(`/api/get_tile_url/?location_id=${selectedLocation.value.id}&job_id=${selectedJob.value.id}`);
    if (response.data.tile_url && map.value) {
      // const TILE_API = `${BACKEND_URL}/api/tile/${selectedLocation.value.id}/${selectedJob.value.id}/{z}/{x}/{y}.png`;
      // console.log("Adding tile layer: ", TILE_API);
      // console.log("Adding region tile layer:", response.data.tile_url);
      L.tileLayer(response.data.tile_url, {
        attribution: 'COG Tiles',
        minZoom: 10,
        maxZoom: 21,
        crossOrigin: true,
      }).addTo(map.value);
    }
  } catch (error) {
    console.warn("No COG tile available or error loading tiles:", error);
  }
}

// Triggered after region outline uploaded
async function onGeoJsonUpload() {
  if (!refetch.value) {
    console.warn("⚠️ No refetch function available from BaseLeafletMap!");
    return;
  }

  try {
    await refetch.value(); // Refresh all geoJSON layers
  } catch (err) {
    console.error("❌ Refresh API call failed:", err);
  }
}

</script>

<style scoped>
.upload-container {
  max-width: 600px;
  margin: auto;
  text-align: center;
}

.upload-box {
  border: 2px dashed #ccc;
  padding: 20px;
  margin-bottom: 15px;
  cursor: pointer;
}

.upload-box:hover {
  background: #f4f4f4;
}
</style>
