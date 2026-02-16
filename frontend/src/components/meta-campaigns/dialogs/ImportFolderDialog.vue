<template>
    <Dialog
        :visible="visible"
        @update:visible="$emit('update:visible', $event)"
        modal
        header="Import Folder from JSON"
        :style="{ width: '50rem' }"
        :closable="!importing"
    >
        <div class="import-dialog-content">
            <div class="field">
                <label for="json-input">Paste Folder JSON:</label>
                <Textarea
                    id="json-input"
                    v-model="jsonInput"
                    rows="15"
                    placeholder="Paste your exported folder JSON here..."
                    :disabled="importing"
                    class="w-full font-mono"
                />
                <small class="p-text-secondary">
                    Paste the JSON copied from "Copy Folder as JSON"
                </small>
            </div>

            <!-- Preview -->
            <div v-if="parsedData" class="preview-section">
                <h4>Preview:</h4>
                <div class="preview-content">
                    <p><strong>Folder:</strong> {{ parsedData.folder?.name }}</p>
                    <p><strong>Rules:</strong> {{ parsedData.rules?.length || 0 }}</p>
                    <Message severity="info" :closable="false">
                        Rules will be imported as <strong>DISABLED</strong> by default for safety
                    </Message>
                </div>
            </div>

            <!-- Error display -->
            <Message v-if="validationError" severity="error" :closable="false">
                {{ validationError }}
            </Message>
        </div>

        <template #footer>
            <Button
                label="Cancel"
                icon="pi pi-times"
                @click="closeDialog"
                :disabled="importing"
                severity="secondary"
            />
            <Button
                label="Import"
                icon="pi pi-download"
                @click="handleImport"
                :disabled="!isValid || importing"
                :loading="importing"
            />
        </template>
    </Dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import Dialog from 'primevue/dialog';
import Textarea from 'primevue/textarea';
import Button from 'primevue/button';
import Message from 'primevue/message';

const props = defineProps({
    visible: Boolean,
    adAccountId: Number,
});

const emit = defineEmits(['update:visible', 'import-success']);

const jsonInput = ref('');
const importing = ref(false);
const validationError = ref('');

const parsedData = computed(() => {
    try {
        if (!jsonInput.value.trim()) return null;
        const data = JSON.parse(jsonInput.value);
        validationError.value = '';
        
        // Basic validation
        if (!data.folder || !data.rules) {
            validationError.value = 'Invalid JSON structure: missing folder or rules';
            return null;
        }
        
        if (!data.folder.name) {
            validationError.value = 'Invalid JSON: folder name is required';
            return null;
        }
        
        if (!Array.isArray(data.rules)) {
            validationError.value = 'Invalid JSON: rules must be an array';
            return null;
        }
        
        return data;
    } catch (e) {
        validationError.value = 'Invalid JSON: ' + e.message;
        return null;
    }
});

const isValid = computed(() => {
    return parsedData.value && !validationError.value;
});

async function handleImport() {
    if (!isValid.value) return;
    
    importing.value = true;
    try {
        emit('import-success', parsedData.value);
        // Dialog will be closed by parent after successful import
    } catch (error) {
        validationError.value = error.message || 'Import failed';
    } finally {
        importing.value = false;
    }
}

function closeDialog() {
    emit('update:visible', false);
    // Reset state after dialog closes
    setTimeout(() => {
        jsonInput.value = '';
        validationError.value = '';
    }, 300);
}

// Watch for dialog closing to reset state
watch(() => props.visible, (newVal) => {
    if (!newVal) {
        setTimeout(() => {
            jsonInput.value = '';
            validationError.value = '';
        }, 300);
    }
});
</script>

<style scoped>
.import-dialog-content {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.font-mono {
    font-family: 'Courier New', Consolas, Monaco, monospace;
    font-size: 0.875rem;
}

.preview-section {
    padding: 1rem;
    background-color: #f8f9fa;
    border-radius: 6px;
    border: 1px solid #dee2e6;
}

.preview-section h4 {
    margin: 0 0 0.75rem 0;
    font-size: 1rem;
    color: #495057;
}

.preview-content {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.preview-content p {
    margin: 0;
    color: #6c757d;
}

.field label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: #495057;
}
</style>
