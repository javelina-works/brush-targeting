<template>

        <CButton class="mb-3" color="info" @click="refreshMapData">
            Refresh Map Data
        </CButton>
        <p v-if="refreshStatus" class="status-message">{{ refreshStatus }}</p>

</template>

<script setup>
import { ref, computed } from "vue";
import { CButton } from "@coreui/vue";

/** Props: Pass in the Base Map Reference */
const props = defineProps({
    baseMap: Object, // Reference to BaseLeafletMap.vue
});


const refreshStatus = ref(null);
const refetch = computed(() => props.baseMap?.refetch);

/** ✅ Refresh Function */
async function refreshMapData() {
    if (!refetch.value) {
        console.warn("⚠️ No refetch function available from BaseLeafletMap!");
        refreshStatus.value = "❌ Unable to refresh.";
        return;
    }

    refreshStatus.value = "🔄 Refreshing map data...";

    try {
        await refetch.value();
        refreshStatus.value = "✅ Map data refreshed!";
    } catch (err) {
        console.error("❌ Refresh API call failed:", err);
        refreshStatus.value = "❌ Failed to refresh map data.";
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
