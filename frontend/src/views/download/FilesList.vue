<template>

    <CAccordion always-open class="mb-4">
        <CAccordionItem v-for="(fileList, category) in files" :key="category">

            <CAccordionHeader>
                <!-- Prevent accordion toggle when clicking checkbox -->
                <div @click.stop class="flex items-center">
                    <CFormCheck 
                        :id="category" 
                        :checked="fileList.every((file) => selectedFiles.has(file))" 
                        @change="(event) => toggleCategory(category, event)" 
                        label="" 
                    />
                    <label :for="category" class="ml-5 font-semibold text-lg">
                        {{ category.charAt(0).toUpperCase() + category.slice(1) }} ({{ fileList.length }})
                    </label>
                </div>
            </CAccordionHeader>

            <CAccordionBody class="pl-4">
                <div v-for="file in fileList" :key="file" class="mb-2">
                    <CFormCheck 
                        :id="file"
                        :checked="selectedFiles.has(file)"
                        @change="toggleFile(file)" 
                        label="" 
                    />
                    <label :for="file" class="ml-2">{{ file }}</label>
                </div>
            </CAccordionBody>
        </CAccordionItem>
    </CAccordion>

</template>

<script setup>
import { ref, computed } from "vue";
import {
    CButton, CAccordion, CAccordionItem,
    CAccordionHeader, CAccordionBody
} from '@coreui/vue';

const props = defineProps({
    files: {
        type: Object,
    },
})

const emit = defineEmits(["update:selectedFiles"]);
const selectedFiles = ref(new Set());

// Toggle selection of all files in a category
const toggleCategory = (category, event) => {
    event.stopPropagation(); // Prevent accordion from toggling

    const filesInCategory = props.files[category] || [];
    const allSelected = filesInCategory.every((file) => selectedFiles.value.has(file));

    filesInCategory.forEach((file) => {
        if (allSelected) {
            selectedFiles.value.delete(file);
        } else {
            selectedFiles.value.add(file);
        }
    });

    emit("update:selectedFiles", Array.from(selectedFiles.value));
};

// Toggle selection of a single file
const toggleFile = (file) => {
    if (selectedFiles.value.has(file)) {
        selectedFiles.value.delete(file);
    } else {
        selectedFiles.value.add(file);
    }

    emit("update:selectedFiles", Array.from(selectedFiles.value));
};

</script>

<style></style>