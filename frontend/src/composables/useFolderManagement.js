import { ref, nextTick } from "vue";
import { useToast } from "primevue/usetoast";
import { exportFolder } from "@/api/metaCampaignsApi";

/**
 * Composable for folder CRUD operations
 * Handles folder creation, editing, deletion, and state management
 */
export function useFolderManagement(emit) {
    const toast = useToast();
    const showNewFolderDialog = ref(false);
    const newFolderName = ref("");
    const folderEditName = ref("");
    const folderNameInput = ref(null);

    function openNewFolderDialog() {
        showNewFolderDialog.value = true;
        newFolderName.value = "";
    }

    function closeNewFolderDialog() {
        showNewFolderDialog.value = false;
        newFolderName.value = "";
    }

    function handleCreateFolder() {
        if (newFolderName.value.trim()) {
            emit("create-folder", newFolderName.value.trim());
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
            emit("rename-folder", folder.id, folderEditName.value.trim());
        }
        folder.editing = false;
    }

    function cancelEditFolder(folder) {
        folder.editing = false;
        folderEditName.value = "";
    }

    function handleDeleteFolder(folder) {
        emit("delete-folder", folder);
    }

    function toggleFolder(folder, folderExpandedState) {
        folder.expanded = !folder.expanded;
        // Store the expanded state to prevent auto-reopening
        folderExpandedState[folder.id] = folder.expanded;
    }

    async function handleCopyFolderJson(folderId) {
        try {
            // Fetch folder export data
            const exportData = await exportFolder(folderId);

            // Convert to formatted JSON string
            const jsonString = JSON.stringify(exportData, null, 2);

            // Copy to clipboard
            await navigator.clipboard.writeText(jsonString);

            toast.add({
                severity: "success",
                summary: "Success",
                detail: `Folder structure copied to clipboard! (${exportData.rules_count} rules)`,
                life: 3000,
            });
        } catch (error) {
            console.error("Failed to export folder:", error);
            toast.add({
                severity: "error",
                summary: "Error",
                detail: error.message || "Failed to export folder",
                life: 5000,
            });
        }
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
        handleCopyFolderJson,
        toggleFolder,
    };
}
