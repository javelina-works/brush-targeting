<template>
    <div class="orthophoto-uploader" v-bind="getRootProps()">
        <input v-bind="getInputProps()" />
        <p v-if="isDragActive">Drop the image file here ...</p>
        <p v-else>Drop region image here, or click to select one</p>
        <CButton color="primary" @click="open">Open File Dialog</CButton>

        <AutoDismissAlert :message="alertMessage" :alertColor="alertColor" :duration="alertDuration" />
    </div>
</template>

<script setup>
import { ref } from 'vue';
import { CButton } from '@coreui/vue';
import AutoDismissAlert from '@/components/AutoDismissAlert.vue';
import api from '@/api/axios.js';
import { useDropzone } from "vue3-dropzone";


const props = defineProps({
    jobId: {
        type: String,
        required: true,
    },
});

const emit = defineEmits([
    'upload-success',
]);

const alertMessage = ref("");
const alertColor = ref("primary");
const alertDuration = ref(7); // Set in seconds

function onDrop(acceptedFiles, rejectReasons) {
    // console.log("Accepted files: ", acceptedFiles);
    if (acceptedFiles.length > 0) {
        uploadFile(acceptedFiles[0]);
    } else {
        console.error("No valid file received.");
        alertColor.value = "warning";
        alertDuration.value = 5;
        alertMessage.value = "No valid file received"; // Triggers alert popup
    }
}

async function uploadFile(file) {
    let filename = null;

    try {
        const formData = new FormData();
        formData.append("file", file, file.name); // Ensure proper naming

        const response = await api.post(`api/upload/${props.jobId}/orthophoto`, formData, {
            headers: {
                "Content-Type": "multipart/form-data",
            },
        });

        if (response.data.filename) { filename = response.data.filename; }
        else { console.error("Upload response missing filename:", response.data); }
    } catch (error) {
        console.error("Orthophoto Upload Failed:", error.response?.data || error.message);
    }

    // Emit outside the try/catch block
    if (filename) {
        alertColor.value = "success";
        alertMessage.value = "File uploaded! Generating image tiles..."; // Triggers alert popup
        await generateImageTiles(); // Now we have image, convert to COG
    }
}

async function generateImageTiles() {
    try {
        const response = await api.post(`api/generate_tiles/${props.jobId}/`);

        if (response.status == 200) {
            console.log("Tile generation started successfully:", response.data);
            alertColor.value = "success";
            alertMessage.value = "Image tiles generated!"; // Triggers alert popup
            
            emit("upload-success", filename); // Now we have succeeded! Trigger refresh in parent
        } else {
            console.warn("Unexpected response during tile generation:", response.data);
            alertColor.value = "warning";
            alertMessage.value = "Unexpected response during tile generation."; // Triggers alert popup
        }
    } catch (error) {
        console.error("Orthophoto Tiling Failed:", error.response?.data || error.message);
        alertColor.value = "danger";
        alertDuration.value = 12; // BIG problem if true
        alertMessage.value = "Orthophoto Tiling Failed. Tell Kellan about this!"; // Triggers alert popup
    }
}

// Dropzone callbacks
const { getRootProps, getInputProps, open, isDragActive } = useDropzone({
    multiple: false,
    onDrop,
    accept: "image/tiff, image/jpeg, image/png", // Ensures only image files are allowed
});

</script>

<style scoped>
.orthophoto-uploader {
    text-align: center;
    margin-top: 20px;
    padding: 20px;
    border: 2px dashed #ccc;
    cursor: pointer;
}

.orthophoto-uploader:hover {
    background: #f4f4f4;
}
</style>
