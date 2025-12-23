import { ref } from "vue";
import { useToast } from "primevue/usetoast";
import { useConfirm } from "primevue/useconfirm";
import {
    getAdAccounts,
    getDefaultAdAccount,
    createAdAccount,
    updateAdAccount,
    deleteAdAccount,
    testAdAccountConnection,
} from "@/api/adAccountsApi";

export function useAdAccounts() {
    const toast = useToast();
    const confirm = useConfirm();

    const adAccounts = ref([]);
    const selectedAccount = ref(null);
    const loadingAccounts = ref(false);
    const savingAccount = ref(false);
    const testingConnection = ref(false);
    const connectionStatus = ref(null);
    const connectionLastChecked = ref(null);
    const showAdAccountDialog = ref(false);
    const editingAccount = ref(null);

    const accountForm = ref({
        name: "",
        description: "",
        meta_account_id: "",
        meta_access_token: "",
        slack_webhook_url: "",
        is_default: false,
    });

    async function loadAdAccounts() {
        loadingAccounts.value = true;
        try {
            adAccounts.value = await getAdAccounts();
        } catch (error) {
            toast.add({
                severity: "error",
                summary: "Error",
                detail: "Failed to load ad accounts",
                life: 5000,
            });
        } finally {
            loadingAccounts.value = false;
        }
    }

    async function loadDefaultAccount() {
        try {
            const defaultAccount = await getDefaultAdAccount();
            selectedAccount.value = defaultAccount;
            return defaultAccount;
        } catch (error) {
            // No default account yet
            return null;
        }
    }

    function selectAccount(account) {
        selectedAccount.value = account;
    }

    function openCreateAdAccountDialog() {
        editingAccount.value = null;
        accountForm.value = {
            name: "",
            description: "",
            meta_account_id: "",
            meta_access_token: "",
            slack_webhook_url: "",
            is_default: false,
        };
        showAdAccountDialog.value = true;
    }

    function editAdAccount(account) {
        editingAccount.value = account;
        accountForm.value = {
            name: account.name,
            description: account.description || "",
            meta_account_id: account.meta_account_id || "",
            meta_access_token: account.meta_access_token || "",
            slack_webhook_url: account.slack_webhook_url || "",
            is_default: account.is_default || false,
        };
        showAdAccountDialog.value = true;
    }

    function closeAccountDialog() {
        showAdAccountDialog.value = false;
        editingAccount.value = null;
        accountForm.value = {
            name: "",
            description: "",
            meta_account_id: "",
            meta_access_token: "",
            slack_webhook_url: "",
            is_default: false,
        };
    }

    async function testConnection() {
        if (!editingAccount.value || !editingAccount.value.id) {
            toast.add({
                severity: "warn",
                summary: "No Account",
                detail: "Please save the account first before testing connection",
                life: 3000,
            });
            return;
        }

        testingConnection.value = true;
        connectionStatus.value = null;
        try {
            const response = await testAdAccountConnection(editingAccount.value.id);
            connectionStatus.value = response.status || "success";
            connectionLastChecked.value = new Date();
            toast.add({
                severity: "success",
                summary: "Connection Successful",
                detail: response.message || "Connection test passed",
                life: 5000,
            });
        } catch (error) {
            connectionStatus.value = "error";
            connectionLastChecked.value = new Date();
            toast.add({
                severity: "error",
                summary: "Connection Failed",
                detail: error.message || "Failed to connect to Meta API",
                life: 5000,
            });
        } finally {
            testingConnection.value = false;
        }
    }

    async function saveAdAccount() {
        if (!accountForm.value.name || accountForm.value.name.trim() === "") {
            toast.add({
                severity: "error",
                summary: "Validation Error",
                detail: "Account name is required",
                life: 3000,
            });
            return;
        }

        savingAccount.value = true;
        try {
            if (editingAccount.value) {
                // Update existing account
                await updateAdAccount(editingAccount.value.id, accountForm.value);
                toast.add({
                    severity: "success",
                    summary: "Success",
                    detail: "Ad account updated successfully",
                    life: 3000,
                });
            } else {
                // Create new account
                const newAccount = await createAdAccount(accountForm.value);
                toast.add({
                    severity: "success",
                    summary: "Success",
                    detail: "Ad account created successfully",
                    life: 3000,
                });
                // If this is the default account, select it
                if (newAccount.is_default) {
                    selectedAccount.value = newAccount;
                }
            }
            await loadAdAccounts();
            closeAccountDialog();
        } catch (error) {
            toast.add({
                severity: "error",
                summary: "Error",
                detail: error.message || "Failed to save ad account",
                life: 5000,
            });
        } finally {
            savingAccount.value = false;
        }
    }

    async function deleteAccount(account) {
        try {
            await deleteAdAccount(account.id);
            toast.add({
                severity: "success",
                summary: "Success",
                detail: "Ad account deleted successfully",
                life: 3000,
            });
            // Clear selection if deleted account was selected
            if (selectedAccount.value?.id === account.id) {
                selectedAccount.value = null;
            }
            await loadAdAccounts();
        } catch (error) {
            toast.add({
                severity: "error",
                summary: "Error",
                detail: error.message || "Failed to delete ad account",
                life: 5000,
            });
        }
    }

    function confirmDeleteAccount(account) {
        confirm.require({
            message: `Are you sure you want to delete the ad account "${account.name}"? This action cannot be undone.`,
            header: "Confirm Delete",
            icon: "pi pi-exclamation-triangle",
            accept: () => {
                deleteAccount(account);
            },
        });
    }

    return {
        // State
        adAccounts,
        selectedAccount,
        loadingAccounts,
        savingAccount,
        testingConnection,
        connectionStatus,
        connectionLastChecked,
        showAdAccountDialog,
        editingAccount,
        accountForm,
        // Methods
        loadAdAccounts,
        loadDefaultAccount,
        selectAccount,
        openCreateAdAccountDialog,
        editAdAccount,
        closeAccountDialog,
        testConnection,
        saveAdAccount,
        deleteAccount,
        confirmDeleteAccount,
    };
}
