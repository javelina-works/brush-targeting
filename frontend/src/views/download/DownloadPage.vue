<template>
    <CCard class="mx-auto mt-4" style="max-width: 600px">
        <CCardHeader class="text-lg font-semibold">Download Files for Job {{ jobId }}</CCardHeader>
        <CCardBody>
            <div v-if="files?.length === 0">
                Loading files...
            </div>
            <div v-else>
                <FilesList :files="files" @update:selectedFiles="updateSelectedFiles" />

                <CButton color="primary" class="mt-3" @click="downloadZip" :disabled="selectedFiles.size === 0">
                    Download Selected Files
                </CButton>
            </div>
        </CCardBody>
    </CCard>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue';
import { useLocationStore } from '@/stores/locationStore';
import api, { apiBaseURL } from '@/api/axios.js';

import FilesList from './FilesList.vue';

/** References */
const locationStore = useLocationStore();
const locationId = computed(() => locationStore.selectedLocation?.id);
const jobId = computed(() => locationStore.selectedJob?.id);

const files = ref([]); // Stores the job's file list
const selectedFiles = ref(new Set()); // Tracks selected files

// Fetch files for the selected job
const fetchFiles = async () => {
    try {
        const response = await api.get(`/api/files/${jobId.value}`);
        files.value = response.data;
        // console.log("Files: ", files.value);
    } catch (error) {
        console.error("Error fetching files:", error);
    }
};

// Update selected files
const updateSelectedFiles = (newSelection) => {
    selectedFiles.value = newSelection;
};

// Generate a ZIP and download
const downloadZip = async () => {
    if (selectedFiles.value.size === 0) {
        alert("No files selected for download.");
        return;
    }

    try {
        console.log("Files params: ", selectedFiles.value);
        // const response = await api.post(`/api/download/${jobId.value}/zip`, {
        //     selected_files: selectedFiles.value
        // }, {
        //     responseType: "blob",
        //     headers: { "Content-Type": "application/json" },
        // });
        // const response = await fetch(`${apiBaseURL}/api/download/${jobId.value}/zip`, {
        //     method: "POST",
        //     headers: { "Content-Type": "application/json" },
        //     body: JSON.stringify({ selected_files: selectedFiles.value }),
        // });

        // if (!response.ok) {
        //     throw new Error("Failed to download file");
        // }

        // // ✅ Create a hidden `<a>` tag and trigger download natively
        // const blob = response.blob();
        // const url = window.URL.createObjectURL(blob);

        // const link = document.createElement("a");
        // link.href = url;
        // link.download = `job_${jobId.value}.zip`;
        // document.body.appendChild(link);
        // link.click();
        // document.body.removeChild(link);

        // ✅ Free memory
        // window.URL.revokeObjectURL(url);

        // ✅ Encode selected files into a query parameter
        const payload = encodeURIComponent(JSON.stringify({ selected_files: selectedFiles.value }));

        // ✅ Open download link in a new tab (browser handles download)
        window.open(`${apiBaseURL}/api/download/${jobId.value}/zip?payload=${payload}`, "_blank");

    } catch (error) {
        console.error("Error downloading zip:", error);
    }
};

onMounted(() => {
    fetchFiles();
});

</script>

<style></style>