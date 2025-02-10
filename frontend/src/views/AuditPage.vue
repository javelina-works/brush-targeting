<template>
    <div>
      <h1>Target Audit</h1>
      <p>Interactive map for target analysis.</p>
      <MapLayers />
      <MapView />
    </div>
  </template>

<script setup>
import MapView from '@/components/MapView.vue';
import MapLayers from "@/components/MapLayers.vue";
</script>