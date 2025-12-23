<template>
    <Dialog
        :visible="modelValue"
        :header="editingAccount ? 'Edit Ad Account' : 'Create Ad Account'"
        :modal="true"
        :style="{ width: '600px' }"
        @update:visible="$emit('update:modelValue', $event)"
    >
        <div class="form-content">
            <div class="field">
                <label>Name *</label>
                <InputText v-model="localAccountForm.name" class="w-full" />
            </div>
            <div class="field">
                <label>Description</label>
                <Textarea v-model="localAccountForm.description" class="w-full" rows="3" />
            </div>
            <div class="field">
                <label>Meta Account ID</label>
                <InputText v-model="localAccountForm.meta_account_id" class="w-full" />
            </div>
            <div class="field">
                <label>Meta Access Token</label>
                <Password
                    v-model="localAccountForm.meta_access_token"
                    :feedback="false"
                    toggleMask
                    class="w-full access-token-field"
                    :inputClass="'w-full'"
                />
            </div>
            <div class="field">
                <label>Slack Webhook URL</label>
                <InputText
                    v-model="localAccountForm.slack_webhook_url"
                    class="w-full"
                    placeholder="https://hooks.slack.com/services/..."
                />
                <small class="p-text-secondary"
                    >Enter your Slack webhook URL to receive notifications when rules execute actions</small
                >
            </div>
            <div class="field checkbox-field">
                <div class="checkbox-container">
                    <Checkbox v-model="localAccountForm.is_default" inputId="is_default" :binary="true" />
                    <label for="is_default" class="checkbox-label">Set as Default</label>
                </div>
            </div>
            <!-- Connection Status (only show when editing) -->
            <div v-if="editingAccount" class="field">
                <label>Connection Status</label>
                <div class="connection-status-container">
                    <div class="connection-status-info">
                        <i
                            v-if="connectionStatus === true"
                            class="pi pi-check-circle connection-status-icon success"
                        ></i>
                        <i
                            v-else-if="connectionStatus === false"
                            class="pi pi-times-circle connection-status-icon error"
                        ></i>
                        <i v-else class="pi pi-question-circle connection-status-icon unknown"></i>
                        <span class="connection-status-text">
                            {{
                                connectionStatus === true
                                    ? "Active"
                                    : connectionStatus === false
                                    ? "Failed"
                                    : "Not Tested"
                            }}
                        </span>
                    </div>
                    <div v-if="connectionLastChecked" class="connection-last-checked">
                        <small class="p-text-secondary"> Last checked: {{ formatDate(connectionLastChecked) }} </small>
                    </div>
                </div>
                <Button
                    label="Test Connection"
                    icon="pi pi-refresh"
                    severity="secondary"
                    outlined
                    @click="handleTestConnection"
                    :loading="testingConnection"
                    :disabled="testingConnection"
                    class="mt-2"
                />
            </div>
        </div>
        <template #footer>
            <Button label="Cancel" severity="secondary" @click="handleClose" />
            <Button :label="editingAccount ? 'Update' : 'Create'" @click="handleSave" :loading="saving" />
        </template>
    </Dialog>
</template>

<script setup>
import { ref, watch } from "vue";
import Dialog from "primevue/dialog";
import InputText from "primevue/inputtext";
import Textarea from "primevue/textarea";
import Password from "primevue/password";
import Checkbox from "primevue/checkbox";
import Button from "primevue/button";

const props = defineProps({
    modelValue: {
        type: Boolean,
        default: false,
    },
    editingAccount: {
        type: Object,
        default: null,
    },
    accountForm: {
        type: Object,
        required: true,
    },
    connectionStatus: {
        type: [Boolean, null],
        default: null,
    },
    connectionLastChecked: {
        type: [Date, null],
        default: null,
    },
    testingConnection: {
        type: Boolean,
        default: false,
    },
    saving: {
        type: Boolean,
        default: false,
    },
});

const emit = defineEmits(["update:modelValue", "save", "close", "test-connection"]);

const localAccountForm = ref({ ...props.accountForm });

watch(
    () => props.accountForm,
    (newForm) => {
        localAccountForm.value = { ...newForm };
    },
    { deep: true }
);

function formatDate(date) {
    if (!date) return "";
    const d = new Date(date);
    return d.toLocaleString();
}

function handleSave() {
    emit("save", { ...localAccountForm.value });
}

function handleClose() {
    emit("close");
    emit("update:modelValue", false);
}

function handleTestConnection() {
    emit("test-connection");
}
</script>

<style scoped>
.form-content {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.field {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.field label {
    font-weight: 600;
    color: #374151;
}

.checkbox-field {
    margin-top: 0.5rem;
}

.checkbox-container {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.checkbox-label {
    cursor: pointer;
    user-select: none;
}

.connection-status-container {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.connection-status-info {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.connection-status-icon {
    font-size: 1.25rem;
}

.connection-status-icon.success {
    color: #10b981;
}

.connection-status-icon.error {
    color: #ef4444;
}

.connection-status-icon.unknown {
    color: #6b7280;
}

.connection-status-text {
    font-weight: 500;
    color: #374151;
}

.connection-last-checked {
    margin-left: 1.75rem;
}

.p-text-secondary {
    color: #6b7280;
    font-size: 0.875rem;
}
</style>
