<template>
    <ul>
      <li 
        v-for="job in jobs" 
        :key="job.id" 
        @click="$emit('select', job)"
      >
        {{ job.name }}
      </li>
    </ul>
  </template>
  
  <script>
  export default {
    props: ['jobs'],
  };
  </script>
  