import { ref, nextTick } from 'vue';

/**
 * Composable for folder CRUD operations
 * Handles folder creation, editing, deletion, and state management
 */
export function useFolderManagement(emit) {
    const showNewFolderDialog = ref(false);
    const newFolderName = ref('');
    const folderEditName = ref('');
    const folderNameInput = ref(null);

    function openNewFolderDialog() {
        showNewFolderDialog.value = true;
        newFolderName.value = '';
    }

    function closeNewFolderDialog() {
        showNewFolderDialog.value = false;
        newFolderName.value = '';
    }

    function handleCreateFolder() {
        if (newFolderName.value.trim()) {
            emit('create-folder', newFolderName.value.trim());
            closeNewFolderDialog();
        }
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
            emit('rename-folder', folder.id, folderEditName.value.trim());
        }
        folder.editing = false;
    }

    function cancelEditFolder(folder) {
        folder.editing = false;
        folderEditName.value = '';
    }

    function handleDeleteFolder(folderId) {
        emit('delete-folder', folderId);
    }

    function toggleFolder(folder, folderExpandedState) {
        folder.expanded = !folder.expanded;
        // Store the expanded state to prevent auto-reopening
        folderExpandedState[folder.id] = folder.expanded;
    }

    return {
        showNewFolderDialog,
        newFolderName,
        folderEditName,
        folderNameInput,
        openNewFolderDialog,
        closeNewFolderDialog,
        handleCreateFolder,
        startEditFolder,
        saveEditFolder,
        cancelEditFolder,
        handleDeleteFolder,
        toggleFolder,
    };
}
