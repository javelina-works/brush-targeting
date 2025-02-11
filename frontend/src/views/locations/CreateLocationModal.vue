<template>
  <CModal 
    :visible="isVisible" 
    @close="$emit('close')"
  >
    <CModalHeader>
      <CModalTitle>Create New Location</CModalTitle>
    </CModalHeader>
    
    <CModalBody>
      <CFormInput v-model="locationName" placeholder="Enter location name"/>
    </CModalBody>

    <CModalFooter>
      <CButton color="primary" @click="createLocation">Create</CButton>
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
    isVisible: Boolean
  },
  emits: ['close', 'created'],
  setup(_, { emit }) {
    const locationName = ref('');

    async function createLocation() {
      await api.post('/api/locations', { name: locationName.value });
      emit('created'); // Notify parent to refresh list
      emit('close'); // Close modal
    }

    return { locationName, createLocation };
  }
};
</script>
