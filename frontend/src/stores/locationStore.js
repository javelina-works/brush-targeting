import { defineStore } from 'pinia';

export const useLocationStore = defineStore({
  id: 'locationStore',
  state: () => ({
    selectedLocation: null,
    selectedJob: null,
  }),
  actions: {
    setLocation(location) {
      this.selectedLocation = location;
      this.selectedJob = null; // Reset job selection
    },
    setJob(job) {
      this.selectedJob = job;
    },
  },
});
