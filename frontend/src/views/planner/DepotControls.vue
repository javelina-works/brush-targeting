<template>
  <div class="depot-controls">
    <CCard style="width: 300px">
      <CCardHeader>Depot Settings</CCardHeader>
      <CCardBody>


        <!-- Depot Radius Slider -->
        <label for="depot-radius">Depot Radius (m): {{ depotRadius }}</label>
        <CFormRange id="depot-radius" :min="10" :max="1000" :step="20" v-model="depotRadius" />

        <!-- Max Depots Slider -->
        <label for="max-depots">Search Density: {{ gridDensity }}</label>
        <CFormRange id="max-depots" :min="1" :max="10" :step="1" v-model="gridDensity" />

        <!-- Generate Button -->
        <CButton color="secondary" @click="generateDepots" :disabled="isGenerating">
          {{ isGenerating ? "Generating..." : "Generate Depots" }}
        </CButton>
      </CCardBody>
    </CCard>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import {
  CCardHeader, CCard, CCollapse, CCardBody, CFormRange, CButton,
} from "@coreui/vue";
import { useDepotsMutation } from "@/api/graphql_queries";
import { useLocationStore } from '@/stores/locationStore';
import { updateLayerData } from '@/components/LeafletMap/layers/layers';



const isGenerating = ref(false);

// 🟢 Default values (Stored as numbers internally)
const depotRadiusRaw = ref(250); // Default 250 m
const gridDensityRaw = ref(4); // Metric of candidate points

// 🔹 Ensure values remain STRINGS for the API but NUMBERS internally
const depotRadius = computed({
  get: () => String(depotRadiusRaw.value), // API gets a string
  set: (value) => (depotRadiusRaw.value = parseFloat(value)), // Store as float internally
});

const gridDensity = computed({
  get: () => String(gridDensityRaw.value), // API gets a string
  set: (value) => (gridDensityRaw.value = parseInt(value, 10)), // Store as int internally
});

const locationStore = useLocationStore();
const locationId = computed(() => locationStore.selectedLocation?.id);
const jobId = computed(() => locationStore.selectedJob?.id);

const { mutate: generateDepotsMutation } = useDepotsMutation();

const generateDepots = async () => {
  isGenerating.value = true;

  const { data } = await generateDepotsMutation({
    locationId: locationId.value,
    jobId: jobId.value,
    depotRadius: depotRadiusRaw.value, // As int
    gridDensity: gridDensityRaw.value, // As int
  });

  if (data?.generateDepots?.geojson) {
    updateLayerData("depot_points", data.generateDepots.geojson);
  }

  isGenerating.value = false;
};


</script>

<style scoped>
.depot-controls {
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