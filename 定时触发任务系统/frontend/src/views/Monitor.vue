<template>
  <div class="page">
    <div class="page-header">
      <div class="page-title">任务监控</div>
      <div style="display: flex; align-items: center; gap: 12px">
        <el-switch v-model="autoRefresh" inline-prompt active-text="自动" inactive-text="手动" />
        <el-button :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :xs="12" :sm="8" :md="4" v-for="card in statCards" :key="card.label">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-value" :class="card.cls">{{ card.value }}</div>
          <div class="stat-label">{{ card.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" style="margin-top: 16px">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span style="font-weight: 600">任务运行状态</span>
          <span class="hint">自动刷新：每 10 秒 · 最后更新 {{ lastUpdate || '—' }}</span>
        </div>
      </template>

      <el-table :data="tasks" v-loading="loading" stripe>
        <el-table-column prop="name" label="任务名称" min-width="150" show-overflow-tooltip />
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.enabled ? 'success' : 'info'">
              {{ row.enabled ? '运行中' : '已停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="上次结果" width="110" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.stats.last_status === 'success'" type="success" size="small">成功</el-tag>
            <el-tag v-else-if="row.stats.last_status === 'fail'" type="danger" size="small">失败</el-tag>
            <span v-else class="hint">未运行</span>
          </template>
        </el-table-column>
        <el-table-column label="上次运行" min-width="160">
          <template #default="{ row }">{{ row.stats.last_run_time || '从未运行' }}</template>
        </el-table-column>
        <el-table-column label="耗时" width="100" align="center">
          <template #default="{ row }">
            {{ row.stats.last_duration ? row.stats.last_duration.toFixed(2) + 's' : '—' }}
          </template>
        </el-table-column>
        <el-table-column label="成功/失败" width="110" align="center">
          <template #default="{ row }">
            <span style="color: #67c23a">{{ row.stats.success_count }}</span> /
            <span style="color: #f56c6c">{{ row.stats.fail_count }}</span>
          </template>
        </el-table-column>
        <el-table-column label="成功率" width="100" align="center">
          <template #default="{ row }">{{ row.stats.success_rate }}%</template>
        </el-table-column>
        <el-table-column label="最近错误" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span :style="{ color: row.stats.last_error ? '#f56c6c' : '' }">
              {{ row.stats.last_error || '—' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="run(row)">立即执行</el-button>
            <el-button size="small" link @click="openLogs(row)">日志</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="logVisible" :title="`运行日志 - ${logTask?.name || ''}`" width="760px">
      <div style="margin-bottom: 10px">
        <el-button size="small" :icon="Refresh" @click="loadLogs">刷新</el-button>
      </div>
      <div class="log-box">{{ logText || '暂无日志' }}</div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { getDashboard, getTaskLogs, listTasks, runTaskNow } from '../api'

const loading = ref(false)
const autoRefresh = ref(true)
const stats = ref({})
const tasks = ref([])
const lastUpdate = ref('')
const logVisible = ref(false)
const logTask = ref(null)
const logText = ref('')
let timer = null

const statCards = computed(() => [
  { label: '任务总数', value: stats.value.total_tasks ?? 0, cls: '' },
  { label: '已启用', value: stats.value.enabled_tasks ?? 0, cls: 'success' },
  { label: '成功次数', value: stats.value.success_count ?? 0, cls: 'success' },
  { label: '失败次数', value: stats.value.fail_count ?? 0, cls: 'danger' },
  { label: '成功率', value: (stats.value.success_rate ?? 0) + '%', cls: '' }
])

async function load() {
  loading.value = true
  try {
    const [dash, list] = await Promise.all([getDashboard(), listTasks()])
    stats.value = dash.stats
    tasks.value = list
    lastUpdate.value = new Date().toLocaleTimeString()
  } finally {
    loading.value = false
  }
}

async function run(row) {
  const res = await runTaskNow(row.id)
  ElMessage[res.success ? 'success' : 'error'](res.message)
  setTimeout(load, 1200)
}

async function openLogs(row) {
  logTask.value = row
  logVisible.value = true
  await loadLogs()
}

async function loadLogs() {
  if (!logTask.value) return
  const logs = await getTaskLogs(logTask.value.id, 200)
  logText.value = logs.length
    ? logs
        .slice()
        .reverse()
        .map((l) => `[${l.ts}] ${l.status === 'success' ? '✅' : '❌'} ${l.message}`)
        .join('\n')
    : ''
}

function startTimer() {
  stopTimer()
  timer = setInterval(() => {
    if (autoRefresh.value) load()
  }, 10000)
}

function stopTimer() {
  if (timer) clearInterval(timer)
  timer = null
}

onMounted(() => {
  load()
  startTimer()
})

onUnmounted(stopTimer)
</script>
