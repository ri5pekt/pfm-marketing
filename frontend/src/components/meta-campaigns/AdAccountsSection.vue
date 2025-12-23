<template>
    <div class="ad-accounts-section">
        <DataTable
            :value="adAccounts"
            :loading="loading"
            selectionMode="single"
            v-model:selection="localSelection"
            class="accounts-table"
            @row-select="handleRowSelect"
            @row-click="handleRowClick"
            :rowHover="true"
        >
            <Column selectionMode="single" headerStyle="width: 3rem"></Column>
            <Column field="name" header="Name" sortable />
            <Column field="description" header="Description" />
            <Column field="is_default" header="Default">
                <template #body="slotProps">
                    <Tag v-if="slotProps.data.is_default" value="Default" severity="success" />
                </template>
            </Column>
            <Column header="Rules" sortable>
                <template #body="slotProps">
                    {{ getRulesCount(slotProps.data.id) }}
                </template>
            </Column>
            <Column header="Actions">
                <template #body="slotProps">
                    <div class="action-buttons">
                        <Button
                            icon="pi pi-pencil"
                            severity="warning"
                            text
                            rounded
                            @click="$emit('edit-account', slotProps.data)"
                            v-tooltip.top="'Edit'"
                        />
                        <Button
                            icon="pi pi-trash"
                            severity="danger"
                            text
                            rounded
                            @click="$emit('delete-account', slotProps.data)"
                            v-tooltip.top="'Delete'"
                        />
                    </div>
                </template>
            </Column>
        </DataTable>
    </div>
</template>

<script setup>
import { ref, watch } from "vue";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import Tag from "primevue/tag";
import Button from "primevue/button";

const props = defineProps({
    adAccounts: {
        type: Array,
        default: () => [],
    },
    loading: {
        type: Boolean,
        default: false,
    },
    selectedAccount: {
        type: Object,
        default: null,
    },
    getRulesCount: {
        type: Function,
        required: true,
    },
});

const emit = defineEmits(["account-selected", "edit-account", "delete-account"]);

// Local selection ref for v-model binding
const localSelection = ref(props.selectedAccount);

// Sync local selection with prop
watch(
    () => props.selectedAccount,
    (newValue) => {
        localSelection.value = newValue;
    }
);

function handleRowSelect(event) {
    if (event && event.data) {
        localSelection.value = event.data;
        emit("account-selected", { data: event.data });
    }
}

function handleRowClick(event) {
    // Handle row clicks (but not when clicking on buttons or checkbox)
    if (event && event.data) {
        const target = event.originalEvent?.target;
        if (target && !target.closest(".action-buttons") && !target.closest(".p-checkbox")) {
            localSelection.value = event.data;
            emit("account-selected", { data: event.data });
        }
    }
}
</script>

<style scoped>
.ad-accounts-section {
    margin-bottom: 2rem;
}

.action-buttons {
    display: flex;
    gap: 0.5rem;
}
</style>
