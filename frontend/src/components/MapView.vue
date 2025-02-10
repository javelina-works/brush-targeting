<template>
    <div id="map"></div>
  </template>
  
  <script>
  import { onMounted, ref } from 'vue';
  import L from 'leaflet';
  
  export default {
    name: 'MapView',
    setup() {
        const map = ref(null);
        const targetMarkers = ref([]);

        const fetchTargets = async () => {
            try {
                const response = await fetch("http://localhost:8000/api/targets");
                const data = await response.json();

                console.log("Fetched targets:", data); // debug fetched points

                targetMarkers.value = data;
                
                // Ensure map is loaded
                if (!map.value) return;

                // Add markers to the map
                data.forEach(target => {
                    console.log(`Adding marker at: ${target.lat}, ${target.lng}`); // ✅ Debug log

                    L.marker([target.lat, target.lng])
                        .addTo(map.value)
                        .bindPopup(`<b>${target.name}</b>`);
                });

            } catch (error) {
                console.error("Error fetching targets:", error);
            }
        };

        onMounted(() => {
            map.value = L.map('map', {
                center: [37.7749, -122.4194], // Default: San Francisco
                zoom: 10,
            });
    
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; OpenStreetMap contributors',
                detectRetina: true,
            }).addTo(map.value);
    

            fetchTargets(); // Fetch targets after map is initialized

            // Fix misaligned tiles
            setTimeout(() => {
                map.value.invalidateSize(); // Fixes potential rendering issues (unconfirmed)
            }, 500);
        });

        return { targetMarkers };
    },
  };
  </script>
  
  <style>
  #map {
    width: 100%;
    height: 500px;
    min-height: 400px;
    max-width: 800px;
    margin: 0 auto;
  }
  </style>
  