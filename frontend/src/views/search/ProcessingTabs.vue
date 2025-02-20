<template>
    <CContainer>
        <CRow class="mt-4">
            <CCol>
                <!-- <CTabs activeItemKey="image" @change="onTabChange"> -->
                <CTabs activeItemKey="image" @change="(e) => console.log('Tab changed:', e)">

                    <CTabList variant="tabs">
                        <CTab itemKey="image">Original</CTab>
                        <CTab itemKey="preprocess">Preprocess</CTab>
                        <CTab itemKey="threshold">Threshold</CTab>
                        <CTab itemKey="targets">Targets</CTab>
                    </CTabList>

                    <CTabContent>
                        <CTabPanel class="p-3" itemKey="image">
                            <div class="text-center">
                                <h4>Original Orthophoto</h4>
                                <img v-if="originalImage" :src="originalImage" class="img-fluid" />
                                <CButton color="primary" @click="fetchOriginalImage">Refresh Image</CButton>
                            </div>
                        </CTabPanel>

                        <CTabPanel class="p-3 text-center" itemKey="preprocess">
                            <h4>CV Processed Image</h4>
                            <img v-if="processedImage" :src="processedImage" class="img-fluid" />
                            <CButton color="success" @click="processCV">Run CV Processing</CButton>
                        </CTabPanel>

                        <CTabPanel class="p-3" itemKey="threshold">
                            <h4>Thresholding</h4>
                            <label for="threshold_range">Masking Threshold: {{ threshold }}</label>
                            <CFormRange id="threshold_range" v-model="threshold" :min="0" :max="1" :step="0.01" />
                            <CButton color="warning" @click="applyThreshold">Apply Threshold</CButton>
                            <img v-if="thresholdedImage" :src="thresholdedImage" class="img-fluid" />
                        </CTabPanel>

                        <CTabPanel class="p-3" itemKey="targets">
                            <h4>Detected Targets</h4>
                            <pre v-if="targets">{{ targets }}</pre>
                            <CButton color="danger" @click="generateTargets">Generate Targets</CButton>
                            <CButton color="info" @click="activateMap">Refresh Map</CButton>
                            <BaseLeafletMap ref="leafletMap" />
                        </CTabPanel>
                    </CTabContent>

                </CTabs>
            </CCol>
        </CRow>
    </CContainer>
</template>

<script>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import api from '@/api/axios.js';
import { useLocationStore } from '@/stores/locationStore';
import { useMapData } from '@/api/graphql_queries';

import {
    CTabs, CTabList, CTab, CTabContent, CTabPanel,
    CButton, CFormRange,
} from '@coreui/vue';

import BaseLeafletMap from '@/components/LeafletMap/BaseLeafletMap.vue';
import { updateLayerData, getAllLayers } from '@/components/LeafletMap/layers';

export default {
    components: { BaseLeafletMap, CTabs },
    setup() {
        const locationStore = useLocationStore();
        const locationId = computed(() => locationStore.selectedLocation?.id);
        const jobId = computed(() => locationStore.selectedJob?.id);
        const shouldQueryRun = computed(() => !!locationId.value && !!jobId.value);

        const leafletMap = ref(null);

        const originalImage = ref(null);
        const processedImage = ref(null);
        const thresholdedImage = ref(null);
        const targets = ref(null);

        const thresholdRaw = ref(0.5);
        // 🔹 Convert to STRING for API, but keep internal as numbers
        const threshold = computed({
            get: () => String(thresholdRaw.value), // API receives a string
            set: (value) => (thresholdRaw.value = parseFloat(value)), // Store as float internally
        });

        const layers = ref([
            // "region_contour",
            "targets",
        ]);
        const { result: getResult, loading, error } = useMapData(locationId.value, jobId.value, layers.value);

        const activateMap = () => {
            console.log("Refreshing map! ", leafletMap.value.map);
            nextTick(() => {
                if (leafletMap.value?.map) {
                    leafletMap.value.map.invalidateSize();
                }
            });
        };

        /** API Calls and handling */

        const fetchImage = async (file_name) => {
            try {
                const response = await api.get(`/api/files/${jobId.value}/${file_name}`, {
                    responseType: 'blob' // Ensure treated as binary
                });
                if (response.status == 200) {
                    const objectURL = URL.createObjectURL(response.data);
                    return objectURL;
                } else {
                    console.error("Failed to fetch orgiginal image.");
                    return null;
                }
            } catch (error) {
                console.error("File Retreival Error:", error);
            }
        }

        const fetchOriginalImage = async () => {
            try {
                const image_name = "region_orthophoto.png";
                originalImage.value = await fetchImage(image_name);
            } catch (error) {
                console.error("Error getting original:", error);
            }
        }

        const processCV = async () => {
            try {
                const response = await api.post(`/api/process_cv/${jobId.value}`, { method: 'POST' })
                if (response.status == 200) {
                    console.log("Processing started, checking status... ", response.data["task_id"]);
                    checkStatus(response.data["task_id"]);
                } else {
                    console.error("Failed to start processing image.");
                }
            } catch (error) {
                console.error("Error:", error);
            }
        }

        const checkStatus = async (task_id) => {
            const interval = setInterval(async () => {
                try {
                    const response = await api.get(`/api/check_status/${jobId.value}/${task_id}`);
                    if (response.data.status === "complete") {
                        clearInterval(interval);
                        const produced_file = response.data.output_file;
                        await fetchProcessedImage(produced_file);
                    }
                } catch (error) {
                    console.error("Error checking status:", error);
                }
            }, 5000); // Poll every 5 seconds
        };

        const fetchProcessedImage = async (image_name = "processed_region.png") => {
            try {
                processedImage.value = await fetchImage(image_name);
            } catch (error) {
                console.error("Error getting processed:", error);
            }
        }

        const applyThreshold = async () => {
            try {
                const response = await api.post("/api/apply_threshold", {
                    job_id: jobId.value,
                    threshold: parseFloat(threshold.value)
                }, { responseType: 'blob' });
                if (response.status == 200) {
                    thresholdedImage.value = URL.createObjectURL(response.data)
                } else {
                    console.error("Thresholding failed")
                }
            } catch (error) {
                console.error("Error:", error)
            }
        }

        const generateTargets = async () => {
            try {
                const response = await api.post(`/api/generate_targets/${jobId.value}`, { method: 'POST' })
                if (response.ok) {
                    const data = await response.json()
                    targets.value = JSON.stringify(data.geojson, null, 2)
                } else {
                    console.error("Target generation failed")
                }
            } catch (error) {
                console.error("Error:", error)
            }
        }


        // Reactively process API data
        watch(
            () => getResult.value?.mapAssets,  // ✅ Only watches `mapAssets`
            (newAssets, oldAssets) => {
                if (error.value) {
                    console.error("GraphQL error:", error.value);
                }
                if (loading.value) {
                    console.log("Data is still loading...");
                }
                if (shouldQueryRun.value && newAssets) {
                    newAssets.forEach((asset) => {
                        updateLayerData(asset.name, asset.geojson);
                        // if (asset.name === "voronoi_cells") hasVoronoiCells.value = true;
                        // if (asset.name === "depot_points") hasDepots.value = true;
                    });
                }
            });


        onMounted(() => {
            // fetchOriginalImage();
            fetchProcessedImage();
        })

        return {
            originalImage,
            processedImage,
            thresholdedImage,
            targets,
            threshold,
            fetchOriginalImage,
            processCV,
            applyThreshold,
            generateTargets,
            BaseLeafletMap,
            leafletMap,
            activateMap,
        }
    }
}
</script>

<style scoped>
.img-fluid {
    max-width: 100%;
    height: auto;
    border: 2px solid #ddd;
    border-radius: 8px;
    margin-top: 10px;
}
</style>