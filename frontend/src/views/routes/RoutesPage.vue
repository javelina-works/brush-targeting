<template>
    <div>
        <h1>Route Planner</h1>

        <!-- Map Container -->
        <BaseLeafletMap ref="baseMap" :layers="layers" />

        <div class="controls">
            <!-- Control Buttons -->
            <CButton class="mb-3" color="primary" aria-expanded={visible} aria-controls="collapseRouteParameters"
                @click="routingParametersCollapsed = !routingParametersCollapsed">
                {{ routingParametersCollapsed ? "Show Routing Settings" : "Hide Routing Settings" }}
            </CButton>
            <RefreshMapData :baseMap="baseMap" />

            <!-- Collapsable Controls -->
            <CRow>
                <CCol xs="6">
                    <CCollapse :visible="!routingParametersCollapsed">
                        <RoutingControls />
                    </CCollapse>
                </CCol>
            </CRow>

        </div>

    </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue';
import { useLocationStore } from '@/stores/locationStore';

import BaseLeafletMap from '@/components/LeafletMap/BaseLeafletMap.vue';
import SaveMapLayers from '@/components/LeafletMap/SaveMapLayers.vue';
import RefreshMapData from '@/components/LeafletMap/RefreshMapData.vue';
import RoutingControls from "./RoutingControls.vue";

const locationStore = useLocationStore();
const locationId = computed(() => locationStore.selectedLocation?.id);
const jobId = computed(() => locationStore.selectedJob?.id);

/** ✅ Reference to the Base Map Component */
const baseMap = ref(null);

/** ✅ Wait for `BaseLeafletMap` to be ready */
const map = computed(() => baseMap.value?.map);
// const mapLayers = computed(() => baseMap.value?.mapLayers);
// const layerControl = computed(() => baseMap.value?.layerControl);

const routingParametersCollapsed = ref(true);

const layers = ref([
    "region_contour",
    "voronoi_cells",
    "depot_points",
    "micro_routes",
]);

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
