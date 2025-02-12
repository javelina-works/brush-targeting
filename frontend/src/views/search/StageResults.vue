<script setup>
import { usePipelineStore } from "@/stores/pipeline";

const pipelineStore = usePipelineStore();
</script>

<template>
  <div class="p-4 border-t">
    <h3 class="text-lg font-bold">Intermediate Results</h3>
    <div v-if="pipelineStore.results.length === 0">No results yet.</div>
    <div v-for="(result, index) in pipelineStore.results" :key="index">
      <h4 class="font-semibold">{{ result.stage }}</h4>
      <img :src="result.image" class="max-w-full border rounded" />
    </div>
  </div>
</template>
