<template>
    <ul>
      <li 
        v-for="location in locations" 
        :key="location.id" 
        :class="{ selected: location.id === selectedLocation?.id }"
        @click="$emit('select', location)"
      >
        {{ location.name }}
      </li>
    </ul>
  </template>
  
  <script>
  export default {
    props: ['locations', 'selectedLocation'],
  };
  </script>
  
  <style scoped>
  .selected {
    font-weight: bold;
    color: blue;
  }
  </style>
  