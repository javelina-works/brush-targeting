<template>
    <CContainer>
        <CRow class="mt-4">
            <CCol>
                <CTabs activeItemKey="image">

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
                            <!-- <CFormInput type="range" v-model="threshold" min="0" max="1" step="0.05" /> -->
                            <p>Threshold: {{ threshold }}</p>
                            <img v-if="thresholdedImage" :src="thresholdedImage" class="img-fluid" />
                            <CButton color="warning" @click="applyThreshold">Apply Threshold</CButton>
                        </CTabPanel>

                        <CTabPanel class="p-3" itemKey="targets">
                            <h4>Detected Targets</h4>
                            <pre v-if="targets">{{ targets }}</pre>
                            <CButton color="danger" @click="generateTargets">Generate Targets</CButton>
                        </CTabPanel>
                    </CTabContent>

                </CTabs>
            </CCol>
        </CRow>
    </CContainer>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import api from '@/api/axios.js';
import { useLocationStore } from '@/stores/locationStore';
import {
    CTabs, CTabList, CTab, CTabContent, CTabPanel,
    CButton, CFormInput,
} from '@coreui/vue';


export default {
    setup() {
        const locationStore = useLocationStore();
        const locationId = computed(() => locationStore.selectedLocation?.id);
        const jobId = computed(() => locationStore.selectedJob?.id);
        const shouldQueryRun = computed(() => !!locationId.value && !!jobId.value);

        const originalImage = ref(null)
        const processedImage = ref(null)
        const thresholdedImage = ref(null)
        const targets = ref(null)
        const threshold = ref(0.5)

        const fetchOriginalImage = async () => {
            try {
                const response = await api.get(`/api/files/${jobId.value}/region_orthophoto.png`, {
                    responseType: 'blob' // Ensure treated as binary
                });
                if (response.status == 200) {
                    console.log("Response: ", response);
                    // originalImage.value = response.data; // Static path for now
                    originalImage.value = URL.createObjectURL(response.data); // Static path for now
                } else {
                    console.error("Failed to fetch image.");
                }
            } catch (error) {
                console.error("File Retreival Error:", error);
            }
        }

        const processCV = async () => {
            try {
                const response = await api.post(`/api/process_cv/${jobId}`, { method: 'POST' })
                if (response.ok) {
                    processedImage.value = URL.createObjectURL(await response.blob())
                } else {
                    console.error("Failed to process CV")
                }
            } catch (error) {
                console.error("Error:", error)
            }
        }

        const applyThreshold = async () => {
            try {
                const response = await api.post("/api/apply_threshold", {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ job_id: jobId, threshold: threshold.value })
                })
                if (response.ok) {
                    thresholdedImage.value = URL.createObjectURL(await response.blob())
                } else {
                    console.error("Thresholding failed")
                }
            } catch (error) {
                console.error("Error:", error)
            }
        }

        const generateTargets = async () => {
            try {
                const response = await api.post(`/api/generate_targets/${jobId}`, { method: 'POST' })
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

        onMounted(() => {
            fetchOriginalImage();
        })

        return { originalImage, processedImage, thresholdedImage, targets, threshold, fetchOriginalImage, processCV, applyThreshold, generateTargets }
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