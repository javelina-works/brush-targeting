<template>
  <div>
    <h1>Planner Page</h1>
    <BaseLeafletMap ref="baseMap" :layers="layers" /> 

    <div class="controls">
      <!-- Control Buttons -->
      <CButton class="mb-3" color="primary" aria-expanded={visible} aria-controls="collapseTesselation"
        @click="cellsCollapsed = !cellsCollapsed">
        {{ cellsCollapsed ? "Show Cells Settings" : "Hide Cells Settings" }}
      </CButton>
      <CButton class="mb-3" color="primary" aria-expanded={visible} aria-controls="collapseDepots"
        @click="depotsCollapsed = !depotsCollapsed">
        {{ depotsCollapsed ? "Show Depot Settings" : "Hide Depot Settings" }}
      </CButton>

      <RefreshMapData :baseMap="baseMap" />
      <SaveMapLayers :baseMap="baseMap" :locationId="locationId" :jobId="jobId" :layersToSave="saveLayers" />

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

<script setup>
import "@geoman-io/leaflet-geoman-free"; // Import Geoman
import "@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css";

import { ref, onMounted, computed } from 'vue';
import { useLocationStore } from '@/stores/locationStore';

import BaseLeafletMap from '@/components/LeafletMap/BaseLeafletMap.vue';
import SaveMapLayers from '@/components/LeafletMap/SaveMapLayers.vue';
import RefreshMapData from '@/components/LeafletMap/RefreshMapData.vue';

import TesselationControls from './TesselationControls.vue';
import DepotControls from './DepotControls.vue';
import { CButton } from "@coreui/vue";



/** ✅ References */
const locationStore = useLocationStore();
const locationId = computed(() => locationStore.selectedLocation?.id);
const jobId = computed(() => locationStore.selectedJob?.id);

/** ✅ Reference to the Base Map Component */
const baseMap = ref(null);

/** ✅ Wait for `BaseLeafletMap` to be ready */
const map = computed(() => baseMap.value?.map);
const mapLayers = computed(() => baseMap.value?.mapLayers);
const layerControl = computed(() => baseMap.value?.layerControl);

const cellsCollapsed = ref(true);
const depotsCollapsed = ref(true);


const layers = ref([
  "region_contour",
  "voronoi_cells",
  "depot_points",
]);

const saveLayers = ref([
  "voronoi_cells",
  "depot_points"
]);


// Initialize Leaflet map
const initMap = () => {
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

};


onMounted(() => {
  if (!map.value) {
    console.warn("Child map component is not ready!");
    return;
  }

  // initMap();
});

</script>

<style scoped>

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