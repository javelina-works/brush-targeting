<template>
  <div>
    <h1>Planner Page</h1>
    <!-- Map Container -->
    <div id="map" ref="mapContainer"></div>

    <div class="controls">
      <!-- Control Buttons -->
      <CButton class="mb-3" color="primary" aria-expanded={visible} aria-controls="collapseTesselation" @click="cellsCollapsed = !cellsCollapsed">
        {{ cellsCollapsed ? "Show Cells Settings" : "Hide Cells Settings" }}
      </CButton>
      <CButton class="mb-3" color="primary" aria-expanded={visible} aria-controls="collapseDepots" @click="depotsCollapsed = !depotsCollapsed">
        {{ depotsCollapsed ? "Show Depot Settings" : "Hide Depot Settings" }}
      </CButton>

      <CButton class="mb-3" color="success" aria-expanded={visible} aria-controls="saveSettings" @click="saveLayers">
        Save Settings
      </CButton>

      <CRow>
        <CCol xs="6">
          <CCollapse :visible="!cellsCollapsed">
            <TesselationControls />
          </CCollapse>
        </CCol>
        <CCol xs="6">
          <CCollapse :visible="!depotsCollapsed">
            <DepotControls />
          </CCollapse>
        </CCol>
      </CRow>

    </div>
  </div>
</template>

<script>
import L from "leaflet";
import 'leaflet/dist/leaflet.css';
import "@geoman-io/leaflet-geoman-free"; // Import Geoman
import "@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css";

import { ref, watch, watchEffect, onMounted, computed } from 'vue';
import { useLocationStore } from '@/stores/locationStore';
import { useMapData, updateMapData } from '@/api/graphql_queries';
import { initializeLayers, updateLayerData, getAllLayers} from "./layers";

import TesselationControls from './TesselationControls.vue';
import DepotControls from './DepotControls.vue';
import { CButton } from "@coreui/vue";

export default {
  components: { TesselationControls, DepotControls },
  setup() {
    const locationStore = useLocationStore();
    const locationId = computed( () => locationStore.selectedLocation?.id );
    const jobId = computed( () => locationStore.selectedJob?.id );

    const shouldQueryRun = computed(() => !!locationId.value && !!jobId.value);

    const cellsCollapsed = ref(true);
    const depotsCollapsed = ref(true);

    const map = ref(null);
    const hasVoronoiCells = ref(false);
    const hasDepots = ref(false);

    const layers = ref([
      "region_contour",
      "voronoi_cells",
      "depot_points",
    ]);

    // Load map assets
    const { result: getResult, loading, error } = useMapData(locationId.value, jobId.value, layers.value);
    const { mutate: updateMapAssets, error: updateError } = updateMapData();

    // Initialize Leaflet map
    const initMap = () => {
      map.value = L.map("map", {
        maxZoom: 21,
        zoomAnimation: false, // https://stackoverflow.com/a/66516334
      }).setView([30.2506, -103.6035], 14);

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map.value);
      L.control.scale().addTo(map.value);
      map.value.pm.addControls({
        position: "topleft",
        drawRectangle: true,
        drawMarker: false, 
        
        drawCircleMarker: false, 
        drawCircle: false,
        drawPolygon: false, 
        drawPolyline: false, 
        drawText: false,

        removalMode: false, // We don't want to delete, just add to removed_targets
        dragMode: true, 
        editMode: false,
        rotateMode: false,
        cutPolygon: false,
      });

      initializeLayers(map.value); // Attach layers
    };

    // Reactively process API data
    watch(
      () => getResult.value?.mapAssets,  // ✅ Only watches `mapAssets`
      (newAssets, oldAssets) => {
        if (error.value) {
          console.error("GraphQL error:", error.value);
        }
        if (loading.value) {
          console.log("Data is still loading...");
        }
        if (shouldQueryRun.value && newAssets) {
          newAssets.forEach((asset) => {
            updateLayerData(asset.name, asset.geojson);
            // if (asset.name === "voronoi_cells") hasVoronoiCells.value = true;
            // if (asset.name === "depot_points") hasDepots.value = true;
          });
        }
    });

    // Save updated GeoJSON layers
    async function saveLayers() {
      const geojsonLayers = getAllLayers();
      const geojsonFiles = ["voronoi_cells", "depot_points"]
        .filter(layerName => geojsonLayers[layerName]) // Ensure layer exists
        .map(layerName => ({
            name: layerName,
            geojson: JSON.stringify(geojsonLayers[layerName].toGeoJSON()),
        }));

      // Send updated GeoJSON layers to the backend
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
            alert("Failed to save layers!");
          } else {
            console.log("Layers successfully saved:", data);
            // alert("Map layers saved successfully!");
          }
      } catch (err) {
          console.error("Save error:", err);
          alert("An unexpected error occurred while saving.");
      }
    }

    onMounted(initMap);

    return {
      saveLayers,
      hasVoronoiCells, 
      hasDepots,
      cellsCollapsed, 
      depotsCollapsed 
    };
  }
};



</script>

<style scoped>
#map {
  width: 100%;
  height: 500px;
}

.controls {
  margin-top: 10px;
}

button {
  margin-right: 10px;
  padding: 8px 12px;
  font-size: 16px;
  cursor: pointer;
}
</style>