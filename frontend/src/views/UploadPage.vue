<template>
    <div>
      <h1>Upload Files</h1>
      <p><strong>Project ID:</strong> {{ selectedLocation?.id }}</p>
      <p><strong>Job ID:</strong> {{ selectedJob?.id }}</p>
    </div>
  </template>
  
  <script>
  import { computed, watch } from 'vue';
  import { useLocationStore } from '@/stores/locationStore';
  
  export default {
    setup() {
      const store = useLocationStore();
  
      const selectedLocation = computed(() => store.selectedLocation);
      const selectedJob = computed(() => store.selectedJob);
  
    // Debugging: Watch for changes and log them
    watch([selectedLocation, selectedJob], ([loc, job]) => {
        console.log("Updated Location:", loc);
        console.log("Updated Job:", job);
    });

      return { selectedLocation, selectedJob };
    }
  };
  </script>
  