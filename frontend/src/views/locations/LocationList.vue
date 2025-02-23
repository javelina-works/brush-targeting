<template>
  <CCard class="sidebar">

    <CCardHeader>
      <h2>Locations</h2>
    </CCardHeader>

    <CButton color="secondary" @click="showCreateLocation = true" class="new-button">
      + New Location
    </CButton>

    <CListGroup flush>
      <CListGroupItem v-for="location in locations" :key="location.id" as="button"
        :active="location.id === selectedLocation?.id" @click="$emit('select', location)">
        {{ location.name }}
      </CListGroupItem>
    </CListGroup>
  </CCard>

  <!-- Opens when triggered with button -->
  <CreateLocationModal :isVisible="showCreateLocation" @close="handleLocationModalClose" />
</template>

<script setup>
import { onMounted, ref } from 'vue';
import {
  CSidebar, CSidebarHeader, CSidebarBrand,
  CListGroup, CListGroupItem, CButton,
  CCard, CCardBody, CCardHeader,
} from '@coreui/vue';
import api from '@/api/axios.js';
import CreateLocationModal from './CreateLocationModal.vue';

const showCreateLocation = ref(false); // Open modal or not

const props = defineProps({
  locations: {
    type: Array,
    default: [],
  },
  selectedLocation: {
    type: String,
    default: "",
  }
});

async function fetchLocations() {
  try {
    // console.log("fetchLocations() called at:", new Date().toISOString());
    const res = await api.get('/api/locations/');
    locations.value = res.data;
    // console.log("Fetched locations:", locations.value);
  } catch (error) {
    console.error("Error fetching locations:", error.response ? error.response.data : error.message);
  }
}

function handleLocationModalClose() {
  showCreateLocation.value = false;
  console.log("Fetching locations after modal closes...");
  fetchLocations(); // Fetch only after closing
}

onMounted(async () => {
  await fetchLocations(); // Fetch locations first
})

</script>

<style scoped>
.new-button {
  margin-bottom: 10px;
}

.sidebar {
  width: 30%;
  padding: 20px;
}

.selected {
  font-weight: bold;
  color: blue;
}
</style>