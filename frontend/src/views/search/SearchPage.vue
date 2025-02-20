<template>
  <div class="flex">

    <!-- Pipeline Select & Manager -->
    <!-- <PipelineManager /> -->

    <!-- Sidebar: Processing Stages -->
    <div class="w-1/3 p-4 border-r">
      <h2 class="text-lg font-bold">Image Search Pipeline</h2>
    </div>

    <!-- MVP Image Processing Tabs -->
    <ProcessingTabs />
  </div>
</template>


<script setup>
import { ref, onMounted } from "vue";


import PipelineManager from "./PipelineManager.vue";
import StageEditor from "./StageEditor.vue";
import RunPipelineButton from "./RunPipelineButton.vue";
import StageResults from "./StageResults.vue";
import ProcessingTabs from "./ProcessingTabs.vue";

// import { usePipelineStore } from "@/stores/pipeline";
// const pipelineStore = usePipelineStore();
const selectedStage = ref(null);

// Simulated pipelineID (replace with dynamic ID from route or user selection)
const pipelineID = "e0d7791f-0732-42a7-82de-f30b12b78eee"; // "Default Pipeline" ID

// onMounted(() => {
//   pipelineStore.fetchPipeline(pipelineID);
// });

// const selectStage = (stage) => {
//   selectedStage.value = stage;
// };
</script>
