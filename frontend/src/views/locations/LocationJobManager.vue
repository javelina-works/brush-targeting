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
  
      <CreateLocationModal :isVisible="showCreateLocation" @close="showCreateLocation = false" @created="fetchLocations"/>
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
      const locations = ref([]);
      const jobs = ref([]);
      const showCreateLocation = ref(false);
      const showCreateJob = ref(false);
      const store = useLocationStore();
  
      const selectedLocation = computed(() => store.selectedLocation);
      const selectedJob = computed(() => store.selectedJob);
  
      async function fetchLocations() {
        const res = await api.get('/api/locations/');
        locations.value = res.data;
      }
  
      async function fetchJobs() {
        if (selectedLocation.value) {
          const res = await api.get(`/api/jobs/?location_id=${selectedLocation.value.id}`);
          jobs.value = res.data;
        }
      }
  
      function selectLocation(location) {
        store.setLocation(location);
        fetchJobs();
      }
  
      function selectJob(job) {
        console.log("Setting Job:", job); // Debug log
        store.setJob(job);
        // Navigate to the main app page with the selected job
        window.location.href = `/?location_id=${selectedLocation.value.id}&job_id=${job.id}`;
      }
  
      onMounted(fetchLocations);
  
      return { locations, jobs, selectedLocation, selectedJob, selectLocation, selectJob, fetchLocations, fetchJobs, showCreateLocation, showCreateJob };
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
    background: #f4f4f4;
  }
  .main-panel {
    flex-grow: 1;
    padding: 20px;
  }
  button {
    margin-bottom: 10px;
  }
  </style>
  