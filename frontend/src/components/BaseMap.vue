<template>
    <div class="map-container" ref="mapContainer"></div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue';
  import L from 'leaflet';
  import 'leaflet/dist/leaflet.css';
  
  /** Map container reference */
  const mapContainer = ref(null);
  const map = ref(null);
  
  /** Initialize Leaflet Map */
  onMounted(() => {
    map.value = L.map(mapContainer.value).setView(
        [30.2506, -103.6035], 
        13
    );
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map.value);

    L.control.scale().addTo(map.value)

  });
  
  /** Expose map instance */
  defineExpose({ map });
  </script>
  
  <style scoped>
  .map-container {
    width: 100%;
    height: 100vh;
  }
  </style>
  