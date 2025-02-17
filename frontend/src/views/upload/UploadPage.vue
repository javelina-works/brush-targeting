<template>
  <div class="upload-container">
    <h1>Upload Files</h1>

    <!-- Display Selected Project & Job -->
    <p><strong>Project ID:</strong> {{ selectedLocation?.id || 'Not Found' }}</p>
    <p><strong>Job ID:</strong> {{ selectedJob?.id || 'Not Found' }}</p>

    <!-- Orthophoto Upload -->
    <!-- <div class="upload-box">
      <input type="file" @change="handleFileSelectOrthophoto" ref="orthophotoInput" accept="image/*" hidden />
      <CButton color="primary" @click="triggerFileInputOrthophoto">Upload Orthophoto</CButton>
    </div> -->

    <!-- Upload Button -->
    <!-- <CButton color="success" @click="uploadFiles" :disabled="!orthophoto">
      Upload Files
    </CButton> -->

    <!-- Upload Progress -->
    <!-- <div v-if="uploading">
      <p>Uploading {{ uploadProgress }}%</p>
      <progress :value="uploadProgress" max="100"></progress>
    </div> -->

    <!-- Region Outline Upload Component -->
    <GeoJsonUploader @upload-success="onGeoJsonUpload" :jobId="selectedJob.id"/>

    <!-- Leaflet Map -->
    <div v-if="regionOutlineFile">
      <h2>Region Outline</h2>
      <div id="map" ref="mapContainer"></div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch, nextTick } from 'vue';
import { useLocationStore } from '@/stores/locationStore';
import { CButton } from '@coreui/vue';
import api from '@/api/axios.js';
import L from "leaflet";
import 'leaflet/dist/leaflet.css';
import GeoJsonUploader from './GeoJsonUploader.vue';

export default {
  components: { CButton, GeoJsonUploader },
  setup() {
    const locationStore = useLocationStore();
    const selectedLocation = computed(() => locationStore.selectedLocation);
    const selectedJob = computed(() => locationStore.selectedJob);

    const orthophoto = ref(null);
    const regionOutlineFile = ref(null);
    const map = ref(null);
    const mapContainer = ref(null);
    const uploading = ref(false);
    const uploadProgress = ref(0);

    async function uploadFiles() {
      if (!selectedLocation.value || !selectedJob.value) {
        alert('Please select a project and job first!');
        return;
      }

      uploading.value = true;
      try {
        if (orthophoto.value) {
          const orthophotoForm = new FormData();
          orthophotoForm.append('file', orthophoto.value);
          await api.post(`/upload/${selectedJob.value.id}/orthophoto`, orthophotoForm);
        }
      } catch (error) {
        console.error('Upload failed:', error);
      } finally {
        uploading.value = false;
      }
    }

    function handleFileSelectOrthophoto(event) {
      orthophoto.value = event.target.files[0];
    }

    function triggerFileInputOrthophoto() {
      document.querySelector("[ref='orthophotoInput']").click();
    }

    // Triggered after region outline uploaded
    function onGeoJsonUpload(filename) {
      console.log("Uploaded file: ", filename);
      regionOutlineFile.value = filename;
      // regionOutlineFile.value = true;
      loadGeoJson(filename);
    }

    async function loadGeoJson(filename) {
      try {
        const response = await api.get(`api/files/${selectedJob.value.id}/${filename}`);
        const geoJsonData = await response.data;
        if (map.value) {
          L.geoJSON(geoJsonData).addTo(map.value);
        }
      } catch (error) {
        console.error("Failed to load GeoJSON:", error);
      }
    }

    watch(regionOutlineFile, (newFile) => {
      if (newFile) {
        nextTick(() => {
          initMap();  // Reinitialize the map when regionOutlineFile updates
        });
      }
    });

    function initMap() {
      if (!mapContainer.value) return;

      map.value = L.map(mapContainer.value, {
        maxZoom: 21,
      }).setView([30.2506, -103.6035], 14);

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map.value);
      L.control.scale().addTo(map.value);
    }

    onMounted(initMap);

    return {
      selectedLocation,
      selectedJob,
      orthophoto,
      uploading,
      uploadProgress,
      uploadFiles,
      handleFileSelectOrthophoto,
      triggerFileInputOrthophoto,
      regionOutlineFile,
      mapContainer,
      onGeoJsonUpload,
    };
  },
};
</script>

<style scoped>
.upload-container {
  max-width: 600px;
  margin: auto;
  text-align: center;
}

.upload-box {
  border: 2px dashed #ccc;
  padding: 20px;
  margin-bottom: 15px;
  cursor: pointer;
}

.upload-box:hover {
  background: #f4f4f4;
}

#map {
  width: 100%;
  height: 400px;
  margin-top: 20px;
}
</style>
