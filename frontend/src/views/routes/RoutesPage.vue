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
import "@geoman-io/leaflet-geoman-free"; // Import Geoman
import "@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css";

import { ref, watch, watchEffect, onMounted, computed } from 'vue';
import { useLocationStore } from '@/stores/locationStore';
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
        ]);

        // Load map assets
        const { result: getResult, loading, error } = useMapData(locationId.value, jobId.value, layers.value);
        const { mutate: updateMapAssets, error: updateError } = updateMapData();

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
