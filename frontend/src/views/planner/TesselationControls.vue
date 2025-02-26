<template>
  <CCard>
    <CCardHeader>Cells Settings</CCardHeader>
    <CCardBody>

      <!-- Cell Size Slider -->
      <label for="cell-size">Cell Area (Acres): {{ targetAreaAcres }}</label>
      <CFormRange id="cell-size" :value="0.5" :min="0.25" :max="5" :step="0.25" v-model="targetAreaAcres" />

      <!-- Iterations Slider -->
      <label for="iterations">Iterations: {{ maxIterations }}</label>
      <CFormRange id="iterations" :value="15" :min="3" :max="50" :step="1" v-model="maxIterations" />

      <!-- Generate Button -->
      <CButton color="secondary" @click="generateTessellation" :disabled="isGenerating">
        {{ isGenerating ? "Generating..." : "Generate Voronoi Cells" }}
      </CButton>
    </CCardBody>
  </CCard>
</template>

<script setup>
import { ref, computed } from "vue";
import { useTessellationMutation } from "@/api/graphql_queries";
import { useLocationStore } from '@/stores/locationStore';
import { updateLayerData } from '@/components/LeafletMap/layers/layers';
import {
  CCardHeader, CCard, CCardBody, CFormRange, CButton,
} from "@coreui/vue";


// 🟢 Default values (Floats & Integers)
const targetAreaAcresRaw = ref(0.5);
const maxIterationsRaw = ref(10);

// 🔹 Convert to STRING for API, but keep internal as numbers
const targetAreaAcres = computed({
  get: () => String(targetAreaAcresRaw.value), // API receives a string
  set: (value) => (targetAreaAcresRaw.value = parseFloat(value)), // Store as float internally
});

const maxIterations = computed({
  get: () => String(maxIterationsRaw.value), // API receives a string
  set: (value) => (maxIterationsRaw.value = parseInt(value, 10)), // Store as int internally
});


const locationStore = useLocationStore();
const locationId = computed(() => locationStore.selectedLocation?.id);
const jobId = computed(() => locationStore.selectedJob?.id);

const { mutate: generateTessellationMutation } = useTessellationMutation();
const isGenerating = ref(false);

const generateTessellation = async () => {
  isGenerating.value = true;

  const { data } = await generateTessellationMutation({
    locationId: locationId.value,
    jobId: jobId.value,
    targetAreaAcres: targetAreaAcresRaw.value, // As float
    maxIterations: maxIterationsRaw.value // As Int
  });

  if (data?.generateTesselation?.geojson) {
    updateLayerData("voronoi_cells", data.generateTesselation.geojson);
  }

  isGenerating.value = false;
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

</style>