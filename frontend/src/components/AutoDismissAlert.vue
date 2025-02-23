<template>
    <CAlert v-if="isVisible" :color="props.alertColor" class="position-relative" dismissible >
        {{ message }}

        <!-- Progress Bar (Countdown Indicator) -->
        <CProgress class="mt-2" :height="5">
            <CProgressBar :value="progress" :color="props.alertColor" variant="striped" animated />
        </CProgress>
    </CAlert>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';
import { CAlert, CProgress, } from '@coreui/vue';

const props = defineProps({
    message: {
        type: String,
        default: "Alert!",
    },
    alertColor: {
        type: String,
        default: "primary",
    },
    duration: {
        type: Number,
        default: 5, // Default to 5 seconds
    },
});

const isVisible = ref(false);
const progress = ref(100); // % of countdown completion

const showAlert = () => {
    isVisible.value = true;
    progress.value = 0;

    const refreshTimout = 250; // ms between refreshing
    const incrementOffset = 1000 / refreshTimout;

    let interval = setInterval(() => {
        progress.value += (100 / (props.duration * incrementOffset));
        if (progress.value >= 100) {
            clearInterval(interval);
            isVisible.value = false;
        }
    }, refreshTimout);
};

watch(() => props.message, (newMessage) => {
    if (newMessage) {
        showAlert();
    }
});

onMounted(() => {
    if (props.message) {
        showAlert();
    }
});

</script>
