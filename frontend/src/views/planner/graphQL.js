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

const GENERATE_TESSELLATION = gql`
  mutation GenerateTessellation($locationId: String!, $jobId: String!, $targetAreaAcres: Float!, $maxIterations: Int!) {
    generateTesselation(locationId: $locationId, jobId: $jobId, targetAreaAcres: $targetAreaAcres, maxIterations: $maxIterations) {
      geojson
    }
  }
`;

const GENERATE_DEPOTS = gql`
  mutation GenerateDepots($locationId: String!, $jobId: String!) {
    generateDepots(locationId: $locationId, jobId: $jobId) {
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
  
export function useTessellationMutation(locationId, jobId) {
    return useMutation(GENERATE_TESSELLATION, {
        locationId, 
        jobId,
    });
}
  
  export function useDepotsMutation(locationId, jobId) {
    return useMutation(GENERATE_DEPOTS, {
        locationId, 
        jobId,
    });
}
