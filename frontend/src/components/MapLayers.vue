<template></template>

<script setup>
import { watch, ref, onMounted } from 'vue';
import L from 'leaflet';

/** Props from parent (AuditPage) */
const props = defineProps({
  map: Object,  // The Leaflet map instance
  layers: Array // The layers to add/remove dynamically
});

const geoJsonLayers = ref([]);

/** Watch for Layer Changes */
watch(() => props.layers, (newLayers) => {
  console.log("📡 New Layers Received:", newLayers);
  if (!props.map) {
    console.error("⚠️ Map instance is undefined!");
    return;
  }

  // Remove previous layers
  geoJsonLayers.value.forEach(layer => props.map.removeLayer(layer));
  geoJsonLayers.value = [];

  // Add new layers
  newLayers.forEach(layer => {
    try {
      const geoJsonLayer = L.geoJSON(JSON.parse(layer.geojson), {
        style: () => layer.style,
        pointToLayer: (feature, latlng) => {
          if (layer.name === "targets") {
            return L.circleMarker(latlng, {
              radius: 6,
              fillColor: "blue",
              color: "black",
              weight: 1,
              opacity: 0.5,
              fillOpacity: 0.3
            });
          }
          return L.marker(latlng);
        }
      }).addTo(props.map);

      geoJsonLayers.value.push(geoJsonLayer);
    } catch (error) {
      console.error(`Error parsing GeoJSON for layer ${layer.name}:`, error);
    }
  });
}, { deep: true });
</script>
