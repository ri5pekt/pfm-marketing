import { ref } from "vue";
import { useToast } from "primevue/usetoast";
import { useConfirm } from "primevue/useconfirm";
import {
    getFolders,
    createFolder as apiCreateFolder,
    updateFolder as apiUpdateFolder,
    deleteFolder as apiDeleteFolder,
    reorderFolders as apiReorderFolders,
    reorderRules as apiReorderRules,
} from "@/api/metaCampaignsApi";

export function useFolders() {
    const toast = useToast();
    const confirm = useConfirm();

    const folders = ref([]);
    const loading = ref(false);

    async function loadFolders(accountId, silent = false) {
        if (!accountId) {
            folders.value = [];
            return;
        }

        if (!silent) {
            loading.value = true;
        }
        try {
            const loadedFolders = await getFolders(accountId);
            folders.value = Array.isArray(loadedFolders) ? loadedFolders : [];
        } catch (error) {
            console.error("Failed to load folders:", error);
            folders.value = [];
            if (!silent) {
                toast.add({
                    severity: "error",
                    summary: "Error",
                    detail: error.message || "Failed to load folders",
                    life: 5000,
                });
            }
        } finally {
            if (!silent) {
                loading.value = false;
            }
        }
    }

    async function createFolder(name, accountId) {
        try {
            // Validate inputs before making API call
            if (!name || typeof name !== 'string' || !name.trim()) {
                throw new Error('Folder name is required');
            }
            if (!accountId) {
                throw new Error('Ad account ID is required');
            }
            
            const newFolder = await apiCreateFolder({
                ad_account_id: accountId,
                name: name.trim(),
                position: folders.value.length,
            });
            
            folders.value.push(newFolder);
            toast.add({
                severity: "success",
                summary: "Success",
                detail: "Folder created successfully",
                life: 3000,
            });
            return newFolder;
        } catch (error) {
            console.error("Failed to create folder:", error);
            toast.add({
                severity: "error",
                summary: "Error",
                detail: error.message || "Failed to create folder",
                life: 5000,
            });
            throw error;
        }
    }

    async function renameFolder(folderId, newName) {
        try {
            const updatedFolder = await apiUpdateFolder(folderId, { name: newName });
            const index = folders.value.findIndex((f) => f.id === folderId);
            if (index !== -1) {
                folders.value[index] = { ...folders.value[index], ...updatedFolder };
            }
            toast.add({
                severity: "success",
                summary: "Success",
                detail: "Folder renamed successfully",
                life: 3000,
            });
            return updatedFolder;
        } catch (error) {
            console.error("Failed to rename folder:", error);
            toast.add({
                severity: "error",
                summary: "Error",
                detail: error.message || "Failed to rename folder",
                life: 5000,
            });
            throw error;
        }
    }

    async function deleteFolder(folderId) {
        return new Promise((resolve, reject) => {
            confirm.require({
                message: "Are you sure you want to delete this folder? Rules will be moved to root level.",
                header: "Confirm Delete",
                icon: "pi pi-exclamation-triangle",
                acceptClass: "p-button-danger",
                accept: async () => {
                    try {
                        await apiDeleteFolder(folderId);
                        folders.value = folders.value.filter((f) => f.id !== folderId);
                        toast.add({
                            severity: "success",
                            summary: "Success",
                            detail: "Folder deleted successfully",
                            life: 3000,
                        });
                        resolve(true);
                    } catch (error) {
                        console.error("Failed to delete folder:", error);
                        toast.add({
                            severity: "error",
                            summary: "Error",
                            detail: error.message || "Failed to delete folder",
                            life: 5000,
                        });
                        reject(error);
                    }
                },
                reject: () => {
                    resolve(false);
                },
            });
        });
    }

    async function saveFolderPositions(accountId, items) {
        try {
            await apiReorderFolders(accountId, items);
        } catch (error) {
            console.error("Failed to reorder folders:", error);
            toast.add({
                severity: "error",
                summary: "Error",
                detail: error.message || "Failed to reorder folders",
                life: 5000,
            });
            throw error;
        }
    }

    async function saveRulePositions(accountId, items) {
        try {
            await apiReorderRules(accountId, items);
        } catch (error) {
            console.error("Failed to reorder rules:", error);
            toast.add({
                severity: "error",
                summary: "Error",
                detail: error.message || "Failed to reorder rules",
                life: 5000,
            });
            throw error;
        }
    }

    return {
        folders,
        loading,
        loadFolders,
        createFolder,
        renameFolder,
        deleteFolder,
        saveFolderPositions,
        saveRulePositions,
    };
}
