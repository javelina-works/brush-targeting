<template>
    <CCard>
        <CCardHeader>Route Planning Settings</CCardHeader>
        <CCardBody>

            <!-- Num Vehicles Slider -->
            <label for="vehicle-count">Routes Count: {{ vehiclesCount }}</label>
            <CFormRange id="vehicle-count" :value="25" :min="15" :max="55" :step="1" v-model="vehiclesCount" />

            <!-- Iterations Slider -->
            <label for="drone-range">Drone Range (m): {{ maxDistance }}</label>
            <CFormRange id="drone-range" :value="850" :min="250" :max="5000" :step="25" v-model="maxDistance" />

            <!-- Generate Button -->
            <button @click="solveRoutes" :disabled="isGenerating">
                {{ isGenerating ? "Generating..." : "Generate Drone Routes" }}
            </button>
        </CCardBody>
    </CCard>
</template>

<script>
import { ref, computed } from "vue";
import { useSolveRoutesMutation } from "@/api/graphql_queries";
import { useLocationStore } from '@/stores/locationStore';
import { updateLayerData } from "@/components/LeafletMap/layers/layers";
import {
    CCardHeader, CCard, CCardBody, CFormRange, CButton,
} from "@coreui/vue";

export default {
    setup() {
        const locationStore = useLocationStore();
        const locationId = computed(() => locationStore.selectedLocation?.id);
        const jobId = computed(() => locationStore.selectedJob?.id);

        const isGenerating = ref(false);

        // 🟢 Default values (Floats & Integers)
        const vehiclesCountRaw = ref(25);
        const maxDistanceRaw = ref(850);

        // 🔹 Convert to STRING for API, but keep internal as numbers
        const vehiclesCount = computed({
            get: () => String(vehiclesCountRaw.value), // API receives a string
            set: (value) => (vehiclesCountRaw.value = parseInt(value, 10)), // Store as int internally
        });

        const maxDistance = computed({
            get: () => String(maxDistanceRaw.value), // API receives a string
            set: (value) => (maxDistanceRaw.value = parseInt(value, 10)), // Store as int internally
        });

        const { mutate: generateRoutesSolution } = useSolveRoutesMutation();



        const solveRoutes = async () => {
            isGenerating.value = true;

            const { data } = await generateRoutesSolution({
                locationId: locationId.value,
                jobId: jobId.value,
                tNumVehicles: vehiclesCountRaw.value, // As int
                maxDistance: maxDistanceRaw.value // As Int
            });

            if (data?.solveRoutes?.geojson) {
                updateLayerData("micro_routes", data.solveRoutes.geojson);
            }

            isGenerating.value = false;
        };

        return {
            vehiclesCount,
            maxDistance,
            isGenerating,
            solveRoutes,
        };
    },
};
</script>

<style scoped>
.tessellation-controls {
    margin: 10px 0;
}

.card {
    padding: 10px;
    border-radius: 5px;
    box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.2);
}

button {
    margin-top: 10px;
    padding: 8px;
    font-size: 14px;
}
</style>