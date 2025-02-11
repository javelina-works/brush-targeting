<template>
    <div class="map-controls">
      <label v-for="layer in availableLayers" :key="layer.name">
        <input type="checkbox" v-model="activeLayers[layer.name]" @change="toggleLayer(layer)">
        {{ layer.label }}
      </label>
      <button @click="enableEditing">Enable Editing</button>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue';
  
  const props = defineProps({ layers: Array });
  const emit = defineEmits(["update:layers", "editMode"]);
  
  const availableLayers = ref([
    { name: "region_contour", label: "Region Contour" },
    { name: "targets", label: "Targets" }
  ]);
  
  const activeLayers = ref({ "region_contour": true, "targets": true });
  
/** Emit Updated Layer Selection */
const toggleLayer = () => {
  const selectedLayers = Object.keys(activeLayers.value).filter(layer => activeLayers.value[layer]);
  console.log("✅ Selected Layers:", selectedLayers);
  emit("update:layers", selectedLayers);
};
  
/** Watch for prop changes (if needed later) */
watch(props.layers, (newLayers) => {
  console.log("🔄 MapControls.vue received layers:", newLayers);
});

  const enableEditing = () => {
    emit("editMode");
  };
  </script>
  
  <style scoped>
  .map-controls {
    position: absolute;
    top: 10px;
    left: 10px;
    background: white;
    padding: 10px;
    border-radius: 5px;
  }
  </style>
  