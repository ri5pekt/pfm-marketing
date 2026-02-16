<template>
    <div class="condition-group-divider">
        <div class="divider-line"></div>
        <div class="divider-label">OR</div>
        <div class="divider-line"></div>
    </div>
</template>

<style scoped>
.condition-group-divider {
    display: flex;
    align-items: center;
    margin: 1.5rem 0;
}

.divider-line {
    flex: 1;
    height: 2px;
    background: linear-gradient(to right, transparent, #d1d5db 20%, #d1d5db 80%, transparent);
}

.divider-label {
    padding: 0.375rem 1.25rem;
    font-weight: 700;
    font-size: 0.875rem;
    color: #3b82f6;
    background: white;
    border: 2px solid #3b82f6;
    border-radius: 20px;
    margin: 0 1rem;
}
</style>
