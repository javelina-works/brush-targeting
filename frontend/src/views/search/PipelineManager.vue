<template>
    <CAccordion>
        <CAccordionItem :item-key="1">
            <CAccordionHeader>
                <p><strong>Processing Pipeline:</strong> {{ selectedPipeline || 'None Selected' }}</p>
            </CAccordionHeader>

            <CAccordionBody>

                <!-- Create a new pipeline -->
                <CRow class="mb-3">
                    <CCol>
                        <CFormInput v-model="newPipelineName" placeholder="New pipeline name"
                            aria-describedby="createPipelineNameInput" />
                    </CCol>
                    <CCol>
                        <CButton color="primary" @click="handleCreatePipeline">Create</CButton>
                    </CCol>
                </CRow>

                <!-- Select a previously created pipeline -->
                <CListGroup>
                    <CListGroupItem v-for="pipeline in pipelines" :key="pipeline.id"
                        :active="selectedPipeline === pipeline.id">

                        <span v-if="editingPipelineId !== pipeline.id"
                            @dblclick="editingPipelineId = pipeline.id; editingPipelineName = pipeline.name"
                            class="flex-grow-1">
                            {{ pipeline.name }}
                        </span>
                        <CFormInput v-else v-model="editingPipelineName" @blur="handleUpdatePipeline(pipeline.id)"
                            @keyup.enter="handleUpdatePipeline(pipeline.id)" class="flex-grow-1" />

                        <CButton color="danger" size="sm" @click="handleDeletePipeline(pipeline.id)">Delete</CButton>
                        <CButton color="success" size="sm" @click="selectPipeline(pipeline.id)"
                            :class="{ selected: selectedPipeline === pipeline.id }">Select</CButton>

                    </CListGroupItem>
                </CListGroup>

            </CAccordionBody>
        </CAccordionItem>
    </CAccordion>
</template>


<script setup>
import {
    CAccordion, CAccordionItem, CAccordionHeader, CAccordionBody,
    CListGroup, CListGroupItem, CFormInput, CButton
} from '@coreui/vue';
import { ref, onMounted } from 'vue';
import { fetchPipelines, createPipeline, deletePipeline, updatePipeline } from '@/api/pipeline_api';

const emit = defineEmits(['update:selectedPipeline']);

const pipelines = ref([]);
const selectedPipeline = ref(null);
const newPipelineName = ref('');
const editingPipelineId = ref(null);
const editingPipelineName = ref('');
const isCollapsed = ref(false);

const loadPipelines = async () => {
    pipelines.value = await fetchPipelines();
    if (pipelines.value.length > 0) {
        selectedPipeline.value = pipelines.value[0].id;
        emit('update:selectedPipeline', selectedPipeline.value);
    }
};

const handleCreatePipeline = async () => {
    const newPipeline = await createPipeline(newPipelineName.value);
    if (newPipeline) {
        pipelines.value.push(newPipeline);
        newPipelineName.value = '';
    }
};

const handleDeletePipeline = async (id) => {
    const success = await deletePipeline(id);
    if (success) {
        pipelines.value = pipelines.value.filter(p => p.id !== id);
        if (selectedPipeline.value === id) {
            selectedPipeline.value = null;
            emit('update:selectedPipeline', null);
        }
    }
};

const handleUpdatePipeline = async (id) => {
    const success = await updatePipeline(id, editingPipelineName.value);
    if (success) {
        const index = pipelines.value.findIndex(p => p.id === id);
        if (index !== -1) pipelines.value[index].name = editingPipelineName.value;
        editingPipelineId.value = null;
    }
};

const selectPipeline = (id) => {
    selectedPipeline.value = id;
    emit('update:selectedPipeline', id);
    isCollapsed.value = true;
};

onMounted(loadPipelines);
</script>


<style scoped>
.pipeline-manager {
    padding: 1rem;
    background: #f5f5f5;
    border-radius: 8px;
}

ul {
    list-style-type: none;
    padding: 0;
}

li {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 0;
}

button {
    cursor: pointer;
}

.selected {
    font-weight: bold;
    color: green;
}
</style>
