<template>
    <div>
        <button @click="saveMapLayers">Save Map Layers</button>
        <p v-if="savingStatus" class="status-message">{{ savingStatus }}</p>
    </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { updateMapData } from "@/api/graphql_queries";


/** Props: Pass in the Base Map Reference */
const props = defineProps({
    baseMap: Object, // Reference to BaseLeafletMap.vue
    locationId: String,
    jobId: String,
    layersToSave: Array, // Optional: Only save these layers
});

/** Apollo Mutation */
const { mutate: updateMapAssets, error: updateError } = updateMapData();
const savingStatus = ref(null);

const mapLayers = computed(() => props.baseMap?.mapLayers);

// Function to Determine Active Layers
const getActiveLayers = () => {
  if (!mapLayers.value) {
    console.warn("⚠️ No map layers available!");
    return [];
  }

  return Object.keys(mapLayers.value)
    .filter(layerName => {
      const layer = mapLayers.value[layerName];
      return layer && layer.toGeoJSON && layer.toGeoJSON().features.length > 0; // ✅ Only save layers with features
    });
};

/** ✅ Save Function */
async function saveMapLayers() {
    savingStatus.value = "Saving...";

    const activeLayers = getActiveLayers();
    if (activeLayers.length === 0) {
        console.error("⚠️ No map layers available to save!");
        savingStatus.value = "❌ No layers to save.";
        return;
    }

    const selectedLayers = props.layersToSave && props.layersToSave.length > 0
        ? props.layersToSave
        : activeLayers; // Default to all layers if none specified

    console.log("✅ Saving layers:", selectedLayers);

    const geojsonFiles = selectedLayers
        .filter(layerName => mapLayers.value[layerName])
        .map(layerName => ({
            name: layerName,
            geojson: JSON.stringify(mapLayers.value[layerName].toGeoJSON()),
        }));

    if (geojsonFiles.length === 0) {
        savingStatus.value = "⚠️ No changes to save.";
        return;
    }

    try {
        const { data } = await updateMapAssets({
            locationId: props.locationId,
            jobId: props.jobId,
            geojsonFiles
        });

        if (data?.updateMapAssets?.errorMessage) {
            console.error("Error saving layers:", data.updateMapAssets.errorMessage);
            savingStatus.value = `⚠️ Some files failed: ${data.updateMapAssets.errorMessage}`;
        } else {
            savingStatus.value = "✅ All changes saved!";
        }
    } catch (err) {
        console.error("❌ Save API call failed:", err);
        savingStatus.value = "❌ Save failed.";
    }
}
</script>

<style scoped>
button {
    padding: 8px 12px;
    background-color: #28a745;
    color: white;
    border: none;
    cursor: pointer;
    font-size: 14px;
}

button:hover {
    background-color: #218838;
}

.status-message {
    font-size: 14px;
    color: white;
    background-color: rgba(0, 0, 0, 0.7);
    padding: 5px 10px;
    border-radius: 5px;
}
</style>
