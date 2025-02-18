import api from '@/api/axios.js';

export const fetchPipelines = async () => {
    try {
        const response = await api.get('/api/pipelines');
        return response.data;
    } catch (error) {
        console.error('Error fetching pipelines:', error);
        return [];
    }
};

export const createPipeline = async (name) => {
    if (!name) return;
    try {
        const response = await api.post('/api/pipelines', { name });
        return response.data;
    } catch (error) {
        console.error('Error creating pipeline:', error);
        return null;
    }
};

export const deletePipeline = async (id) => {
    try {
        await api.delete(`/api/pipelines/${id}`);
        return true;
    } catch (error) {
        console.error('Error deleting pipeline:', error);
        return false;
    }
};

export const updatePipeline = async (id, name) => {
    try {
        await api.put(`/api/pipelines/${id}`, { name });
        return true;
    } catch (error) {
        console.error('Error updating pipeline:', error);
        return false;
    }
};