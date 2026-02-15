<template>
    <div class="ungrouped-rules-container">
        <div class="ungrouped-header">
            <i class="pi pi-list ungrouped-icon"></i>
            <span>Ungrouped Rules</span>
        </div>
        <VueDraggable
            v-model="localRules"
            :animation="200"
            group="rules"
            handle=".rule-drag-handle"
            @start="$emit('drag-start')"
            @end="$emit('drag-end')"
            class="ungrouped-rules-list"
            :class="{ 'empty-drop-zone': rules.length === 0 && isDragging }"
        >
            <RuleListItem
                v-for="rule in localRules"
                :key="rule.id"
                :rule="rule"
                :testing-rule-id="testingRuleId"
                :is-ungrouped="true"
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
import { computed } from 'vue';
import { VueDraggable } from 'vue-draggable-plus';
import RuleListItem from './RuleListItem.vue';

const props = defineProps({
    rules: {
        type: Array,
        required: true,
    },
    testingRuleId: {
        type: [Number, null],
        default: null,
    },
    isDragging: {
        type: Boolean,
        default: false,
    },
});

const emit = defineEmits(['update:rules', 'drag-start', 'drag-end', 'test-rule', 'cancel-test', 'view-logs', 'edit-rule', 'delete-rule']);

const localRules = computed({
    get: () => props.rules,
    set: (value) => emit('update:rules', value),
});
</script>

<style scoped>
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
    content: 'Drop rules here to ungroup';
    color: var(--text-color-secondary);
    font-style: italic;
}
</style>
