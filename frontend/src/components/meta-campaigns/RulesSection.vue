<template>
    <div v-if="selectedAccount" class="rules-section">
        <RulesToolbar
            :account-name="selectedAccount.name"
            @create-folder-click="folderMgmt.openNewFolderDialog()"
            @import-folder-click="openImportDialog"
            @create-rule-click="ruleActions.navigateToCreateRule()"
        />

        <ProgressSpinner v-if="loading" style="width: 50px; height: 50px" />

        <div v-else class="rules-container">
            <!-- Helpful hint -->
            <div v-if="folders.length > 0" class="drag-hint">
                <i class="pi pi-info-circle"></i>
                <span>
                    Tip: Drag folders by the <i class="pi pi-bars"></i> handle to reorder, or drag rules into/out of folders
                </span>
            </div>

            <!-- Unified list of folders and ungrouped rules -->
            <VueDraggable
                v-model="unifiedItems"
                :animation="200"
                handle=".item-drag-handle"
                @end="dragDrop.onFolderReorder(unifiedItems)"
                class="unified-container"
            >
                <template v-for="item in unifiedItems" :key="item.type + '-' + item.id">
                    <!-- Ungrouped Rules Container -->
                    <RulesUngroupedSection
                        v-if="item.type === 'ungrouped-container'"
                        v-model:rules="item.data"
                        :testing-rule-id="testingRuleId"
                        :is-dragging="dragDrop.isDragging.value"
                        @drag-start="dragDrop.onDragStart()"
                        @drag-end="dragDrop.onRuleDragEnd(unifiedItems)"
                        @test-rule="ruleActions.handleTestRule($event)"
                        @cancel-test="ruleActions.handleCancelTest()"
                        @view-logs="ruleActions.handleViewLogs($event)"
                        @edit-rule="ruleActions.navigateToEditRule($event)"
                        @delete-rule="ruleActions.handleDeleteRule($event)"
                    />

                    <!-- Folder -->
                    <RulesFolderItem
                        v-else-if="item.type === 'folder'"
                        :folder="item.data"
                        :testing-rule-id="testingRuleId"
                        :folder-edit-name="folderMgmt.folderEditName.value"
                        @update:folder="updateFolderData(item, $event)"
                        @toggle-folder="folderMgmt.toggleFolder($event, dragDrop.folderExpandedState.value)"
                        @start-edit="folderMgmt.startEditFolder($event)"
                        @save-edit="handleSaveEditFolder"
                        @cancel-edit="folderMgmt.cancelEditFolder($event)"
                        @delete-folder="folderMgmt.handleDeleteFolder($event)"
                        @copy-folder-json="folderMgmt.handleCopyFolderJson($event)"
                        @folder-drag-enter="dragDrop.handleFolderDragEnter($event)"
                        @folder-drag-over="dragDrop.handleFolderDragOver($event)"
                        @folder-drag-leave="dragDrop.handleFolderDragLeave($event.folder, $event.e)"
                        @folder-drop="dragDrop.handleFolderDrop($event)"
                        @drag-start="dragDrop.onDragStart()"
                        @drag-end="dragDrop.onRuleDragEnd(unifiedItems)"
                        @test-rule="ruleActions.handleTestRule($event)"
                        @cancel-test="ruleActions.handleCancelTest()"
                        @view-logs="ruleActions.handleViewLogs($event)"
                        @edit-rule="ruleActions.navigateToEditRule($event)"
                        @delete-rule="ruleActions.handleDeleteRule($event)"
                    />
                </template>
            </VueDraggable>
        </div>

        <!-- New Folder Dialog -->
        <NewFolderDialog
            v-model:visible="folderMgmt.showNewFolderDialog.value"
            v-model:folder-name="folderMgmt.newFolderName.value"
            @create="folderMgmt.handleCreateFolder()"
        />
        
        <!-- Import Folder Dialog -->
        <ImportFolderDialog
            v-model:visible="showImportDialog"
            :ad-account-id="selectedAccount?.id"
            @import-success="handleImportFolder"
        />
    </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { VueDraggable } from 'vue-draggable-plus';
import ProgressSpinner from 'primevue/progressspinner';
import { useToast } from 'primevue/usetoast';

// Components
import RulesToolbar from './rules/RulesToolbar.vue';
import RulesUngroupedSection from './rules/RulesUngroupedSection.vue';
import RulesFolderItem from './rules/RulesFolderItem.vue';
import NewFolderDialog from './dialogs/NewFolderDialog.vue';
import ImportFolderDialog from './dialogs/ImportFolderDialog.vue';

// Composables
import { useRuleDragDrop } from '@/composables/useRuleDragDrop';
import { useFolderManagement } from '@/composables/useFolderManagement';
import { useRuleActions } from '@/composables/useRuleActions';

// API
import { importFolder } from '@/api/metaCampaignsApi';

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
    'test-rule',
    'cancel-test',
    'view-logs',
    'delete-rule',
    'create-folder',
    'rename-folder',
    'delete-folder',
    'folder-imported',
    'reorder-folders',
    'reorder-rules',
]);

// Initialize composables
const toast = useToast();
const dragDrop = useRuleDragDrop(props, emit);
const folderMgmt = useFolderManagement(emit);
const ruleActions = useRuleActions(props, emit);

// Local state
const unifiedItems = ref([]);
const foldersWithRules = ref([]);
const showImportDialog = ref(false);

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
            dragDrop.folderExpandedState.value[folder.id] !== undefined
                ? dragDrop.folderExpandedState.value[folder.id]
                : false;

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
    if (rootRulesArray.length > 0 || dragDrop.isDragging.value) {
        items.push({
            type: 'ungrouped-container',
            id: 'ungrouped',
            position: -1, // Always first
            data: rootRulesArray,
        });
    }

    // Add all folders as items
    foldersWithRules.value.forEach((folder) => {
        items.push({
            type: 'folder',
            id: folder.id,
            position: folder.position || 0,
            data: folder,
        });
    });

    // Sort by position
    items.sort((a, b) => a.position - b.position);

    unifiedItems.value = items;
}

function updateFolderData(item, updatedFolder) {
    item.data = updatedFolder;
}

function handleSaveEditFolder(folder, newName) {
    if (newName && newName.trim() !== folder.name) {
        emit('rename-folder', folder.id, newName.trim());
    }
    folder.editing = false;
}

// Import folder handlers
function openImportDialog() {
    showImportDialog.value = true;
}

async function handleImportFolder(folderJson) {
    try {
        const result = await importFolder(props.selectedAccount.id, folderJson);
        
        toast.add({
            severity: 'success',
            summary: 'Success',
            detail: `Imported folder "${result.folder_name}" with ${result.rules_imported} rules`,
            life: 5000,
        });
        
        // Close dialog and trigger reload
        showImportDialog.value = false;
        emit('folder-imported'); // Trigger parent reload after import
    } catch (error) {
        console.error('Failed to import folder:', error);
        toast.add({
            severity: 'error',
            summary: 'Import Failed',
            detail: error.message || 'Failed to import folder',
            life: 5000,
        });
    }
}
</script>

<style scoped>
.rules-section {
    margin-top: 2rem;
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
</style>
