<template>
    <div class="upload-container">
      <h1>Upload Files</h1>
  
      <!-- Display Selected Project & Job -->
      <p><strong>Project ID:</strong> {{ selectedLocation?.id || 'Not Found' }}</p>
      <p><strong>Job ID:</strong> {{ selectedJob?.id || 'Not Found' }}</p>
  
      <!-- Drag & Drop File Upload -->
      <div class="upload-box" @dragover.prevent @drop="handleDrop">
        <input type="file" multiple @change="handleFileSelect" ref="fileInput" hidden />
        <CButton color="primary" @click="triggerFileInput">Choose Files</CButton>
        <p v-if="files.length === 0">Drag & drop files here, or click to select</p>
        <ul v-if="files.length > 0">
          <li v-for="(file, index) in files" :key="index">
            {{ file.name }} - {{ formatFileSize(file.size) }}
            <CButton color="danger" size="sm" @click="removeFile(index)">Remove</CButton>
          </li>
        </ul>
      </div>
  
      <!-- Upload Button -->
      <CButton color="success" @click="uploadFiles" :disabled="files.length === 0">
        Upload Files
      </CButton>
  
      <!-- Upload Progress -->
      <div v-if="uploading">
        <p>Uploading {{ uploadProgress }}%</p>
        <progress :value="uploadProgress" max="100"></progress>
      </div>
  
      <!-- Uploaded Files List -->
      <div v-if="uploadedFiles.length > 0">
        <h2>Uploaded Files</h2>
        <ul>
          <li v-for="(file, index) in uploadedFiles" :key="index">
            {{ file.name }} ({{ formatFileSize(file.size) }})
          </li>
        </ul>
      </div>
    </div>
  </template>
  
  <script>
  import { useLocationStore } from '@/stores/locationStore';
  import { ref, computed } from 'vue';
  import { CButton } from '@coreui/vue';
  import api from '@/api/axios.js';
  
  export default {
    components: { CButton },
    setup() {
      const store = useLocationStore();
      const selectedLocation = computed(() => store.selectedLocation);
      const selectedJob = computed(() => store.selectedJob);
  
      const files = ref([]);
      const uploadedFiles = ref([]);
      const uploading = ref(false);
      const uploadProgress = ref(0);
      const fileInput = ref(null);
  
      // Handle File Selection
      function handleFileSelect(event) {
        files.value = Array.from(event.target.files);
      }
  
      // Handle Drag & Drop
      function handleDrop(event) {
        event.preventDefault();
        files.value = Array.from(event.dataTransfer.files);
      }
  
      // Remove a File from List
      function removeFile(index) {
        files.value.splice(index, 1);
      }
  
      // Trigger File Input Click
      function triggerFileInput() {
        fileInput.value.click();
      }
  
      // Format File Size
      function formatFileSize(size) {
        return (size / 1024).toFixed(2) + ' KB';
      }
  
      // Upload Files
      async function uploadFiles() {
        if (!selectedLocation.value || !selectedJob.value) {
          alert('Please select a project and job first!');
          return;
        }
  
        uploading.value = true;
        uploadProgress.value = 0;
  
        const formData = new FormData();
        files.value.forEach((file) => {
          formData.append('files', file);
        });
  
        try {
          const response = await api.post(`/api/upload?projectId=${selectedLocation.value.id}&jobId=${selectedJob.value.id}`, 
            formData, 
            {
              headers: { 'Content-Type': 'multipart/form-data' },
              onUploadProgress: (event) => {
                uploadProgress.value = Math.round((event.loaded * 100) / event.total);
              }
            }
          );
  
          uploadedFiles.value = response.data.files;
          files.value = [];
        } catch (error) {
          console.error('Upload failed:', error.response ? error.response.data : error.message);
          alert('File upload failed');
        } finally {
          uploading.value = false;
        }
      }
  
      return { 
        selectedLocation, 
        selectedJob, 
        files, 
        uploadedFiles, 
        uploading, 
        uploadProgress, 
        fileInput,
        handleFileSelect, 
        handleDrop, 
        removeFile, 
        triggerFileInput, 
        uploadFiles, 
        formatFileSize 
      };
    }
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
  
  ul {
    list-style: none;
    padding: 0;
  }
  </style>
  