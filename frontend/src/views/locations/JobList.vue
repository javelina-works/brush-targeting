<template>
  <CCard>
    <CCardHeader>
      <h2 v-if="selectedLocation">Jobs for {{ selectedLocation.name }}</h2>
      <h2 v-else>Jobs</h2>
    </CCardHeader>

    <CButton color="secondary" @click="showCreateJob = true" class="new-button">
      Create New Job
    </CButton>

    <CListGroup flush>
      <CListGroupItem v-for="job in jobs" :key="job.id" as="button"
        :active="job.id === selectedJob?.id" @click="$emit('select', job)">
        {{ job.name }}
      </CListGroupItem>
    </CListGroup>

  </CCard>

  <CreateJobModal :isVisible="showCreateJob" :locationId="selectedLocation?.id" 
  @close="showCreateJob = false" @created="fetchJobs" />

</template>

<script setup>
import { onMounted, ref } from 'vue';
import {
  CListGroup, CListGroupItem, CButton,
  CCard, CCardBody, CCardHeader,
} from '@coreui/vue';
import api from '@/api/axios.js';
import CreateJobModal from './CreateJobModal.vue';

const showCreateJob = ref(false); // For modal popup state
const getJobs = ref([]);


const props = defineProps({
  jobs: {
    type: Array,
    default: [],
  },
  selectedLocation: {
    type: String,
    default: "",
  },
  selectedJob: {
    type: String,
    // default: "",
  },
});


async function fetchJobs() {
  if (!props.selectedLocation) return;
  try {
    // console.log(`Fetching jobs for location: ${selectedLocation.value.id}`);
    const res = await api.get(`/api/jobs/?location_id=${props.selectedLocation.id}`);
    jobs.value = res.data;
    // console.log("Fetched jobs:", jobs.value);
  } catch (error) {
    console.error("Error fetching jobs:", error.response ? error.response.data : error.message);
  }
}


onMounted(async () => {
  await fetchJobs(); // TODO: check if location set first?
})

</script>

<style scoped>
.new-button {
  margin-bottom: 10px;
}

</style>