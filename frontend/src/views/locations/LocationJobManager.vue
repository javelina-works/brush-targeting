<template>
  <div class="location-job-manager">
    <LocationList
      :locations="locations"
      :selectedLocation="selectedLocation"
      @select="selectLocation"
      @update-locations="locations = $event"
    />

    <div class="main-panel">
      <JobList
        v-if="selectedLocation"
        :jobs="jobs"
        :selectedLocation="selectedLocation"
        @select="selectJob"
        @update-jobs="jobs = $event"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useLocationStore } from "@/stores/locationStore";
import LocationList from "./LocationList.vue";
import JobList from "./JobList.vue";
import api from "@/api/axios.js";

const store = useLocationStore();
const selectedLocation = computed(() => store.selectedLocation);
const selectedJob = computed(() => store.selectedJob);

const locations = ref([]);
const jobs = ref([]);

async function fetchLocations() {
  try {
    // console.log("fetchLocations() called at:", new Date().toISOString());
    const res = await api.get("/api/locations/");
    locations.value = res.data ? res.data : []; // ✅ Safely assign fetched data

    console.log("Fetched locations:", locations.value);
  } catch (error) {
    console.error(
      "Error fetching locations:",
      error.response ? error.response.data : error.message
    );
  }
}

async function fetchJobs() {
  if (!selectedLocation.value) return;
  try {
    // console.log(`Fetching jobs for location: ${selectedLocation.value.id}`);
    const res = await api.get(
      `/api/jobs/?location_id=${selectedLocation.value.id}`
    );
    jobs.value = res.data ? res.data : []; // Safely fetch jobs list
    console.log("Fetched jobs:", jobs.value);
  } catch (error) {
    console.error(
      "Error fetching jobs:",
      error.response ? error.response.data : error.message
    );
  }
}

function selectLocation(location) {
  store.setLocation(location);
  // console.log("Storing new location", store.selectedLocation);
  fetchJobs();
}

function selectJob(job) {
  // console.log("Setting Job:", job); // Debug log
  store.setJob(job);
  // Navigate to the main app page with the selected job
  window.location.href = `/?location_id=${selectedLocation.value.id}&job_id=${job.id}`;
}

onMounted(async () => {
  // console.log("Component mounted at:", new Date().toISOString());
  // console.log("Pinia Store - Selected Location:", store.selectedLocation);
  // console.log("Pinia Store - Selected Job:", store.selectedJob);
  await fetchLocations(); // Fetch locations first
  if (selectedLocation.value) {
    await fetchJobs(); // Only fetch jobs if a location is selected
  }
});
</script>

<style scoped>
.location-job-manager {
  display: flex;
  height: 100vh;
}

.main-panel {
  flex-grow: 1;
  padding: 20px;
}

button {
  margin-bottom: 10px;
}
</style>
