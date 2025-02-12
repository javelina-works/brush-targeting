<template>
    <div class="location-job-manager">
      <div class="sidebar">
        <h2>Locations</h2>
        <button @click="showCreateLocation = true">+ New Location</button>
        <LocationList 
          :locations="locations" 
          :selectedLocation="selectedLocation" 
          @select="selectLocation" 
        />
      </div>
  
      <div class="main-panel">
        <h2 v-if="selectedLocation">
          Jobs for {{ selectedLocation.name }}
        </h2>
        <button v-if="selectedLocation" @click="showCreateJob = true">
          + New Job
        </button>
        <JobList 
          v-if="selectedLocation" 
          :jobs="jobs" 
          @select="selectJob" 
        />
      </div>
  
      <CreateLocationModal :isVisible="showCreateLocation" @close="handleLocationModalClose" />
      <CreateJobModal :isVisible="showCreateJob" :locationId="selectedLocation?.id" @close="showCreateJob = false" @created="fetchJobs"/>
    </div>
  </template>
  
  <script>
  import { ref, onMounted, computed } from 'vue';
  import { useLocationStore } from '@/stores/locationStore';
  import LocationList from './LocationList.vue';
  import JobList from './JobList.vue';
  import CreateLocationModal from './CreateLocationModal.vue';
  import CreateJobModal from './CreateJobModal.vue';
  import api from '@/api/axios.js';
  
  export default {
    components: { LocationList, JobList, CreateLocationModal, CreateJobModal },
    setup() {
      const store = useLocationStore();
      const locations = ref([]);
      const jobs = ref([]);
      const showCreateLocation = ref(false);
      const showCreateJob = ref(false);
  
      const selectedLocation = computed(() => store.selectedLocation);
      const selectedJob = computed(() => store.selectedJob);
  
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

      async function fetchJobs() {
        if (!selectedLocation.value) return;
        try {
          // console.log(`Fetching jobs for location: ${selectedLocation.value.id}`);
          const res = await api.get(`/api/jobs/?location_id=${selectedLocation.value.id}`);
          jobs.value = res.data;
          // console.log("Fetched jobs:", jobs.value);
        } catch (error) {
          console.error("Error fetching jobs:", error.response ? error.response.data : error.message);
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
  
      function handleLocationModalClose() {
        showCreateLocation.value = false;
        console.log("Fetching locations after modal closes...");
        fetchLocations(); // Fetch only after closing
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
  
      return { locations, jobs, selectedLocation, selectedJob, selectLocation, selectJob, handleLocationModalClose, fetchLocations, fetchJobs, showCreateLocation, showCreateJob };
    }
  };
  </script>
  
  <style scoped>
  .location-job-manager {
    display: flex;
    height: 100vh;
  }
  .sidebar {
    width: 30%;
    padding: 20px;
  }
  .main-panel {
    flex-grow: 1;
    padding: 20px;
  }
  button {
    margin-bottom: 10px;
  }
  </style>
  