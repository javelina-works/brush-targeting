/**
 * layerManager.js
 * ===============
 *
 * Functions to save, refresh, and update leaflet.js map layers.
 * Performs API calls and handles data in the background.
 */
import { ref, watch } from "vue";
import { useMapData, updateMapData } from "@/api/graphql_queries";
import { updateLayerData, getAllLayers } from "./layers";

/**
 * Composable function to fetch and manage Leaflet map layers.
 * @param {String} locationId - The location ID
 * @param {String} jobId - The job ID
 * @param {Array} layerNames - List of names of layers to fetch
 * @param {Object} layerControl - [reference] Leaflet layer control
 * @param {Object} mapLayers - [reference] Leaflet map layers
 */
export function useMapLayers(
  locationId,
  jobId,
  layerNames,
  layerControl,
  mapLayers
) {
  // perform GraphQL API query
  const { result, refetch, loading, error, onResult } = useMapData(
    locationId,
    jobId,
    layerNames
  );

  /**
   * Intitialize GraphQL watcher
   * -> Automatically updates map layers when data is updated
   */
  onResult((newAssets) => {
    // console.log("📡 Map data updated:", newAssets);

    if (error.value) {
      console.error("GraphQL error:", error.value);
    }
    if (loading.value) {
      console.log("Data is still loading...");
    }

    if (!newAssets?.data?.mapAssets) return;
    if (!mapLayers || !layerControl.value) return;

    newAssets.data.mapAssets.forEach((asset) => {
      if (mapLayers[asset.name]) {
        layerControl.value.removeLayer(mapLayers[asset.name]);
      }
      updateLayerData(asset.name, asset.geojson);
      layerControl.value.addOverlay(mapLayers[asset.name], asset.name);
    });
  });

  return {
    loading,
    error,
    refetch, // ✅ Allows manual refresh
  };
}

/**
 *
 * @param {String} locationId - The location ID
 * @param {String} jobId - The job ID
 * @param {Array} saveLayers
 * @returns
 */
export function useSaveMapLayers(
  locationId,
  jobId,
  saveLayers // Pass layer names to save
) {
  // Init GraphQL mutation call
  const savingStatus = ref(null);
  const { mutate: updateMapAssets, error: updateError } = updateMapData();

  async function saveMapLayers(locationId, jobId, saveLayers) {
    savingStatus.value = "Saving...";
    const geojsonLayers = getAllLayers();
    const geojsonFiles = saveLayers
      .filter((layerName) => geojsonLayers[layerName]) // Ensure layer exists
      .map((layerName) => ({
        name: layerName,
        geojson: JSON.stringify(geojsonLayers[layerName].toGeoJSON()),
      }));

    if (geojsonFiles.length === 0) {
      savingStatus.value = "⚠️ No files to save.";
      return;
    }

    // Perform GraphQL mutation API call
    try {
      const { data } = await updateMapAssets({
        locationId: locationId,
        jobId: jobId,
        geojsonFiles: geojsonFiles,
      });

      if (data.error) {
        console.error("Error saving layers:", updateError);
      }

      if (updateError.value) {
        console.error("Save API error:", updateError.value);
        savingStatus.value = `⚠️ Some files failed: ${response.data.updateMapAssets.errorMessage}`;
        alert("Failed to save layers!");
      } else {
        console.log("Layers successfully saved:", data);
        savingStatus.value = "✅ All changes saved!";
        // alert("Map layers saved successfully!");
      }
    } catch (err) {
      console.error("❌ Save API call failed:", err);
      alert("An unexpected error occurred while saving.");
      savingStatus.value = `⚠️ Save files failed: ${err}`;
    }
  }

  return { saveMapLayers, savingStatus, updateError };
}
