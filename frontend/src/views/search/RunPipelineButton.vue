<script setup>
import { usePipelineStore } from "@/stores/pipeline";

const pipelineStore = usePipelineStore();

const runPipeline = async () => {
  await pipelineStore.runPipeline();
};
</script>

<template>
  <button 
    @click="runPipeline" 
    class="mt-4 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-700"
  >
    Run Pipeline
  </button>
</template>
