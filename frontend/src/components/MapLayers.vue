<script setup>
import { useQuery } from "@vue/apollo-composable";
import gql from "graphql-tag";  // ✅ Import gql from graphql-tag
import { ref, watch } from "vue";

const locationId = ref("6a9b0014-fa87-463d-9767-46cf5c762b9f");
const jobId = ref("0b8dd912-c4a6-4bd1-882e-c182bf120065");
const layers = ref(["region_outline", "targets"]);

const GET_MAP_ASSETS = gql`
  query GetMapAssets($locationId: String!, $jobId: String!, $layers: [String!]) {
    mapAssets(locationId: $locationId, jobId: $jobId, layers: $layers) {
      id
      name
      geojson
    }
  }
`;

const { result, loading, refetch } = useQuery(GET_MAP_ASSETS, {
  locationId: locationId.value,
  jobId: jobId.value,
  layers: layers.value,
});

// Auto-refetch when location/job changes
watch([locationId, jobId, layers], () => {
  refetch();
});
</script>

<template>
  <div>
    <h3>Map Layers</h3>
    <div v-if="loading">Loading...</div>
    <ul v-else>
      <li v-for="asset in result?.mapAssets" :key="asset.id">
        {{ asset.name }} (GeoJSON: {{ asset.geojson.substring(0, 50) }}...)
      </li>
    </ul>
  </div>
</template>
