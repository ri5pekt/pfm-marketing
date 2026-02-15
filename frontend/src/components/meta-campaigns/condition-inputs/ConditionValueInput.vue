<template>
    <div class="value-input-wrapper">
        <StatusValueInput
            v-if="inputType === 'status'"
            :value="value"
            :status-options="statusOptions"
            @update:value="$emit('update:value', $event)"
        />

        <SpecialValueInput
            v-else-if="inputType === 'special'"
            :value="value"
            @update:value="$emit('update:value', $event)"
        />

        <CppWinningDaysInput
            v-else-if="inputType === 'cpp-winning-days'"
            :value="value"
            :threshold="threshold"
            @update:value="$emit('update:value', $event)"
            @update:threshold="$emit('update:threshold', $event)"
        />

        <NumericValueInput
            v-else-if="inputType === 'numeric'"
            :value="value"
            @update:value="$emit('update:value', $event)"
        />

        <TextValueInput
            v-else
            :value="value"
            :placeholder="placeholder"
            @update:value="$emit('update:value', $event)"
        />
    </div>
</template>

<script setup>
import { computed } from "vue";
import StatusValueInput from "./StatusValueInput.vue";
import SpecialValueInput from "./SpecialValueInput.vue";
import CppWinningDaysInput from "./CppWinningDaysInput.vue";
import NumericValueInput from "./NumericValueInput.vue";
import TextValueInput from "./TextValueInput.vue";
import { getValueInputType } from "@/utils/conditionFieldConfig";
import { getValuePlaceholder } from "@/utils/specialValues";

const props = defineProps({
    field: {
        type: String,
        required: true,
    },
    value: {
        type: [String, Number, Object, null],
        default: null,
    },
    threshold: {
        type: [Number, null],
        default: null,
    },
    statusOptions: {
        type: Array,
        default: () => [],
    },
});

defineEmits(["update:value", "update:threshold"]);

const inputType = computed(() => {
    return getValueInputType(props.field, props.value);
});

const placeholder = computed(() => {
    return getValuePlaceholder(props.field);
});
</script>

<style scoped>
.value-input-wrapper {
    width: 100%;
}
</style>
