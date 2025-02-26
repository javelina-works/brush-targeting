<template>
    <div class="waypoint-manager">
        <h2>Waypoint Manager</h2>

        <div v-if="jobId">
            <CButton @click="handleWaypoints" :disabled="loading">
                {{ loading ? "Processing..." : "Generate & Download" }}
            </CButton>

            <p v-if="message" class="message">{{ message }}</p>
        </div>

        <p v-else class="error">No job selected.</p>
    </div>
</template>

<script>
import { CButton } from "@coreui/vue";
import api from "@/api/axios.js";

export default {
    props: {
        jobId: {
            type: String,
            required: true
        }
    },
    data() {
        return {
            loading: false,
            message: ""
        };
    },
    methods: {
        async handleWaypoints() {
            this.loading = true;
            this.message = "";

            try {
                // Step 1: Generate Waypoints
                const generateResponse = await api.get(`/api/waypoints/${this.jobId}/generate`);
                this.message = generateResponse.data.message;

                // Step 2: Download Waypoints
                const downloadResponse = await api.get(`/api/waypoints/${this.jobId}/download`, {
                    responseType: "blob"
                });

                // Create a blob and trigger download
                const blob = new Blob([downloadResponse.data], { type: "application/zip" });
                const link = document.createElement("a");
                link.href = window.URL.createObjectURL(blob);
                link.download = `${this.jobId}_waypoints.zip`;
                link.click();
                window.URL.revokeObjectURL(link.href);

            } catch (error) {
                this.message = error.response?.data?.detail || "An error occurred.";
            }

            this.loading = false;
        }
    }
};
</script>

<style scoped>
.waypoint-manager {
    padding: 1rem;
    border: 1px solid #ddd;
    border-radius: 5px;
    text-align: center;
    max-width: 400px;
    margin: 1rem auto;
}

button {
    margin: 0.5rem;
    padding: 0.5rem 1rem;
    border: none;
    cursor: pointer;
    font-size: 1rem;
    border-radius: 4px;
    background-color: #007bff;
    color: white;
}

button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}

.message {
    margin-top: 1rem;
    font-size: 0.9rem;
    color: green;
}

.error {
    color: red;
    font-weight: bold;
}
</style>