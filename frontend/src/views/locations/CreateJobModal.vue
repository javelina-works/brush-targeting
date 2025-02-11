<template>
  <CModal :visible="isVisible" @close="$emit('close')">
    <CModalHeader>
      <CModalTitle>Create New Job</CModalTitle>
    </CModalHeader>

    <CModalBody>
      <CFormInput v-model="jobName" placeholder="Enter job name" />
    </CModalBody>

    <CModalFooter>
      <CButton color="primary" @click="createJob">Create</CButton>
      <CButton color="secondary" @click="$emit('close')">Cancel</CButton>
    </CModalFooter>
  </CModal>
</template>

<script>
import { ref } from 'vue';
import { CModal, CModalHeader, CModalTitle, CModalBody, CModalFooter, CButton, CFormInput } from '@coreui/vue';
import api from '@/api/axios.js';

export default {
  components: { CModal, CModalHeader, CModalTitle, CModalBody, CModalFooter, CButton, CFormInput },
  props: {
    isVisible: Boolean,
    locationId: String // Required to know which location we're adding the job under
  },
  emits: ['close', 'created'],
  setup(props, { emit }) {
    const jobName = ref('');

    async function createJob() {
      if (!props.locationId) {
        console.error("No location selected for job creation");
        return;
      }
      await api.post(`/api/jobs/`, { 
        location_id: props.locationId,
        name: jobName.value });
      emit('created'); // Notify parent to refresh job list
      emit('close'); // Close modal
    }

    return { jobName, createJob };
  }
};
</script>
