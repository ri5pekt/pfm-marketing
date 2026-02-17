<template>
    <div class="section-header">
        <h2>Rules for {{ accountName }}</h2>
        <div class="header-actions">
            <Button label="New Folder" icon="pi pi-folder" severity="secondary" @click="$emit('create-folder-click')" />
            <Button
                label="Import Folder"
                icon="pi pi-download"
                severity="secondary"
                outlined
                @click="$emit('import-folder-click')"
            />
            <Button label="Create Rule" icon="pi pi-plus" @click="$emit('create-rule-click')" />
        </div>
    </div>
</template>

<script setup>
import Button from "primevue/button";

defineProps({
    accountName: {
        type: String,
        required: true,
    },
});

defineEmits(["create-folder-click", "import-folder-click", "create-rule-click"]);
</script>

<style scoped>
.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
}

.header-actions {
    display: flex;
    gap: 0.75rem;
}
</style>
