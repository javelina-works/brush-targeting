<template>
    <div class="map-container" ref="mapContainer"></div>
</template>
  
<script setup>
  import { ref, watch, onMounted } from 'vue';
  import L from 'leaflet';
  import { useQuery } from '@vue/apollo-composable';
  import gql from 'graphql-tag';
  import 'leaflet/dist/leaflet.css';
  
  /** ✅ References */
  const mapContainer = ref(null);
  let map = null;
  const geojsonLayers = {}; // Dictionary to store actual Leaflet layers
  let layerControl = null;
  
  /** API Parameters */
  const locationId = ref("6a9b0014-fa87-463d-9767-46cf5c762b9f");
  const jobId = ref("0b8dd912-c4a6-4bd1-882e-c182bf120065");
  const layers = ref([
    "region_contour", 
    "removed_targets",
    "approved_targets"
    ]);
  
  /** GraphQL Query */
  const GET_MAP_ASSETS = gql`
    query GetMapAssets($locationId: String!, $jobId: String!, $layers: [String!]) {
      mapAssets(locationId: $locationId, jobId: $jobId, layers: $layers) {
        id
        name
        geojson
      }
    }
  `;

    /** Fetch GeoJSON Data */
    const { result } = useQuery(GET_MAP_ASSETS, {
        locationId: locationId.value,
        jobId: jobId.value,
        layers: layers.value
    });

  
  /** ✅ Initialize Leaflet Map */
  onMounted(() => {
    map = L.map(mapContainer.value).setView([30.2506, -103.6035], 14);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);
  
    L.control.scale().addTo(map);
    layerControl = L.control.layers(null, {}).addTo(map);

    console.log("✅ Map Initialized, waiting for API data...");
  });


const layerFactory = {
    region_contour: () => L.geoJSON(null, {
        style: { color: "blue", weight: 2, fillOpacity: 0.1 },
    }),
    approved_targets: () => L.geoJSON(null, {
        pointToLayer: (feature, latlng) => L.circleMarker(latlng, { color: "blue", radius: 5 }),
        onEachFeature: (feature, layer) => {
        layer.bindPopup(`<b>Approved Target</b><br>ID: ${feature.properties.id}`);
        },
    }),
    removed_targets: () => L.geoJSON(null, {
        pointToLayer: (feature, latlng) => L.circleMarker(latlng, { color: "red", radius: 5 }),
        onEachFeature: (feature, layer) => {
        layer.bindPopup(`<b>Removed Target</b><br>ID: ${feature.properties.id}`);
        },
    }),
    default: () => L.geoJSON(null, {
        pointToLayer: (feature, latlng) => L.circleMarker(latlng, { color: "gray", radius: 5 }),
        onEachFeature: (feature, layer) => {
        layer.bindPopup(`<b>Unknown Layer</b><br>ID: ${feature.properties?.id || "N/A"}`);
        },
    }),
};

// Function to initialize layers
function initLayers() {
  Object.keys(layerFactory).forEach(name => {
    geojsonLayers[name] = layerFactory[name]();
    geojsonLayers[name].addTo(map); // Assuming `map` is your Leaflet instance
  });
}

// Function to update a specific layer with new data
function updateLayer(name, geojsonData) {
  if (geojsonLayers[name]) {
    geojsonLayers[name].clearLayers(); // Clear existing features
    geojsonLayers[name].addData(geojsonData);
  }
}

/** ✅ Watch for API Data and Update Layers */
watch(result, (newData) => {
  if (!newData || !newData.mapAssets) return;
  console.log("📡 API Data Received:", newData.mapAssets);

  newData.mapAssets.forEach(asset => {
    try {
      const parsedGeoJson = JSON.parse(asset.geojson); // ✅ Convert JSON string to object
      const name = asset.name

      if (geojsonLayers[name]) {
        updateLayer(name, parsedGeoJson);
      } else {
        // If a new layer type appears, initialize it dynamically
        geojsonLayers[name] = (layerFactory[name] || layerFactory.default)();
        geojsonLayers[name].addTo(map);
        updateLayer(name, parsedGeoJson);
        layerControl.addOverlay(geojsonLayers[name], name);
      }
    } catch (error) {
      console.error(`❌ Error parsing GeoJSON for ${asset.name}:`, error);
    }
  });
});


</script>
  
  <style scoped>
  .map-container {
    width: 100%;
    height: 100vh;
  }
</style>
  