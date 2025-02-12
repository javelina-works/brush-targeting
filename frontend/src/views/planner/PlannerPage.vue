<template>
  <div>
    <h1>Planner Page</h1>
    <!-- Map Container -->
    <div id="map" ref="mapContainer"></div>

    <!-- Control Buttons -->
    <div class="controls">
      <button v-if="!hasVoronoiCells" @click="generateTessellation">
        Generate Tessellation
      </button>
      <button v-if="!hasDepots" @click="generateDepots">
        Generate Depots
      </button>
    </div>
  </div>
</template>

<script>
import { ref, watch, watchEffect, onMounted, computed } from 'vue';
import L from "leaflet";
import { useLocationStore } from '@/stores/locationStore';
import { useMapData, useDepotsMutation, useTessellationMutation } from './graphQL'
import { initializeLayers, updateLayerData } from "./layers";

export default {
  setup() {
    const locationStore = useLocationStore();
    const locationId = computed( () => locationStore.selectedLocation?.id );
    const jobId = computed( () => locationStore.selectedJob?.id );

    const shouldQueryRun = computed(() => !!locationId.value && !!jobId.value);

    const map = ref(null);
    const hasVoronoiCells = ref(false);
    const hasDepots = ref(false);

    const layers = ref([
      "region_contour",
      "voronoi_cells",
    ]);

    // Load map assets
    const { result, loading, error } = useMapData(locationId.value, jobId.value, layers.value);
    const { mutate: generateTessellationMutation } = useTessellationMutation();
    const { mutate: generateDepotsMutation } = useDepotsMutation();


    // Initialize Leaflet map
    const initMap = () => {
      map.value = L.map("map", {
        maxZoom: 21,
      }).setView([30.2506, -103.6035], 14);

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map.value);
      L.control.scale().addTo(map.value);
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

    // Generate Voronoi Tessellation
    const generateTessellation = async () => {
      const { data } = await generateTessellationMutation({
        locationId: props.locationId,
        jobId: props.jobId,
        targetAreaAcres: 0.5,
        maxIterations: 10
      });
      if (data?.generateTesselation?.geojson) {
        updateLayerData("voronoi_cells", data.generateTesselation.geojson);
        hasVoronoiCells.value = true;
      }
    };

    // Generate Depots
    const generateDepots = async () => {
      const { data } = await generateDepotsMutation({
        locationId: props.locationId,
        jobId: props.jobId
      });
      if (data?.generateDepots?.geojson) {
        updateLayerData("depot_locations", data.generateDepots.geojson);
        hasDepots.value = true;
      }
    };

    onMounted(initMap);

    return { hasVoronoiCells, hasDepots, generateTessellation, generateDepots };
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