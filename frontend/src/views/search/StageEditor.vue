<script setup>
import { defineProps, reactive, watch } from "vue";
import { usePipelineStore } from "@/stores/pipeline";

const props = defineProps(["stage"]);
const pipelineStore = usePipelineStore();

// Clone the parameters so we don't edit directly
const params = reactive({ ...props.stage.params });

// Update store when parameters change
watch(params, () => {
  pipelineStore.updateStage(props.stage.id, params);
});
</script>

<template>
  <div>
    <h3 class="text-lg font-bold">{{ stage.name }}</h3>
    <div v-for="(value, key) in params" :key="key" class="mb-2">
      <label class="block text-sm font-medium">{{ key }}</label>
      <input 
        v-model="params[key]" 
        type="text" 
        class="w-full p-2 border rounded"
      />
    </div>
  </div>
</template>
