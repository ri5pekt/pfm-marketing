<template>
    <div v-if="selectedAccount" class="rules-section">
        <div class="section-header">
            <h2>Rules for {{ selectedAccount.name }}</h2>
            <div class="header-actions">
                <Button
                    label="New Folder"
                    icon="pi pi-folder"
                    severity="secondary"
                    @click="showNewFolderDialog = true"
                />
                <Button label="Create Rule" icon="pi pi-plus" @click="navigateToCreateRule" />
            </div>
        </div>

        <ProgressSpinner v-if="loading" style="width: 50px; height: 50px" />

        <div v-else class="rules-container">
            <!-- Helpful hint -->
            <div v-if="folders.length > 0" class="drag-hint">
                <i class="pi pi-info-circle"></i>
                <span
                    >Tip: Drag folders by the <i class="pi pi-bars"></i> handle to reorder, or drag rules into/out of
                    folders</span
                >
            </div>

            <!-- Unified list of folders and ungrouped rules -->
            <VueDraggable
                v-model="unifiedItems"
                :animation="200"
                handle=".item-drag-handle"
                @end="onUnifiedDragEnd"
                class="unified-container"
            >
                <template v-for="item in unifiedItems" :key="item.type + '-' + item.id">
                    <!-- Ungrouped Rules Container -->
                    <div v-if="item.type === 'ungrouped-container'" class="ungrouped-rules-container">
                        <div class="ungrouped-header">
                            <i class="pi pi-list ungrouped-icon"></i>
                            <span>Ungrouped Rules</span>
                        </div>
                        <VueDraggable
                            v-model="item.data"
                            :animation="200"
                            group="rules"
                            handle=".rule-drag-handle"
                            @start="onDragStart"
                            @end="onRuleDragEnd"
                            class="ungrouped-rules-list"
                            :class="{ 'empty-drop-zone': item.data.length === 0 && isDragging }"
                        >
                            <div v-for="rule in item.data" :key="rule.id" class="rule-item ungrouped-rule">
                                <i class="pi pi-bars rule-drag-handle"></i>
                                <i class="pi pi-bolt rule-icon"></i>
                                <div class="rule-content">
                                    <div class="rule-main-line">
                                        <div class="rule-name">{{ rule.name }}</div>
                                        <div class="rule-meta">
                                            <Tag
                                                :value="rule.enabled ? 'Enabled' : 'Disabled'"
                                                :severity="rule.enabled ? 'success' : 'secondary'"
                                            />
                                            <span class="rule-schedule">{{ formatSchedule(rule.schedule_cron) }}</span>
                                        </div>
                                        <div class="action-buttons">
                                            <Button
                                                v-if="testingRuleId !== rule.id"
                                                icon="pi pi-play"
                                                severity="success"
                                                text
                                                size="small"
                                                @click="$emit('test-rule', rule.id)"
                                                v-tooltip.top="'Test Rule'"
                                            />
                                            <Button
                                                v-else
                                                severity="danger"
                                                text
                                                size="small"
                                                @click="$emit('cancel-test')"
                                                v-tooltip.top="'Cancel Test'"
                                            >
                                                <ProgressSpinner
                                                    style="width: 14px; height: 14px; margin-right: 6px"
                                                    strokeWidth="3"
                                                />
                                                <i class="pi pi-times"></i>
                                            </Button>
                                            <Button
                                                icon="pi pi-list"
                                                severity="info"
                                                text
                                                size="small"
                                                @click="$emit('view-logs', rule.id)"
                                                v-tooltip.top="'View Logs'"
                                            />
                                            <Button
                                                icon="pi pi-pencil"
                                                severity="warning"
                                                text
                                                size="small"
                                                @click="navigateToEditRule(rule.id)"
                                                v-tooltip.top="'Edit'"
                                            />
                                            <Button
                                                icon="pi pi-trash"
                                                severity="danger"
                                                text
                                                size="small"
                                                @click="$emit('delete-rule', rule)"
                                                v-tooltip.top="'Delete'"
                                            />
                                        </div>
                                    </div>
                                    <div v-if="rule.description" class="rule-description">{{ rule.description }}</div>
                                    <div class="rule-times">
                                        <span class="rule-time">
                                            <i class="pi pi-history"></i>
                                            Last: {{ formatDateWithTimezone(rule.last_run_at, rule.schedule_cron) }}
                                        </span>
                                        <span v-if="rule.schedule_cron" class="rule-time">
                                            <i class="pi pi-clock"></i>
                                            Next: {{ formatDateWithTimezone(rule.next_run_at, rule.schedule_cron) }}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </VueDraggable>
                    </div>

                    <!-- Folder -->
                    <div
                        v-else-if="item.type === 'folder'"
                        class="folder"
                        :class="{ 'folder-drag-over': item.data.isDragOver }"
                        @dragenter.prevent="handleFolderDragEnter(item.data)"
                        @dragover.prevent="handleFolderDragOver(item.data)"
                        @dragleave.prevent="handleFolderDragLeave(item.data, $event)"
                        @drop.prevent="handleFolderDrop(item.data)"
                    >
                        <div class="folder-header">
                            <i class="pi pi-bars item-drag-handle"></i>
                            <i
                                :class="item.data.expanded ? 'pi pi-chevron-down' : 'pi pi-chevron-right'"
                                @click="toggleFolder(item.data)"
                                class="folder-toggle"
                            ></i>
                            <i class="pi pi-folder folder-icon"></i>
                            <span v-if="!item.data.editing" class="folder-name" @dblclick="startEditFolder(item.data)">
                                {{ item.data.name }} ({{ item.data.rules.length }})
                            </span>
                            <InputText
                                v-else
                                v-model="folderEditName"
                                @keyup.enter="saveEditFolder(item.data)"
                                @keyup.esc="cancelEditFolder(item.data)"
                                @blur="saveEditFolder(item.data)"
                                class="folder-name-input"
                                ref="folderNameInput"
                                autofocus
                            />
                            <div class="folder-actions">
                                <Button
                                    v-if="!item.data.editing"
                                    icon="pi pi-pencil"
                                    text
                                    size="small"
                                    @click="startEditFolder(item.data)"
                                    v-tooltip.top="'Rename'"
                                />
                                <Button
                                    icon="pi pi-trash"
                                    severity="danger"
                                    text
                                    size="small"
                                    @click="handleDeleteFolder(item.data)"
                                    v-tooltip.top="'Delete Folder'"
                                />
                            </div>
                        </div>

                        <!-- Drop zone hint when folder is collapsed -->
                        <div v-if="!item.data.expanded && item.data.isDragOver" class="folder-drop-hint">
                            <i class="pi pi-arrow-down"></i>
                            <span>Release to add rule to this folder</span>
                        </div>

                        <!-- Rules in folder -->
                        <VueDraggable
                            v-if="item.data.expanded"
                            v-model="item.data.rules"
                            :animation="200"
                            group="rules"
                            handle=".rule-drag-handle"
                            @start="onDragStart"
                            @end="onRuleDragEnd"
                            class="folder-rules"
                        >
                            <div v-for="rule in item.data.rules" :key="rule.id" class="rule-item">
                                <i class="pi pi-bars rule-drag-handle"></i>
                                <i class="pi pi-bolt rule-icon"></i>
                                <div class="rule-content">
                                    <div class="rule-main-line">
                                        <div class="rule-name">{{ rule.name }}</div>
                                        <div class="rule-meta">
                                            <Tag
                                                :value="rule.enabled ? 'Enabled' : 'Disabled'"
                                                :severity="rule.enabled ? 'success' : 'secondary'"
                                            />
                                            <span class="rule-schedule">{{ formatSchedule(rule.schedule_cron) }}</span>
                                        </div>
                                        <div class="action-buttons">
                                            <Button
                                                v-if="testingRuleId !== rule.id"
                                                icon="pi pi-play"
                                                severity="success"
                                                text
                                                size="small"
                                                @click="$emit('test-rule', rule.id)"
                                                v-tooltip.top="'Test Rule'"
                                            />
                                            <Button
                                                v-else
                                                severity="danger"
                                                text
                                                size="small"
                                                @click="$emit('cancel-test')"
                                                v-tooltip.top="'Cancel Test'"
                                            >
                                                <ProgressSpinner
                                                    style="width: 14px; height: 14px; margin-right: 6px"
                                                    strokeWidth="3"
                                                />
                                                <i class="pi pi-times"></i>
                                            </Button>
                                            <Button
                                                icon="pi pi-list"
                                                severity="info"
                                                text
                                                size="small"
                                                @click="$emit('view-logs', rule.id)"
                                                v-tooltip.top="'View Logs'"
                                            />
                                            <Button
                                                icon="pi pi-pencil"
                                                severity="warning"
                                                text
                                                size="small"
                                                @click="navigateToEditRule(rule.id)"
                                                v-tooltip.top="'Edit'"
                                            />
                                            <Button
                                                icon="pi pi-trash"
                                                severity="danger"
                                                text
                                                size="small"
                                                @click="$emit('delete-rule', rule)"
                                                v-tooltip.top="'Delete'"
                                            />
                                        </div>
                                    </div>
                                    <div v-if="rule.description" class="rule-description">{{ rule.description }}</div>
                                    <div class="rule-times">
                                        <span class="rule-time">
                                            <i class="pi pi-history"></i>
                                            Last: {{ formatDateWithTimezone(rule.last_run_at, rule.schedule_cron) }}
                                        </span>
                                        <span v-if="rule.schedule_cron" class="rule-time">
                                            <i class="pi pi-clock"></i>
                                            Next: {{ formatDateWithTimezone(rule.next_run_at, rule.schedule_cron) }}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </VueDraggable>
                    </div>
                </template>
            </VueDraggable>
        </div>

        <!-- New Folder Dialog -->
        <Dialog
            v-model:visible="showNewFolderDialog"
            header="Create New Folder"
            :modal="true"
            :style="{ width: '400px' }"
        >
            <div class="p-fluid">
                <label for="folder-name">Folder Name</label>
                <InputText id="folder-name" v-model="newFolderName" @keyup.enter="handleCreateFolder" autofocus />
            </div>
            <template #footer>
                <Button label="Cancel" severity="secondary" @click="showNewFolderDialog = false" />
                <Button label="Create" @click="handleCreateFolder" />
            </template>
        </Dialog>
    </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from "vue";
import { useRouter } from "vue-router";
import { VueDraggable } from "vue-draggable-plus";
import Tag from "primevue/tag";
import Button from "primevue/button";
import ProgressSpinner from "primevue/progressspinner";
import Dialog from "primevue/dialog";
import InputText from "primevue/inputtext";
import { formatSchedule, formatDateWithTimezone } from "@/utils/cronHelpers";

const router = useRouter();

const props = defineProps({
    selectedAccount: {
        type: Object,
        required: true,
    },
    rules: {
        type: Array,
        default: () => [],
    },
    folders: {
        type: Array,
        default: () => [],
    },
    loading: {
        type: Boolean,
        default: false,
    },
    testingRuleId: {
        type: [Number, null],
        default: null,
    },
});

const emit = defineEmits([
    "test-rule",
    "cancel-test",
    "view-logs",
    "delete-rule",
    "create-folder",
    "rename-folder",
    "delete-folder",
    "reorder-folders",
    "reorder-rules",
    "reorder-unified",
]);

// Local state
const showNewFolderDialog = ref(false);
const newFolderName = ref("");
const folderEditName = ref("");
const folderNameInput = ref(null);
const isDragging = ref(false);

// Unified list of folders and ungrouped rules
const unifiedItems = ref([]);
const foldersWithRules = ref([]);

// Store expanded state separately to prevent auto-reopening
const folderExpandedState = ref({});

// Watch for changes in rules or folders and reorganize
watch(
    () => [props.rules, props.folders],
    () => {
        organizeItems();
    },
    { immediate: true, deep: true },
);

function organizeItems() {
    // Separate rules by folder
    const rulesByFolder = {};
    const rootRulesArray = [];

    props.rules.forEach((rule) => {
        if (rule.folder_id) {
            if (!rulesByFolder[rule.folder_id]) {
                rulesByFolder[rule.folder_id] = [];
            }
            rulesByFolder[rule.folder_id].push(rule);
        } else {
            rootRulesArray.push(rule);
        }
    });

    // Attach rules to folders and add expanded state
    foldersWithRules.value = props.folders.map((folder) => {
        // Preserve the local expanded state, default to false (collapsed)
        const expanded =
            folderExpandedState.value[folder.id] !== undefined ? folderExpandedState.value[folder.id] : false;

        return {
            ...folder,
            rules: rulesByFolder[folder.id] || [],
            expanded,
            editing: false,
            isDragOver: false,
        };
    });

    // Create unified list with folders and an ungrouped rules container
    const items = [];

    // Add ungrouped rules container (always position 0 or first)
    if (rootRulesArray.length > 0 || isDragging.value) {
        items.push({
            type: "ungrouped-container",
            id: "ungrouped",
            position: -1, // Always first
            data: rootRulesArray,
        });
    }

    // Add all folders as items
    foldersWithRules.value.forEach((folder) => {
        items.push({
            type: "folder",
            id: folder.id,
            position: folder.position || 0,
            data: folder,
        });
    });

    // Sort by position
    items.sort((a, b) => a.position - b.position);

    unifiedItems.value = items;
}

function onDragStart() {
    isDragging.value = true;
}

function handleFolderDragEnter(folder) {
    if (isDragging.value) {
        folder.isDragOver = true;
        // Auto-expand collapsed folders when dragging over them
        if (!folder.expanded) {
            setTimeout(() => {
                if (folder.isDragOver) {
                    folder.expanded = true;
                    folderExpandedState.value[folder.id] = true;
                }
            }, 500);
        }
    }
}

function handleFolderDragOver(folder) {
    if (isDragging.value) {
        folder.isDragOver = true;
    }
}

function handleFolderDragLeave(folder, event) {
    // Only clear if actually leaving the folder element
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX;
    const y = event.clientY;

    if (x < rect.left || x >= rect.right || y < rect.top || y >= rect.bottom) {
        folder.isDragOver = false;
    }
}

function handleFolderDrop(folder) {
    folder.isDragOver = false;
}

function onRuleDragEnd() {
    // Clear all drag-over states
    isDragging.value = false;
    unifiedItems.value.forEach((item) => {
        if (item.type === "folder") {
            item.data.isDragOver = false;
        }
    });

    // Small delay to ensure vue-draggable has updated the models
    setTimeout(() => {
        // Collect all rules with their new positions and folder assignments
        const items = [];

        // Ungrouped rules (no folder)
        unifiedItems.value.forEach((item) => {
            if (item.type === "ungrouped-container") {
                item.data.forEach((rule, index) => {
                    items.push({
                        id: rule.id,
                        folder_id: null,
                        position: index,
                    });
                });
            }
        });

        // Rules in folders
        unifiedItems.value.forEach((item) => {
            if (item.type === "folder") {
                item.data.rules.forEach((rule, index) => {
                    items.push({
                        id: rule.id,
                        folder_id: item.data.id,
                        position: index,
                    });
                });
            }
        });

        emit("reorder-rules", items);
    }, 100);
}

function toggleFolder(folder) {
    folder.expanded = !folder.expanded;
    // Store the expanded state to prevent auto-reopening
    folderExpandedState.value[folder.id] = folder.expanded;
}

function startEditFolder(folder) {
    folder.editing = true;
    folderEditName.value = folder.name;
    nextTick(() => {
        if (folderNameInput.value) {
            folderNameInput.value.$el.focus();
        }
    });
}

function saveEditFolder(folder) {
    if (folderEditName.value && folderEditName.value.trim() !== folder.name) {
        emit("rename-folder", folder.id, folderEditName.value.trim());
    }
    folder.editing = false;
}

function cancelEditFolder(folder) {
    folder.editing = false;
    folderEditName.value = "";
}

function handleCreateFolder() {
    if (newFolderName.value.trim()) {
        emit("create-folder", newFolderName.value.trim());
        newFolderName.value = "";
        showNewFolderDialog.value = false;
    }
}

function handleDeleteFolder(folder) {
    emit("delete-folder", folder.id);
}

function onUnifiedDragEnd() {
    // Update positions for folders only (ungrouped container doesn't have a position in DB)
    const folderItems = unifiedItems.value
        .filter((item) => item.type === "folder")
        .map((item, index) => ({
            id: item.id,
            position: index,
        }));

    if (folderItems.length > 0) {
        emit("reorder-folders", folderItems);
    }
}

function onFolderDragEnd() {
    // Update folder positions
    const items = foldersWithRules.value.map((folder, index) => ({
        id: folder.id,
        position: index,
    }));
    emit("reorder-folders", items);
}

function navigateToCreateRule() {
    router.push({
        name: "rule-create",
        query: { accountId: props.selectedAccount.id },
    });
}

function navigateToEditRule(ruleId) {
    router.push({
        name: "rule-edit",
        params: { id: ruleId },
        query: { accountId: props.selectedAccount.id },
    });
}
</script>

<style scoped>
.rules-section {
    margin-top: 2rem;
}

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

.rules-container {
    display: flex;
    flex-direction: column;
    gap: 0;
}

.drag-hint {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: var(--blue-50);
    border: 1px solid var(--blue-200);
    border-radius: 6px;
    color: var(--blue-700);
    font-size: 0.875rem;
}

.drag-hint i.pi-info-circle {
    color: var(--blue-500);
    font-size: 1rem;
}

.drag-hint i.pi-bars {
    font-size: 0.75rem;
    color: var(--blue-600);
}

.unified-container {
    display: flex;
    flex-direction: column;
    gap: 0;
}

.unified-container > * {
    margin-bottom: 0.75rem;
}

.unified-container > *:last-child {
    margin-bottom: 0;
}

.item-drag-handle {
    cursor: move;
    color: var(--text-color-secondary);
}

.ungrouped-rules-container {
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    background: var(--surface-card);
    overflow: hidden;
}

.ungrouped-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    background: var(--surface-50);
    border-bottom: 1px solid #e5e7eb;
    font-weight: 600;
    font-size: 0.9375rem;
}

.ungrouped-icon {
    color: var(--text-color-secondary);
    font-size: 1.25rem;
}

.ungrouped-rules-list {
    min-height: 60px;
}

.ungrouped-rules-list.empty-drop-zone {
    min-height: 100px;
    border: 2px dashed #e5e7eb;
    margin: 1rem;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--surface-50);
    position: relative;
}

.ungrouped-rules-list.empty-drop-zone::before {
    content: "Drop rules here to ungroup";
    color: var(--text-color-secondary);
    font-style: italic;
}

.rule-item.ungrouped-rule {
    border-bottom: 1px solid #e5e7eb !important;
}

.ungrouped-rules-list > .rule-item.ungrouped-rule:last-child {
    border-bottom: none !important;
}

.root-rules-section {
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    background: var(--surface-card);
    overflow: hidden;
    margin-bottom: 0;
    padding-bottom: 1rem;
}

.root-rules-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    background: var(--surface-50);
    border-bottom: 1px solid var(--surface-border);
    font-weight: 600;
    font-size: 0.9375rem;
}

.root-icon {
    color: var(--text-color-secondary);
    font-size: 1.25rem;
}

.root-rules-container {
    min-height: 60px;
}

.root-rules-container.empty-drop-zone {
    min-height: 100px;
    border: 2px dashed #e5e7eb;
    margin: 1rem;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--surface-50);
}

.root-rules-container.empty-drop-zone::before {
    content: "Drop rules here to ungroup";
    color: var(--text-color-secondary);
    font-style: italic;
}

.root-rules-container .rule-item:first-child {
    border-top: none;
}

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

.folder-drag-handle {
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

.rule-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem;
    background: var(--surface-card);
    position: relative;
    border-bottom: 1px solid #e5e7eb !important;
}

.rule-item:last-child {
    border-bottom: none !important;
}

.folder-rules .rule-item {
    padding-left: 3rem;
    background: var(--surface-0);
    border-left: 3px solid var(--primary-100);
}

.folder-rules .rule-item:last-child {
    border-bottom: none !important;
}

.rule-drag-handle {
    cursor: move;
    color: var(--text-color-secondary);
    align-self: flex-start;
    padding-top: 0.5rem;
}

.rule-icon {
    color: var(--yellow-500);
    font-size: 1.125rem;
    flex-shrink: 0;
    align-self: flex-start;
    padding-top: 0.5rem;
}

.rule-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0;
    min-width: 0;
}

.rule-main-line {
    display: flex;
    align-items: center;
    gap: 1rem;
    width: 100%;
}

.rule-name {
    font-weight: 600;
    font-size: 0.9375rem;
    color: var(--text-color);
    flex-shrink: 0;
}

.rule-description {
    font-size: 0.875rem;
    color: #6b7280;
    margin-top: 0.25rem;
    margin-bottom: 0.75rem;
}

.rule-meta {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-shrink: 0;
}

.rule-schedule {
    font-size: 0.875rem;
    color: var(--text-color-secondary);
    white-space: nowrap;
}

.rule-times {
    display: flex;
    gap: 1.5rem;
    font-size: 0.8125rem;
    color: #6b7280;
}

.rule-time {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    white-space: nowrap;
}

.rule-time i {
    font-size: 0.875rem;
}

.action-buttons {
    display: flex;
    gap: 0.25rem;
    align-items: center;
    margin-left: auto;
    flex-shrink: 0;
}

@media (max-width: 768px) {
    .rule-main-line {
        flex-direction: column;
        align-items: flex-start;
    }

    .action-buttons {
        width: 100%;
        justify-content: flex-start;
        margin-left: 0;
    }

    .rule-meta {
        flex-wrap: wrap;
    }
}
</style>
