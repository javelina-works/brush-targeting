import { gql } from "graphql-tag";
import { useQuery, useMutation } from "@vue/apollo-composable";


const GET_MAP_ASSETS = gql`
  query GetMapAssets($locationId: String!, $jobId: String!, $layers: [String!]) {
    mapAssets(locationId: $locationId, jobId: $jobId, layers: $layers) {
      id
      name
      geojson
    }
  }
`;

const UPDATE_GEOJSON_FILES = gql`
  mutation updateMapAssets($locationId: String!, $jobId: String!, $geojsonFiles: [GeoJSONInput!]!) {
      updateMapAssets(locationId: $locationId, jobId: $jobId, geojsonFiles: $geojsonFiles) {
          updatedAssets {
              id
              name
              geojson
          }
          errorMessage
      }
  }
`;

const GENERATE_TESSELLATION = gql`
  mutation getTesselation($locationId: String!, $jobId: String!, $targetAreaAcres: Float!, $maxIterations: Int!) {
      generateTesselation(locationId: $locationId, jobId: $jobId, targetAreaAcres: $targetAreaAcres, maxIterations: $maxIterations) {
        id
        name
        type
        geojson
      }
  }
`;

const GENERATE_DEPOTS = gql`
  mutation GenerateDepots($locationId: String!, $jobId: String!, $depotRadius: Float!, $gridDensity: Int!) {
    generateDepots(locationId: $locationId, jobId: $jobId, depotRadius: $depotRadius, gridDensity: $gridDensity) {
        id
        name
        type
        geojson
    }
  }
`;



// GraphQL API handlers
export function useMapData(locationId, jobId, layers) {
  return useQuery(GET_MAP_ASSETS, { 
      locationId, 
      jobId, 
      layers 
  });
}

export function updateMapData(locationId, jobId, geojsonFiles) {
  return useMutation(UPDATE_GEOJSON_FILES, {
    locationId,
    jobId,
    geojsonFiles
  });
}
  
export function useTessellationMutation(locationId, jobId, targetAreaAcres, maxIterations) {
    return useMutation(GENERATE_TESSELLATION, {
        locationId, 
        jobId,
        targetAreaAcres,
        maxIterations
    });
}
  
  export function useDepotsMutation(locationId, jobId, depotRadius, gridDensity) {
    return useMutation(GENERATE_DEPOTS, {
        locationId, 
        jobId,
        depotRadius,
        gridDensity
    });
}
