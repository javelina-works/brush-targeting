<script setup>
import { ref, onMounted } from "vue";
import { usePipelineStore } from "@/stores/pipeline";
import StageEditor from "./StageEditor.vue";
import RunPipelineButton from "./RunPipelineButton.vue";
import StageResults from "./StageResults.vue";

const pipelineStore = usePipelineStore();
const selectedStage = ref(null);

// Simulated pipelineID (replace with dynamic ID from route or user selection)
const pipelineID = "e0d7791f-0732-42a7-82de-f30b12b78eee"; // "Default Pipeline" ID

onMounted(() => {
  pipelineStore.fetchPipeline(pipelineID);
});

const selectStage = (stage) => {
  selectedStage.value = stage;
};
</script>

<template>
  <div class="flex">
    <!-- Sidebar: Processing Stages -->
    <div class="w-1/3 p-4 border-r">
      <h2 class="text-lg font-bold">Pipeline Stages</h2>
      <p>Pipeline Name: {{ pipelineStore.pipelineName }} </p>
      <p>Pipeline ID: {{ pipelineStore.pipelineID }} </p>
      <ul>
        <li v-for="stage in pipelineStore.pipeline" 
            :key="stage.id"
            @click="selectStage(stage)"
            class="cursor-pointer p-2 hover:bg-gray-200">
          {{ stage.name }}
        </li>
      </ul>
    </div>

    <!-- Main Panel: Parameter Editor -->
    <div class="w-2/3 p-4">
      <StageEditor v-if="selectedStage" :stage="selectedStage" />
      <RunPipelineButton />
    </div>
  </div>

  <!-- Results -->
  <StageResults />
</template>
