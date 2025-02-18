<template>
    <div>
        <h1>Route Planner</h1>

        <!-- Map Container -->
        <div id="map" ref="mapContainer"></div>

        <div class="controls">
            <!-- Control Buttons -->
            <CButton class="mb-3" color="primary" aria-expanded={visible} aria-controls="collapseRouteParameters"
                @click="routingParametersCollapsed = !routingParametersCollapsed">
                {{ routingParametersCollapsed ? "Show Routing Settings" : "Hide Routing Settings" }}
            </CButton>

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

<script>
import L from "leaflet";
import 'leaflet/dist/leaflet.css';

import { ref, watch, watchEffect, onMounted, computed } from 'vue';
import { useLocationStore } from '@/stores/locationStore';
import api from '@/api/axios.js';
import { useMapData, updateMapData } from '@/api/graphql_queries';
import { initializeLayers, updateLayerData, getAllLayers } from "./layers";

import RoutingControls from "./RoutingControls.vue";

export default {
    components: { RoutingControls },
    setup() {
        const locationStore = useLocationStore();
        const locationId = computed(() => locationStore.selectedLocation?.id);
        const jobId = computed(() => locationStore.selectedJob?.id);

        const shouldQueryRun = computed(() => !!locationId.value && !!jobId.value);

        const routingParametersCollapsed = ref(true);
        const hasSolvedRoutes = ref(false);

        const map = ref(null);

        const layers = ref([
            "region_contour",
            "voronoi_cells",
            "depot_points",
            "micro_routes",
        ]);

        // Load map assets
        const { result: getResult, loading, error } = useMapData(locationId.value, jobId.value, layers.value);

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
                    });
                }
            });

        
        // Ensure tiles are loaded only when locationId and jobId are available
        watch(
            () => shouldQueryRun, 
            (newValue, oldValue) => {
                // console.log("shouldQueryRun changed:", oldValue, "→", newValue); // Debugging log
                // console.log("New: ", newValue.value);
                if (newValue) {
                    loadRegionTiles();
                }
            },
            { immediate: true } // ✅ Run immediately if shouldQueryRun is already true
        );

        async function loadRegionTiles() {
            if (shouldQueryRun.value !== true) return; // Need both location and job IDs
            try {
                const response = await api.get(`/api/get_tile_url/?location_id=${locationId.value}&job_id=${jobId.value}`);
                if (response.data.tile_url && map.value) {
                    L.tileLayer(response.data.tile_url, {
                        attribution: 'COG Tiles',
                        maxZoom: 21,
                        timeout: 3000, // 3 seconds
                        crossOrigin: true,
                    }).addTo(map.value);
                }
            } catch (error) {
                console.warn("No COG tile available or error loading tiles:", error);
            }
        }


        // Initialize Leaflet map
        const initMap = () => {
            map.value = L.map("map", {
                maxZoom: 21,
                zoomAnimation: false, // https://stackoverflow.com/a/66516334
            }).setView([30.2506, -103.6035], 14);

            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map.value);
            L.control.scale().addTo(map.value);

            initializeLayers(map.value); // Attach layers
        };

        onMounted(initMap);

        return {
            routingParametersCollapsed,
            hasSolvedRoutes,
        };
    }
}

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
