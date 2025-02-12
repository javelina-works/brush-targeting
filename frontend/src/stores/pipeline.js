import { defineStore } from "pinia";
import api from '@/api/axios';

export const usePipelineStore = defineStore("pipeline", {
  state: () => ({
    pipelineName: "No Pipeline Loaded",
    pipelineID: null,
    pipeline: [],
    results: []
  }),
  actions: {
    async fetchPipeline(pipelineID) {
        try {
            const response = await api.get(`/api/pipelines/${pipelineID}`);
            const pipelineData = response.data; // Collect data dict from response
            this.pipelineName = pipelineData.name;
            this.pipelineID = pipelineData.id;  // Store the pipeline ID
            this.stages = pipelineData.stages;
        } catch (error) {
            console.error("Error fetching locations:", error.response ? error.response.data : error.message);
        }
        
    },
    async updateStage(id, params) {
      await axios.put(`/api/pipeline/${id}`, { params });
      const index = this.pipeline.findIndex((s) => s.id === id);
      if (index !== -1) this.pipeline[index].params = params;
    },
    async runPipeline() {
      const response = await api.post("/api/pipeline/run");
      this.results = response.data.results;
    }
  }
});
