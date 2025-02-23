<template>
  <div>
    <div id="map" class="map-container" ref="mapContainer"></div>
  </div>
</template>

<script setup>
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { initializeLayers, updateLayerData, getAllLayers, getLayer } from "./layers/layers";
import { useLocationStore } from '@/stores/locationStore';
import { useMapData, updateMapData } from "@/api/graphql_queries";
import api from '@/api/axios.js';

const props = defineProps({
  center: {
    type: Array,
    default: () => [30.25065, -103.60355], // Default: Out in Alpine
  },
  zoom: {
    type: Number,
    default: 14,
  },
  layers: {
    type: Array,
    default: () => [ 
      "region_contour", // Always start with region outline
    ],
  }
});

/** Location and Job reference setup */
const locationStore = useLocationStore();
const locationId = computed(() => locationStore.selectedLocation?.id);
const jobId = computed(() => locationStore.selectedJob?.id);
const shouldQueryRun = computed(() => !!locationId.value && !!jobId.value);

/** Map API query setups */
const { result: getResult, refetch, loading, error, onResult } = useMapData(locationId.value, jobId.value, props.layers);
const { mutate: updateMapAssets, error: updateError } = updateMapData();

/** Map container reference */
const mapContainer = ref(null); // Connect map to div
const map = ref(null); // Holds ref to actual map & layers
const layerControl = ref(null);
const mapLayers = ref({}); // Store all layers for easy access

const regionTilesLoaded = ref(false);

/** Load and Apply API Data to Map */
watch([layerControl, mapLayers], ([newLayerControl, newMapLayers]) => {
  if (!newLayerControl || !newMapLayers) return;

  onResult((newAssets) => {
    // console.log("📡 Map data updated:", newAssets);

    if (error.value) {
      console.error("GraphQL error:", error.value);
    }
    if (loading.value) {
      console.log("Data is still loading...");
    }
    
    if (!newAssets?.data?.mapAssets) return;
    if (!layerControl.value || !mapLayers.value) return;

    newAssets.data.mapAssets.forEach((asset) => {
      if (mapLayers.value[asset.name]) {
        layerControl.value.removeLayer(mapLayers.value[asset.name]);
      }

      updateLayerData(asset.name, asset.geojson);
      layerControl.value.addOverlay(mapLayers.value[asset.name], asset.name);
    });
  });
}, { immediate: true });



const BACKEND_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function loadRegionTiles() {
  if (regionTilesLoaded.value) return; // Prevent duplicate calls if already setup

  try {
    const response = await api.get(`/api/get_tile_url/?location_id=${locationId.value}&job_id=${jobId.value}`);    
    if (response.data.tile_url && map.value) {
      // const TILE_API = `${BACKEND_URL}/api/tile/${selectedLocation.value.id}/${selectedJob.value.id}/{z}/{x}/{y}.png`;
      // console.log("Adding tile layer: ", TILE_API);
      console.log("Adding region tile layer:", response.data.tile_url);
      L.tileLayer(response.data.tile_url, {
        attribution: 'COG Tiles',
        minZoom: 10,
        maxZoom: 21,
      }).addTo(map.value);
      regionTilesLoaded.value = true;
    }
  } catch (error) {
    console.warn("No COG tile available or error loading tiles:", error);
  }
}

/** Initialize Leaflet Map */
const initMap = () => {
  map.value = L.map(mapContainer.value, {
    center: props.center,
    zoom: props.zoom,
    minZoom: 6,
    maxZoom: 21,
    zoomAnimation: false, // https://stackoverflow.com/a/66516334
    preferCanvas: true,
  });

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    crossOrigin: true,
  }).addTo(map.value);
  
  L.control.scale().addTo(map.value);
  layerControl.value = L.control.layers(null, {}, { sortLayers: true }).addTo(map.value);

  initializeLayers(map.value);
  mapLayers.value = getAllLayers(); // Ensure we can access all layers

  // const regionOutlineLayer = getLayer("region_contour");
  // if (regionOutlineLayer) {
  //   console.log("Region bounds: ", regionOutlineLayer.getBounds());
  //   map.value.fitBounds(regionOutlineLayer.getBounds());
  // }

  loadRegionTiles();
  
  // Fix map sizing issues after a short delay
  setTimeout(() => {
    map.value.invalidateSize();
  }, 300);

}


onMounted(() => {
  if (!mapContainer.value) {
    console.error("Map container not ready.");
    return;
  }
  
  if ( !shouldQueryRun.value ) {
    console.warn("Location or Job ID not available. Skipping map init.");
    return;
  }

  initMap();
});

onUnmounted(() => {
  if (map.value) {
    map.value.off();
    map.value.remove();
    map.value = null;
  }

  regionTilesLoaded.value = false;
});

/** Expose map instance */
defineExpose({ map, mapLayers, layerControl, refetch });

</script>

<style scoped>
.map-container {
  width: 100%;
  height: 500px;
  border: 2px solid #ccc;
  border-radius: 8px;
}
</style>