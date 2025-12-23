<template>
    <Dialog
        :visible="modelValue"
        @update:visible="$emit('update:modelValue', $event)"
        header="Add Scope Filter"
        :modal="true"
        :style="{ width: '400px' }"
    >
        <div class="field">
            <label>Scope Type *</label>
            <Select
                v-model="localSelectedScopeType"
                :options="availableScopeTypes"
                optionLabel="label"
                optionValue="value"
                placeholder="Select scope type"
                class="w-full"
            />
        </div>
        <template #footer>
            <Button
                label="Cancel"
                severity="secondary"
                @click="handleCancel"
            />
            <Button label="Add" @click="handleAdd" :disabled="!localSelectedScopeType" />
        </template>
    </Dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Select from 'primevue/select'
import Button from 'primevue/button'

const props = defineProps({
    modelValue: {
        type: Boolean,
        default: false,
    },
    availableScopeTypes: {
        type: Array,
        default: () => [],
    },
})

const emit = defineEmits(['update:modelValue', 'add'])

const localSelectedScopeType = ref(null)

watch(() => props.modelValue, (newVal) => {
    if (!newVal) {
        localSelectedScopeType.value = null
    }
})

function handleCancel() {
    emit('update:modelValue', false)
    localSelectedScopeType.value = null
}

function handleAdd() {
    if (localSelectedScopeType.value) {
        emit('add', localSelectedScopeType.value)
        emit('update:modelValue', false)
        localSelectedScopeType.value = null
    }
}
</script>

<style scoped>
.field {
    margin-bottom: 1rem;
}

.field label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: #374151;
}
</style>

