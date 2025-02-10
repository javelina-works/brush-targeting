<template>
    <div class="map-container" ref="mapContainer"></div>
  </template>
  
  <script setup>
  import { defineProps, ref, watch, onMounted } from 'vue';
  import L from 'leaflet';
  import 'leaflet/dist/leaflet.css';
  
  /** Props */
  const props = defineProps({
    layers: Array,  // Layers to display
    center: { type: Array, default: () => [37.7749, -122.4194] }
  });
  
  const mapContainer = ref(null);
  let map = null;
  let geoJsonLayers = [];
  
  /** Initialize Leaflet Map */
  onMounted(() => {
    map = L.map(mapContainer.value).setView(props.center, 13);
  
    // Add Tile Layer (OpenStreetMap)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);
  
    // Watch for layer changes
    watch(() => props.layers, (newLayers) => updateGeoJsonLayers(newLayers), { deep: true });
  
    // Load initial layers
    updateGeoJsonLayers(props.layers);
  });
  
  /** Function to Update GeoJSON Layers */
  const updateGeoJsonLayers = (newLayers) => {
    // Remove old layers before adding new ones
    geoJsonLayers.forEach(layer => map.removeLayer(layer));
    geoJsonLayers = [];
  
    newLayers.forEach(layer => {
      try {
        const geoJsonLayer = L.geoJSON(layer.data, {
          style: () => layer.style, // Ensure styling is applied as function
          /** ✅ Custom Point Style: Convert markers to circles */
        pointToLayer: (feature, latlng) => {
          if (layer.name === "targets") {
            return L.circleMarker(latlng, {
              radius: 6,          // ✅ Circle size
              fillColor: "blue",  // ✅ Fill color
              color: "black",      // ✅ Border color
              weight: 1,          // ✅ Border weight
              opacity: 0.5,       // ✅ Border opacity
              fillOpacity: 0.3    // ✅ Fill opacity
            });
          }
          return L.marker(latlng); // Default for other point layers
        },
          onEachFeature: (feature, layer) => {
            layer.on('click', (e) => {
              console.log("Feature Clicked:", feature, e.latlng);
            });
          }
        }).addTo(map);
        geoJsonLayers.push(geoJsonLayer);
      } catch (error) {
        console.error("Error adding GeoJSON layer:", error);
      }
    });
  };
  </script>
  
  <style scoped>
  .map-container {
    width: 100%;
    height: 100vh;
  }
  </style>
  