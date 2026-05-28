<template>
    <div class="settings-users">
        <div class="page-header">
            <div>
                <h1>Users</h1>
                <p>Manage who has access to this application.</p>
            </div>
            <Button
                v-if="authStore.isAdmin"
                label="Add User"
                icon="pi pi-plus"
                @click="openAddDialog"
            />
        </div>

        <div class="users-table-wrapper">
            <DataTable
                :value="users"
                :loading="loading"
                stripedRows
                class="users-table"
            >
                <Column field="email" header="Email">
                    <template #body="{ data }">
                        <span class="user-email">{{ data.email }}</span>
                        <span v-if="data.id === authStore.user?.id" class="you-badge">you</span>
                    </template>
                </Column>
                <Column field="is_admin" header="Role">
                    <template #body="{ data }">
                        <Tag
                            :value="data.is_admin ? 'Admin' : 'User'"
                            :severity="data.is_admin ? 'info' : 'secondary'"
                        />
                    </template>
                </Column>
                <Column field="is_active" header="Status">
                    <template #body="{ data }">
                        <Tag
                            :value="data.is_active ? 'Active' : 'Inactive'"
                            :severity="data.is_active ? 'success' : 'danger'"
                        />
                    </template>
                </Column>
                <Column field="created_at" header="Created">
                    <template #body="{ data }">
                        {{ formatDate(data.created_at) }}
                    </template>
                </Column>
                <Column v-if="authStore.isAdmin" header="" style="width: 60px">
                    <template #body="{ data }">
                        <Button
                            icon="pi pi-trash"
                            severity="danger"
                            text
                            rounded
                            :disabled="data.id === authStore.user?.id"
                            @click="confirmDelete(data)"
                        />
                    </template>
                </Column>
                <template #empty>
                    <div class="empty-state">No users found.</div>
                </template>
            </DataTable>
        </div>

        <!-- Add User Dialog -->
        <Dialog
            v-model:visible="showAddDialog"
            header="Add User"
            :style="{ width: '420px' }"
            modal
        >
            <form @submit.prevent="submitAddUser" class="add-user-form">
                <div class="field">
                    <label>Email Address</label>
                    <InputText
                        v-model="newUser.email"
                        type="email"
                        placeholder="user@example.com"
                        class="w-full"
                        :class="{ 'p-invalid': formErrors.email }"
                        required
                    />
                    <small v-if="formErrors.email" class="p-error">{{ formErrors.email }}</small>
                </div>
                <div class="field">
                    <label>Password</label>
                    <Password
                        v-model="newUser.password"
                        placeholder="Set a password"
                        :feedback="false"
                        toggleMask
                        class="w-full"
                        :inputClass="'w-full'"
                        :class="{ 'p-invalid': formErrors.password }"
                        required
                    />
                    <small v-if="formErrors.password" class="p-error">{{ formErrors.password }}</small>
                </div>
                <div class="field-checkbox">
                    <Checkbox v-model="newUser.is_admin" inputId="is_admin" :binary="true" />
                    <label for="is_admin">Grant admin access</label>
                </div>
                <div class="dialog-footer">
                    <Button label="Cancel" severity="secondary" outlined @click="showAddDialog = false" type="button" />
                    <Button label="Add User" icon="pi pi-check" type="submit" :loading="saving" />
                </div>
            </form>
        </Dialog>

        <!-- Confirm Delete Dialog -->
        <ConfirmDialog />
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { useAuthStore } from '@/store/authStore'
import { getUsers, createUser, deleteUser } from '@/api/usersApi'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Checkbox from 'primevue/checkbox'
import ConfirmDialog from 'primevue/confirmdialog'

const authStore = useAuthStore()
const confirm = useConfirm()
const toast = useToast()

const users = ref([])
const loading = ref(false)
const saving = ref(false)
const showAddDialog = ref(false)

const newUser = ref({ email: '', password: '', is_admin: false })
const formErrors = ref({})

async function fetchUsers() {
    loading.value = true
    try {
        users.value = await getUsers()
    } catch (e) {
        toast.add({ severity: 'error', summary: 'Error', detail: e.message, life: 4000 })
    } finally {
        loading.value = false
    }
}

function openAddDialog() {
    newUser.value = { email: '', password: '', is_admin: false }
    formErrors.value = {}
    showAddDialog.value = true
}

async function submitAddUser() {
    formErrors.value = {}
    if (!newUser.value.email) {
        formErrors.value.email = 'Email is required'
        return
    }
    if (!newUser.value.password || newUser.value.password.length < 6) {
        formErrors.value.password = 'Password must be at least 6 characters'
        return
    }
    saving.value = true
    try {
        await createUser(newUser.value)
        toast.add({ severity: 'success', summary: 'User added', detail: `${newUser.value.email} has been created.`, life: 3000 })
        showAddDialog.value = false
        await fetchUsers()
    } catch (e) {
        toast.add({ severity: 'error', summary: 'Error', detail: e.message, life: 5000 })
    } finally {
        saving.value = false
    }
}

function confirmDelete(user) {
    confirm.require({
        message: `Are you sure you want to delete ${user.email}? This cannot be undone.`,
        header: 'Delete User',
        icon: 'pi pi-exclamation-triangle',
        acceptSeverity: 'danger',
        acceptLabel: 'Delete',
        rejectLabel: 'Cancel',
        accept: async () => {
            try {
                await deleteUser(user.id)
                toast.add({ severity: 'success', summary: 'Deleted', detail: `${user.email} has been removed.`, life: 3000 })
                await fetchUsers()
            } catch (e) {
                toast.add({ severity: 'error', summary: 'Error', detail: e.message, life: 5000 })
            }
        },
    })
}

function formatDate(dateStr) {
    if (!dateStr) return '—'
    return new Date(dateStr).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

onMounted(fetchUsers)
</script>

<style scoped>
.settings-users {
    max-width: 900px;
    margin: 0 auto;
}

.page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 2rem;
}

.page-header h1 {
    font-size: 1.75rem;
    font-weight: 700;
    color: #1f2937;
    margin-bottom: 0.25rem;
}

.page-header p {
    color: #6b7280;
    font-size: 0.95rem;
}

.users-table-wrapper {
    background: white;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    overflow: hidden;
}

.user-email {
    font-weight: 500;
    color: #1f2937;
}

.you-badge {
    display: inline-block;
    margin-left: 0.5rem;
    padding: 0.1rem 0.4rem;
    background: #f3f4f6;
    color: #6b7280;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.empty-state {
    text-align: center;
    padding: 2rem;
    color: #9ca3af;
}

.add-user-form {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
}

.field {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
}

.field label {
    font-size: 0.875rem;
    font-weight: 600;
    color: #374151;
}

.field-checkbox {
    display: flex;
    align-items: center;
    gap: 0.6rem;
}

.field-checkbox label {
    font-size: 0.875rem;
    color: #374151;
    cursor: pointer;
}

.field :deep(.p-password),
.field :deep(.p-password-input) {
    width: 100%;
}

.dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    margin-top: 0.5rem;
}
</style>
