<template>
    <Dialog v-model:visible="isVisible" header="Create New Folder" :modal="true" :style="{ width: '400px' }">
        <div class="p-fluid">
            <label for="folder-name">Folder Name</label>
            <InputText id="folder-name" v-model="localFolderName" @keyup.enter="handleCreate" autofocus />
        </div>
        <template #footer>
            <Button label="Cancel" severity="secondary" @click="handleCancel" />
            <Button label="Create" @click="handleCreate" />
        </template>
    </Dialog>
</template>

<script setup>
import { computed } from 'vue';
import Dialog from 'primevue/dialog';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';

const props = defineProps({
    visible: {
        type: Boolean,
        required: true,
    },
    folderName: {
        type: String,
        default: '',
    },
});

const emit = defineEmits(['update:visible', 'update:folderName', 'create']);

const isVisible = computed({
    get: () => props.visible,
    set: (value) => emit('update:visible', value),
});

const localFolderName = computed({
    get: () => props.folderName,
    set: (value) => emit('update:folderName', value),
});

function handleCreate() {
    emit('create');
}

function handleCancel() {
    isVisible.value = false;
}
</script>

<style scoped>
.p-fluid {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

label {
    font-weight: 600;
    font-size: 0.875rem;
    color: var(--text-color);
}
</style>
