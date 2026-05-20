<template>
  <div class="storage-widget" v-if="usage">
    <div class="widget-header">
      <div class="widget-title">Storage Usage</div>
      <div class="plan-badge">{{ planLabel }}</div>
    </div>

    <div class="storage-bar-wrap">
      <div class="storage-bar">
        <div class="storage-fill" :style="{ width: fillPercent + '%' }" :class="{ warning: fillPercent > 80, danger: fillPercent > 95 }"></div>
      </div>
      <div class="storage-labels">
        <span>{{ usage.storage_used_gb }} GB used</span>
        <span>{{ usage.storage_included_gb }} GB included</span>
      </div>
    </div>

    <div class="storage-stats">
      <div class="stat-item">
        <div class="stat-label">Used</div>
        <div class="stat-val">{{ usage.storage_used_gb }} GB</div>
      </div>
      <div class="stat-item">
        <div class="stat-label">Included</div>
        <div class="stat-val">{{ usage.storage_included_gb }} GB</div>
      </div>
      <div class="stat-item">
        <div class="stat-label">Overage</div>
        <div class="stat-val" :class="{ 'text-warn': usage.storage_overage_gb > 0 }">{{ usage.storage_overage_gb }} GB</div>
      </div>
      <div class="stat-item">
        <div class="stat-label">Est. Extra Charge</div>
        <div class="stat-val" :class="{ 'text-warn': usage.estimated_overage_charge > 0 }">${{ usage.estimated_overage_charge.toFixed(2) }}</div>
      </div>
    </div>

    <div class="overage-note" v-if="usage.storage_overage_gb > 0">
      ⚠ You are {{ usage.storage_overage_gb }} GB over your plan limit. Extra storage is billed at ${{ usage.overage_rate_per_gb }}/GB.
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getStorageUsage } from '@/api/index.js'

const usage = ref(null)

const planLabel = computed(() => {
  const map = { basic: 'Basic Plan', professional: 'Professional Plan', premium: 'Premium Plan' }
  return usage.value ? map[usage.value.plan] || 'Active Plan' : ''
})

const fillPercent = computed(() => {
  if (!usage.value) return 0
  const pct = (usage.value.storage_used_mb / usage.value.storage_included_mb) * 100
  return Math.min(pct, 100)
})

onMounted(async () => {
  try {
    const { data } = await getStorageUsage()
    usage.value = data
  } catch {
    // silently ignore if org has no subscription yet
  }
})
</script>

<style scoped>
.storage-widget { background: var(--surface); border: 1.5px solid var(--border); border-radius: 14px; padding: 20px 24px; }

.widget-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.widget-title  { font-size: 15px; font-weight: 700; }
.plan-badge    { font-size: 11px; font-weight: 700; background: rgba(108,99,255,.12); color: var(--accent); padding: 3px 10px; border-radius: 20px; }

.storage-bar-wrap { margin-bottom: 16px; }
.storage-bar   { height: 10px; background: var(--border); border-radius: 8px; overflow: hidden; }
.storage-fill  { height: 100%; background: var(--accent); border-radius: 8px; transition: width .4s ease; }
.storage-fill.warning { background: #f59e0b; }
.storage-fill.danger  { background: #ef4444; }
.storage-labels { display: flex; justify-content: space-between; font-size: 12px; color: var(--text-muted); margin-top: 6px; }

.storage-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 14px; }
.stat-item     { text-align: center; }
.stat-label    { font-size: 11px; color: var(--text-muted); margin-bottom: 4px; }
.stat-val      { font-size: 16px; font-weight: 700; }
.text-warn     { color: #f59e0b; }

.overage-note  { background: rgba(245,158,11,.1); border: 1px solid rgba(245,158,11,.3); border-radius: 8px; padding: 10px 14px; font-size: 13px; color: #b45309; }
</style>
