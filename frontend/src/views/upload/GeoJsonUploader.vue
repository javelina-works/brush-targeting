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
      try {
        const formData = new FormData();
        formData.append("file", file, file.name); // Ensure proper naming

        const response = await api.post(`/upload/${props.jobId}/region_outline`, formData, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        });

        emit("upload-success", response.data.path);
      } catch (error) {
        console.error("GeoJSON Upload Failed:", error.response?.data || error.message);
      }
    }

    const { getRootProps, getInputProps, open, isDragActive } = useDropzone({
      onDrop,
      accept: ".geojson", // Ensures only .geojson files
      multiple: false,
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
