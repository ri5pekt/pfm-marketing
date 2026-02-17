<template>
    <div
        class="folder"
        :class="{ 'folder-drag-over': folder.isDragOver }"
        @dragenter.prevent="$emit('folder-drag-enter', folder)"
        @dragover.prevent="$emit('folder-drag-over', folder)"
        @dragleave.prevent="(e) => $emit('folder-drag-leave', folder, e)"
        @drop.prevent="$emit('folder-drop', folder)"
    >
        <div class="folder-header">
            <i class="pi pi-bars item-drag-handle"></i>
            <i
                :class="folder.expanded ? 'pi pi-chevron-down' : 'pi pi-chevron-right'"
                @click="$emit('toggle-folder', folder)"
                class="folder-toggle"
            ></i>
            <i class="pi pi-folder folder-icon"></i>
            <span v-if="!folder.editing" class="folder-name" @dblclick="$emit('start-edit', folder)">
                {{ folder.name }} ({{ folder.rules.length }})
            </span>
            <InputText
                v-else
                v-model="folderEditNameLocal"
                @keyup.enter="$emit('save-edit', folder, folderEditNameLocal)"
                @keyup.esc="$emit('cancel-edit', folder)"
                @blur="$emit('save-edit', folder, folderEditNameLocal)"
                class="folder-name-input"
                :ref="(el) => (folderNameInput = el)"
                autofocus
            />
            <div class="folder-actions">
                <Button
                    v-if="!folder.editing"
                    icon="pi pi-pencil"
                    text
                    size="small"
                    @click="$emit('start-edit', folder)"
                    v-tooltip.top="'Rename'"
                />
                <Button
                    icon="pi pi-copy"
                    severity="info"
                    text
                    size="small"
                    @click.stop="$emit('copy-folder-json', folder.id)"
                    v-tooltip.top="'Copy Folder as JSON'"
                />
                <Button
                    icon="pi pi-trash"
                    severity="danger"
                    text
                    size="small"
                    @click="$emit('delete-folder', folder)"
                    v-tooltip.top="'Delete Folder'"
                />
            </div>
        </div>

        <!-- Drop zone hint when folder is collapsed -->
        <div v-if="!folder.expanded && folder.isDragOver" class="folder-drop-hint">
            <i class="pi pi-arrow-down"></i>
            <span>Release to add rule to this folder</span>
        </div>

        <!-- Rules in folder -->
        <VueDraggable
            v-if="folder.expanded"
            v-model="localRules"
            :animation="200"
            group="rules"
            handle=".rule-drag-handle"
            @start="$emit('drag-start')"
            @end="$emit('drag-end')"
            class="folder-rules"
        >
            <RuleListItem
                v-for="rule in localRules"
                :key="rule.id"
                :rule="rule"
                :testing-rule-id="testingRuleId"
                :is-in-folder="true"
                @test-rule="$emit('test-rule', $event)"
                @cancel-test="$emit('cancel-test')"
                @view-logs="$emit('view-logs', $event)"
                @edit-rule="$emit('edit-rule', $event)"
                @delete-rule="$emit('delete-rule', $event)"
            />
        </VueDraggable>
    </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { VueDraggable } from "vue-draggable-plus";
import Button from "primevue/button";
import InputText from "primevue/inputtext";
import RuleListItem from "./RuleListItem.vue";

const props = defineProps({
    folder: {
        type: Object,
        required: true,
    },
    testingRuleId: {
        type: [Number, null],
        default: null,
    },
    folderEditName: {
        type: String,
        default: "",
    },
});

const emit = defineEmits([
    "update:folder",
    "toggle-folder",
    "start-edit",
    "save-edit",
    "cancel-edit",
    "delete-folder",
    "copy-folder-json",
    "folder-drag-enter",
    "folder-drag-over",
    "folder-drag-leave",
    "folder-drop",
    "drag-start",
    "drag-end",
    "test-rule",
    "cancel-test",
    "view-logs",
    "edit-rule",
    "delete-rule",
]);

const folderNameInput = ref(null);
const folderEditNameLocal = ref(props.folderEditName);

watch(
    () => props.folderEditName,
    (newValue) => {
        folderEditNameLocal.value = newValue;
    },
);

const localRules = computed({
    get: () => props.folder.rules,
    set: (value) => {
        const updatedFolder = { ...props.folder, rules: value };
        emit("update:folder", updatedFolder);
    },
});
</script>

<style scoped>
.folder {
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    background: var(--surface-card);
    overflow: hidden;
    transition: all 0.2s ease;
}

.folder.folder-drag-over {
    border: 2px dashed var(--primary-color);
    background: var(--primary-color);
    background: linear-gradient(135deg, var(--primary-50) 0%, var(--primary-100) 100%);
    box-shadow:
        0 0 0 4px rgba(96, 165, 250, 0.2),
        0 4px 12px rgba(0, 0, 0, 0.1);
    transform: scale(1.02);
}

.folder-drop-hint {
    padding: 1.5rem;
    text-align: center;
    background: var(--primary-50);
    border-top: 1px dashed var(--primary-color);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    color: var(--primary-color);
    font-weight: 500;
}

.folder-drop-hint i {
    font-size: 1.5rem;
    animation: bounce 1s infinite;
}

@keyframes bounce {
    0%,
    100% {
        transform: translateY(0);
    }
    50% {
        transform: translateY(-5px);
    }
}

.folder-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    background: var(--surface-50);
    border-bottom: 1px solid #e5e7eb;
    cursor: default;
}

.item-drag-handle {
    cursor: move;
    color: var(--text-color-secondary);
}

.folder-toggle {
    cursor: pointer;
    color: var(--text-color-secondary);
    font-size: 0.875rem;
}

.folder-icon {
    color: var(--primary-color);
    font-size: 1.5rem;
}

.folder-name {
    flex: 1;
    font-weight: 600;
    font-size: 0.9375rem;
}

.folder-name-input {
    flex: 1;
    font-weight: 600;
    font-size: 0.9375rem;
}

.folder-actions {
    display: flex;
    gap: 0.25rem;
}

.folder-rules {
    display: flex;
    flex-direction: column;
    background: var(--surface-0);
}
</style>
