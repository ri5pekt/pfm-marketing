<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1>Dashboard</h1>
      <p>Welcome to PFM Marketing Campaign Management</p>
    </div>
    <div class="services-grid">
      <Card
        v-for="service in services"
        :key="service.id"
        class="service-card"
        @click="navigateToService(service.path)"
      >
        <template #content>
          <div class="service-content">
            <div class="service-icon" :style="{ background: service.gradient }">
              <i :class="service.icon"></i>
            </div>
            <h3>{{ service.title }}</h3>
            <p>{{ service.description }}</p>
            <div class="service-footer">
              <span>Open Service</span>
              <i class="pi pi-arrow-right"></i>
            </div>
          </div>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import Card from 'primevue/card'

const router = useRouter()

const services = ref([
  {
    id: 1,
    title: 'Meta Campaign Rules',
    description: 'Create and manage automated rules for Meta campaigns with scheduled checks and logs',
    icon: 'pi pi-facebook',
    gradient: 'linear-gradient(135deg, #0099FF 0%, #0064E0 100%)',
    path: '/meta-campaigns'
  }
])

function navigateToService(path) {
  router.push(path)
}
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard-header {
  margin-bottom: 2rem;
}

.dashboard-header h1 {
  font-size: 2rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.dashboard-header p {
  color: #6b7280;
  font-size: 1rem;
}

.services-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.5rem;
}

.service-card {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
}

.service-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.service-content {
  padding: 1.5rem;
}

.service-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 2rem;
  margin-bottom: 1rem;
}

.service-content h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.service-content p {
  color: #6b7280;
  font-size: 0.875rem;
  line-height: 1.5;
  margin-bottom: 1rem;
}

.service-footer {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #0099FF;
  font-weight: 600;
  font-size: 0.875rem;
  margin-top: 1rem;
}

.service-footer i {
  transition: transform 0.2s;
}

.service-card:hover .service-footer i {
  transform: translateX(4px);
}
</style>

