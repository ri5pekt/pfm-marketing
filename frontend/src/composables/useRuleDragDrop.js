import { ref, watch } from "vue";

/**
 * Composable for handling rule drag and drop functionality
 * Manages drag state, folder drag-over effects, and reordering logic
 */
export function useRuleDragDrop(props, emit) {
    const isDragging = ref(false);
    const folderExpandedState = ref({});

    function onDragStart() {
        isDragging.value = true;
    }

    function onDragEnd() {
        isDragging.value = false;
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
        // Guard against undefined event
        if (!event || !event.currentTarget) {
            folder.isDragOver = false;
            return;
        }

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

    function onRuleDragEnd(unifiedItems) {
        // Clear all drag-over states
        isDragging.value = false;
        unifiedItems.forEach((item) => {
            if (item.type === "folder") {
                item.data.isDragOver = false;
            }
        });

        // Small delay to ensure vue-draggable has updated the models
        setTimeout(() => {
            // Collect all rules with their new positions and folder assignments
            const items = [];

            // Ungrouped rules (no folder)
            unifiedItems.forEach((item) => {
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
            unifiedItems.forEach((item) => {
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

    function onFolderReorder(unifiedItems) {
        // Update positions for folders only (ungrouped container doesn't have a position in DB)
        const folderItems = unifiedItems
            .filter((item) => item.type === "folder")
            .map((item, index) => ({
                id: item.id,
                position: index,
            }));

        if (folderItems.length > 0) {
            emit("reorder-folders", folderItems);
        }
    }

    return {
        isDragging,
        folderExpandedState,
        onDragStart,
        onDragEnd,
        handleFolderDragEnter,
        handleFolderDragOver,
        handleFolderDragLeave,
        handleFolderDrop,
        onRuleDragEnd,
        onFolderReorder,
    };
}
