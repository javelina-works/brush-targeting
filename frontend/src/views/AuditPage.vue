<template>
    <BaseMap
      :layers="geojsonLayers"
      :center="center"
      @update:center="center = $event"
    />
</template>
  
  <script setup>
  import { ref, watch } from 'vue';
  import BaseMap from '@/components/BaseMap.vue';
  import { useQuery } from '@vue/apollo-composable';
  import gql from 'graphql-tag';
  
  /** Local State for Zoom & Center */
  const center = ref([30.2506, -103.6035]);
  
  /** API Parameters */
  const locationId = ref("6a9b0014-fa87-463d-9767-46cf5c762b9f");
  const jobId = ref("0b8dd912-c4a6-4bd1-882e-c182bf120065");
  const layers = ref([
    "region_contour", 
    "targets"
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
  
  /** Fetch GeoJSON Layers */
  const geojsonLayers = ref([]);
  const { result, loading, refetch } = useQuery(GET_MAP_ASSETS, {
    locationId: locationId.value,
    jobId: jobId.value,
    layers: layers.value,
  });
  
/** Process API Data */
watch(result, (newData) => {
  if (newData && newData.mapAssets) {
    geojsonLayers.value = newData.mapAssets.map(asset => {
      try {
        return {
          name: asset.name,
          data: JSON.parse(asset.geojson),  // ✅ Fix: Parse JSON string into an object
          style: getLayerStyle(asset.name),
        };
      } catch (error) {
        console.error(`Error parsing GeoJSON for layer ${asset.name}:`, error);
        return null;  // Skip invalid layers
      }
    }).filter(layer => layer !== null);  // Remove failed layers
  }
});
  
  /** Define Layer Styles Dynamically */
  const getLayerStyle = (layerName) => {
    const styles = {
      "region_contour": { color: "blue", 'fillOpacity': 0.05, weight: 2 },
      "targets": { color: "red", weight: 2 }
    };
    return styles[layerName] || { color: "gray", weight: 1 };
  };
  </script>
  