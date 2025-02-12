<template>
    <div>
      <h1>Upload Files</h1>
      <p><strong>Project ID:</strong> {{ selectedLocation?.id || 'Not Found' }}</p>
      <p><strong>Job ID:</strong> {{ selectedJob?.id || 'Not Found' }}</p>
    </div>
  </template>
  
  <script>
  import { computed, onMounted } from 'vue';
  import { useLocationStore } from '@/stores/locationStore';
  
  export default {
    setup() {
      const store = useLocationStore();
  
      const selectedLocation = computed(() => store.selectedLocation);
      const selectedJob = computed(() => store.selectedJob);
  
        // Debugging: Log values when navigating
        onMounted(() => {
        console.log("Pinia Store - Selected Location:", store.selectedLocation);
        var obj = store.selectedLocation
        console.log(obj);
        console.log(JSON.stringify(store.selectedLocation));
        console.log("Pinia Store - Selected Job:", store.selectedJob);
        });

      return { selectedLocation, selectedJob };
    }
  };
  </script>
  