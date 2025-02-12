import { defineStore } from 'pinia';
import { useStorage } from '@vueuse/core';

export const useLocationStore = defineStore('locationStore', {
    state: () => ({
        selectedLocation: useStorage('selectedLocation', {}, localStorage, {
          serializer: {
            read: (v) => (v ? JSON.parse(v) : null),
            write: (v) => JSON.stringify(v),
          },
        }),
        selectedJob: useStorage('selectedJob', {}, localStorage, {
          serializer: {
            read: (v) => (v ? JSON.parse(v) : null),
            write: (v) => JSON.stringify(v),
          },
        }),
      }),
      actions: {
        setLocation(location) {
          console.log("📌 Setting selectedLocation:", location);
          this.selectedLocation = location ? { ...location } : null;
          this.selectedJob = null; // Reset job selection when changing location
        },
        setJob(job) {
          console.log("📌 Setting selectedJob:", job);
          this.selectedJob = job ? { ...job } : null;
        },
    },
});
