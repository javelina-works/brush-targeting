<template>

    <CButton class="mb-3" color="success" @click="saveMapLayers">
        Save Map Layers
    </CButton>
    <p v-if="savingStatus" class="status-message">{{ savingStatus }}</p>

</template>

<script setup>
import { ref, computed } from "vue";
import { updateMapData } from "@/api/graphql_queries";
import { CButton } from "@coreui/vue";


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



function cleanDepotPointsLayer(depotLayer) {
    if (!depotLayer) {
        console.warn("⚠️ No depot_points layer found to clean!");
        return null;
    }
    //   console.log("🔍 Cleaning depot_points layer before saving...");
    depotLayer.eachLayer((group) => {
        group.eachLayer((subLayer) => {
            if (!subLayer.feature) {
                // console.log("🗑️ Removing empty sublayer:", subLayer);
                group.removeLayer(subLayer); // Remove unwanted sublayers
            }
        });
    });
    return depotLayer;
}


function getCleanedActiveLayers(layersToSave = []) {
    if (!mapLayers.value) {
        console.warn("⚠️ No map layers available!");
        return {};
    }

    const cleanedLayers = {};

    /** ✅ If no layers are specified, default to active layers */
    const layersToProcess = layersToSave.length > 0
        ? layersToSave
        : Object.keys(mapLayers.value).filter(layerName => {
            const layer = mapLayers.value[layerName];
            return layer && layer.toGeoJSON && layer.toGeoJSON().features.length > 0;
        });

    /** ✅ Process only the selected or active layers */
    layersToProcess.forEach((layerName) => {
        const layer = mapLayers.value[layerName];

        // Skip layers with no features
        if (!layer || !layer.toGeoJSON || layer.toGeoJSON().features.length === 0) {
            return;
        }

        // 🔹 Call the separate depot cleaning function
        if (layerName === "depot_points") {
            cleanedLayers[layerName] = cleanDepotPointsLayer(layer);
        } else {
            cleanedLayers[layerName] = layer;
        }
    });

    return cleanedLayers;
}



/** ✅ Save Function */
async function saveMapLayers() {
    savingStatus.value = "Saving...";

    const cleanedLayers = getCleanedActiveLayers(props.layersToSave || []);
    if (Object.keys(cleanedLayers).length === 0) {
        console.error("⚠️ No map layers available to save!");
        savingStatus.value = "❌ No layers to save.";
        return;
    }

    const geojsonFiles = Object.keys(cleanedLayers)
        .map(layerName => ({
            name: layerName,
            geojson: JSON.stringify(cleanedLayers[layerName].toGeoJSON()),
        }));

    console.log("✅ Saving layers:", geojsonFiles);

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
.status-message {
    font-size: 14px;
    color: white;
    background-color: rgba(0, 0, 0, 0.7);
    padding: 5px 10px;
    border-radius: 5px;
}
</style>
