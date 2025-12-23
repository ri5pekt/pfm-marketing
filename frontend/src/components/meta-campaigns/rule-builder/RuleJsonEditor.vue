<template>
    <div class="json-editor-content">
        <div class="field">
            <label>Rule JSON</label>
            <div class="json-editor-scroll-container">
                <div class="json-editor-wrapper" :class="{ 'p-invalid': jsonError }">
                    <div class="json-line-numbers" ref="lineNumbersRef">
                        <div v-for="n in jsonLineCount" :key="n" class="json-line-number">{{ n }}</div>
                    </div>
                    <Textarea
                        :modelValue="modelValue"
                        @update:modelValue="$emit('update:modelValue', $event)"
                        class="w-full json-textarea"
                        :rows="jsonLineCount"
                        placeholder='{"name": "Rule Name", "description": "...", "enabled": true, "schedule_cron": "...", "conditions": {...}, "actions": {...}}'
                        @input="$emit('input')"
                        ref="jsonTextareaRef"
                    />
                </div>
            </div>
        </div>
        <div class="json-actions">
            <div class="json-actions-info">
                <small v-if="jsonError" class="p-error">{{ jsonError }}</small>
                <small v-else class="p-text-secondary">
                    Edit the JSON directly or use the "Apply JSON" button to update the form. JSON
                    updates automatically when you change the form.
                </small>
            </div>
            <div class="json-actions-buttons">
                <Button
                    label="Apply JSON"
                    icon="pi pi-check"
                    @click="$emit('applyJson')"
                    :disabled="!modelValue || !!jsonError"
                    :loading="applyingJson"
                />
                <Button
                    label="Copy JSON"
                    icon="pi pi-copy"
                    severity="secondary"
                    outlined
                    @click="$emit('copyJson')"
                />
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed } from "vue";
import Textarea from "primevue/textarea";
import Button from "primevue/button";

const props = defineProps({
    modelValue: {
        type: String,
        default: "",
    },
    jsonError: {
        type: String,
        default: "",
    },
    applyingJson: {
        type: Boolean,
        default: false,
    },
});

const emit = defineEmits(["update:modelValue", "input", "applyJson", "copyJson"]);

const jsonTextareaRef = ref(null);
const lineNumbersRef = ref(null);

const jsonLineCount = computed(() => {
    if (!props.modelValue) return 20;
    const lines = props.modelValue.split("\n").length;
    // Add 1 to match textarea's actual line count (textarea shows one more line)
    return Math.max(lines + 1, 20); // Minimum 20 lines for empty textarea
});
</script>

<style scoped>
.json-editor-content {
    padding: 1rem 0;
}

.field {
    margin-bottom: 1rem;
}

.field label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: #374151;
}

.json-editor-scroll-container {
    border: 1px solid #ced4da;
    border-radius: 6px;
    background: #fff;
}

.json-editor-wrapper {
    position: relative;
    display: flex;
    background: #fff;
}

.json-line-numbers {
    background-color: #f8f9fa;
    color: #6c757d;
    padding-top: 0.65rem;
    padding-bottom: 0.75rem;
    padding-left: 0.5rem;
    padding-right: 0.5rem;
    text-align: right;
    user-select: none;
    font-family: "Courier New", Courier, monospace;
    font-size: 0.875rem;
    line-height: 1.5;
    min-width: 3rem;
    border-right: 1px solid #dee2e6;
    flex-shrink: 0;
}

.json-line-number {
    height: 1.49em;
    padding-right: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: flex-end;
}

.json-textarea {
    font-family: "Courier New", Courier, monospace;
    font-size: 0.875rem;
    line-height: 1.5;
    flex: 1;
    border: none;
    resize: none;
}

.json-textarea :deep(textarea) {
    border: none;
    padding-top: 0.75rem;
    padding-bottom: 0.75rem;
    padding-left: 0.75rem;
    padding-right: 0.75rem;
    resize: none;
    line-height: 1.5;
}

.json-editor-scroll-container.p-invalid {
    border-color: #e24c4c;
}

.json-actions {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin-top: 1rem;
}

.json-actions-info {
    flex: 1;
}

.json-actions-buttons {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
}

.p-error {
    color: #ef4444;
    font-size: 0.875rem;
    margin-top: 0.25rem;
}

.p-text-secondary {
    color: #6b7280;
    font-size: 0.875rem;
}

.json-editor-scroll-container :deep(textarea) {
    overflow: hidden;
    overflow-y: hidden;
    overflow-x: hidden;
}
</style>

