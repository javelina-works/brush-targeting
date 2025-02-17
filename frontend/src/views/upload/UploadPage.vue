<template>
  <div class="upload-container">
    <h1>Upload Files</h1>

    <!-- Display Selected Project & Job -->
    <p><strong>Project ID:</strong> {{ selectedLocation?.id || 'Not Found' }}</p>
    <p><strong>Job ID:</strong> {{ selectedJob?.id || 'Not Found' }}</p>

    <!-- Region Image Upload Component -->
    <OrthophotoUploader @upload-success="onOrthophotoUpload" :jobId="selectedJob.id"/>

    <!-- Region Outline Upload Component -->
    <GeoJsonUploader @upload-success="onGeoJsonUpload" :jobId="selectedJob.id"/>

    <!-- Leaflet Map -->
    <!-- <div v-if="regionOutlineLoaded || regionTilesLoaded"> -->
    <div>
      <h2>Region Outline</h2>
      <div id="map" ref="mapContainer"></div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch, nextTick } from 'vue';
import L from "leaflet";
import 'leaflet/dist/leaflet.css';

import api from '@/api/axios.js';
import { useLocationStore } from '@/stores/locationStore';

import GeoJsonUploader from './GeoJsonUploader.vue';
import OrthophotoUploader from './OrthophotoUploader.vue';
import { CButton } from '@coreui/vue';

export default {
  components: { 
    CButton, 
    GeoJsonUploader, 
    OrthophotoUploader 
  },
  setup() {
    const locationStore = useLocationStore();
    const selectedLocation = computed(() => locationStore.selectedLocation);
    const selectedJob = computed(() => locationStore.selectedJob);

    const map = ref(null);
    const mapContainer = ref(null);
    const regionOutlineLoaded = ref(false);
    const regionTilesLoaded = ref(false);
    const BACKEND_URL = "http://localhost:8000";

    watch([regionOutlineLoaded, regionTilesLoaded], ([outline, tiles]) => {
      console.log("Updated values:", { outline, tiles });
    });

    function onOrthophotoUpload(filename) {
      console.log("Uploaded orthophoto: ", filename);
      regionTilesLoaded.value = true;
      // TODO: begin tiling region image
      loadRegionTiles();
    }

    async function loadRegionTiles() {
      try {
        const response = await api.get(`/api/get_tile_url/?location_id=${selectedLocation.value.id}&job_id=${selectedJob.value.id}`);
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

    // async function loadRegionTiles() {
    //   try {
    //     if (map.value) {
    //       
    //       L.tileLayer(TILE_API, {
    //           attribution: 'COG Tiles',
    //           maxZoom: 21,
    //           timeout: 30000,  // 30 seconds
    //       }).addTo(map.value);
    //     }
    //   } catch (error) {
    //     console.error("Failed to load tile layer:", error);
    //   }
    // }


    // Triggered after region outline uploaded
    function onGeoJsonUpload(filename) {
      console.log("Uploaded file: ", filename);
      regionOutlineLoaded.value = true;
      loadGeoJson(filename);
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

    watch(regionOutlineLoaded, (newFile) => {
      if (newFile) {
        nextTick(() => {
          initMap();  // Reinitialize the map when regionOutlineFile updates
        });
      }
    });

    function initMap() {
      if (!mapContainer.value) return;
      if (map.value) return; // Prevent duplicate map initialization
      
      map.value = L.map(mapContainer.value, {
        maxZoom: 21,
      }).setView([30.2506, -103.6035], 14);
      
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map.value);
      L.control.scale().addTo(map.value);
      
      loadGeoJson();
      loadRegionTiles();
    }

    onMounted(initMap);

    return {
      selectedLocation,
      selectedJob,
      mapContainer,
      regionOutlineLoaded,
      regionTilesLoaded,
      onOrthophotoUpload,
      onGeoJsonUpload,
    };
  },
};
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

#map {
  width: 100%;
  height: 400px;
  margin-top: 20px;
}
</style>
