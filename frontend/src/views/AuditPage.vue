<template>
    <BaseMap ref="baseMap" />
    <MapLayers v-if="mapReady" :map="baseMap.map" :layers="filteredLayers" />
  </template>
  
  <script setup>
  import { ref, watch, computed } from 'vue';
  import BaseMap from '@/components/BaseMap.vue';
  import MapLayers from '@/components/MapLayers.vue';
  import MapControls from '@/components/MapControls.vue';
  import { useQuery } from '@vue/apollo-composable';
  import gql from 'graphql-tag';
  
  /** Reference to BaseMap */
  const baseMap = ref(null);
  const mapReady = ref(false); // ✅ Ensure map is ready before loading layers
  
  /** API Parameters */
  const locationId = ref("6a9b0014-fa87-463d-9767-46cf5c762b9f");
  const jobId = ref("0b8dd912-c4a6-4bd1-882e-c182bf120065");
  const layers = ref(["region_contour", "targets"]);
  
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
  
  /** Fetch GeoJSON Layers */
  const geojsonLayers = ref([]);
  const activeLayerNames = ref(["region_contour", "targets"]);
  
  const { result } = useQuery(GET_MAP_ASSETS, {
    locationId: locationId.value,
    jobId: jobId.value,
    layers: layers.value,
  });
  
  /** Watch for map readiness */
  watch(() => baseMap.value?.map, (newMap) => {
    if (newMap) {
        console.log("Base map is ready!");
      mapReady.value = true;  // ✅ Mark map as ready
    }
  });
  
  /** Process API Data */
  watch(result, (newData) => {
  if (newData && newData.mapAssets) {
    geojsonLayers.value = newData.mapAssets.map(asset => {
      try {
        const parsedData = JSON.parse(asset.geojson);
        console.log(`✅ Successfully Parsed ${asset.name} GeoJSON:`, parsedData);

        return {
          name: asset.name,
          geojson: asset.geojson,
          style: getLayerStyle(asset.name)
        };
      } catch (error) {
        console.error(`❌ Error parsing JSON for ${asset.name}:`, error);
        return null;
      }
    }).filter(layer => layer !== null);
  }
});
  
  /** ✅ Define Layer Styling */
  const getLayerStyle = (layerName) => {
    const styles = {
      "region_contour": { color: "blue", weight: 2 },
      "targets": { color: "red", weight: 2 }
    };
    return styles[layerName] || { color: "gray", weight: 1 };
  };
  
  /** Filter Layers Based on Active Toggles */
  const filteredLayers = computed(() => 
    geojsonLayers.value.filter(layer => activeLayerNames.value.includes(layer.name))
  );

  /** Debug filtered layers */
watch(filteredLayers, (newLayers) => {
  console.log("🗺️ Filtered Layers Ready for Map:", newLayers);
});
  
  /** Handle Toggle Updates */
  const updateActiveLayers = (newActiveLayers) => {
    activeLayerNames.value = newActiveLayers;
  };
  
  /** Handle Editing Mode */
  const enableEditing = () => {
    console.log("Editing mode enabled!");
  };
  </script>
  