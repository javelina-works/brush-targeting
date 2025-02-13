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
import { useMapData, } from '@/api/graphql_queries';
import { initializeLayers, updateLayerData } from "./layers";

import TesselationControls from './TesselationControls.vue';
import DepotControls from './DepotControls.vue';

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
    const { result, loading, error } = useMapData(locationId.value, jobId.value, layers.value);

    // Initialize Leaflet map
    const initMap = () => {
      map.value = L.map("map", {
        maxZoom: 21,
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
    watchEffect(() => {
      if (error.value) {
        console.error("GraphQL error:", error.value);
      }
      if (loading.value) {
        console.log("Data is still loading...");
      }
      if (shouldQueryRun.value && result.value?.mapAssets) {
        result.value.mapAssets.forEach((asset) => {
          console.log(`Updating layer ${asset.name}`);
          updateLayerData(asset.name, asset.geojson);
          if (asset.name === "voronoi_cells") hasVoronoiCells.value = true;
          if (asset.name === "depot_locations") hasDepots.value = true;
        });
      }
    });

    onMounted(initMap);

    return { 
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