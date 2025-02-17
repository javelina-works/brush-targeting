<template>
    <div class="geojson-uploader" v-bind="getRootProps()">
        <input v-bind="getInputProps()" />
        <p v-if="isDragActive">Drop the GeoJSON file here ...</p>
        <p v-else>Drag 'n' drop a GeoJSON file here, or click to select one</p>
        <CButton color="primary" @click="open">Open File Dialog</CButton>
    </div>
</template>

<script>
import { ref } from 'vue';
import { CButton } from '@coreui/vue';
import api from '@/api/axios.js';
import { useDropzone } from "vue3-dropzone";

export default {
    components: { CButton },
    props: {
        jobId: {
            type: String,
            required: true,
        },
    },
    emits: ['upload-success'],
    setup(props, { emit }) {

        function onDrop(acceptedFiles, rejectReasons) {
            // console.log("Accepted files: ", acceptedFiles);
            if (acceptedFiles.length > 0) {
                uploadFile(acceptedFiles[0]);
            } else {
                console.error("No valid file received.");
            }
        }

        async function uploadFile(file) {
            let filename = null;

            try {
                const formData = new FormData();
                formData.append("file", file, file.name); // Ensure proper naming

                const response = await api.post(`api/upload/${props.jobId}/region_contour`, formData, {
                    headers: {
                        "Content-Type": "multipart/form-data",
                    },
                });

                if (response.data.filename) { filename = response.data.filename; } 
                else { console.error("Upload response missing filename:", response.data); }
            } catch (error) {
                console.error("GeoJSON Upload Failed:", error.response?.data || error.message);
            }

            // Emit outside the try/catch block
            if (filename) {
                emit("upload-success", filename);
            }
        }

        const { getRootProps, getInputProps, open, isDragActive } = useDropzone({
            multiple: false,
            onDrop,
            accept: ".geojson", // Ensures only .geojson files
        });

        return {
            getRootProps,
            getInputProps,
            open,
            isDragActive,
        };
    },
};
</script>

<style scoped>
.geojson-uploader {
    text-align: center;
    margin-top: 20px;
    padding: 20px;
    border: 2px dashed #ccc;
    cursor: pointer;
}

.geojson-uploader:hover {
    background: #f4f4f4;
}
</style>
