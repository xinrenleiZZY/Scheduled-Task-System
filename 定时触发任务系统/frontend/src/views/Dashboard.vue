<template>
  <div class="page">
    <div class="page-header">
      <div class="page-title">欢迎使用 HZX 定时任务系统</div>
      <el-button :icon="Refresh" @click="load" :loading="loading">刷新</el-button>
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
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span style="font-weight: 600">关注的定时任务</span>
          <el-button text type="primary" @click="$router.push('/tasks')">管理全部任务</el-button>
        </div>
      </template>

      <el-empty v-if="!pinnedTasks.length" description="暂未关注任何任务，可在任务管理中「关注」" />

      <div v-else class="card-grid">
        <el-card v-for="task in pinnedTasks" :key="task.id" shadow="hover">
          <div style="display: flex; justify-content: space-between; align-items: center">
            <span style="font-weight: 600">{{ task.name }}</span>
            <el-tag :type="task.enabled ? 'success' : 'info'" size="small">
              {{ task.enabled ? '已启用' : '已停用' }}
            </el-tag>
          </div>
          <div class="hint" style="margin-top: 8px">
            <div>调度：{{ scheduleText(task) }}</div>
            <div>成功 / 失败：{{ task.stats.success_count }} / {{ task.stats.fail_count }}</div>
            <div>上次运行：{{ task.stats.last_run_time || '从未运行' }}</div>
          </div>
          <div style="margin-top: 10px; display: flex; gap: 8px">
            <el-button size="small" type="primary" :icon="VideoPlay" @click="run(task)">立即执行</el-button>
            <el-button size="small" @click="openLogs(task)">日志</el-button>
          </div>
        </el-card>
      </div>
    </el-card>

    <el-card shadow="never" style="margin-top: 16px">
      <template #header><span style="font-weight: 600">快捷入口</span></template>
      <el-space wrap :size="12">
        <el-button @click="$router.push('/tasks')">新建定时任务</el-button>
        <el-button @click="$router.push('/bots')">配置应用机器人</el-button>
        <el-button @click="$router.push('/chats')">配置群聊</el-button>
        <el-button @click="$router.push('/users')">配置用户</el-button>
        <el-button @click="$router.push('/backup')">备份与恢复</el-button>
        <el-button @click="$router.push('/tutorial')">查看使用教程</el-button>
      </el-space>
    </el-card>

    <el-dialog v-model="logVisible" :title="`任务日志 - ${logTask?.name || ''}`" width="720px">
      <div class="log-box">{{ logText || '暂无日志' }}</div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, VideoPlay } from '@element-plus/icons-vue'
import { getDashboard, getTaskLogs, runTaskNow } from '../api'

const loading = ref(false)
const stats = ref({})
const pinnedTasks = ref([])
const logVisible = ref(false)
const logTask = ref(null)
const logText = ref('')

const statCards = computed(() => [
  { label: '任务总数', value: stats.value.total_tasks ?? 0, cls: '' },
  { label: '已启用', value: stats.value.enabled_tasks ?? 0, cls: 'success' },
  { label: '成功次数', value: stats.value.success_count ?? 0, cls: 'success' },
  { label: '失败次数', value: stats.value.fail_count ?? 0, cls: 'danger' },
  { label: '成功率', value: (stats.value.success_rate ?? 0) + '%', cls: '' }
])

function scheduleText(task) {
  if (task.schedule_type === 'cron') return `Cron：${task.cron_expr}`
  const s = task.interval_seconds
  if (s % 86400 === 0) return `每 ${s / 86400} 天`
  if (s % 3600 === 0) return `每 ${s / 3600} 小时`
  if (s % 60 === 0) return `每 ${s / 60} 分钟`
  return `每 ${s} 秒`
}

async function load() {
  loading.value = true
  try {
    const data = await getDashboard()
    stats.value = data.stats
    pinnedTasks.value = data.pinned_tasks
  } finally {
    loading.value = false
  }
}

async function run(task) {
  const res = await runTaskNow(task.id)
  ElMessage[res.success ? 'success' : 'error'](res.message)
  setTimeout(load, 1200)
}

async function openLogs(task) {
  logTask.value = task
  logVisible.value = true
  const logs = await getTaskLogs(task.id, 100)
  logText.value = logs.length
    ? logs
        .slice()
        .reverse()
        .map((l) => `[${l.ts}] ${l.status === 'success' ? '✅' : '❌'} ${l.message}`)
        .join('\n')
    : ''
}

onMounted(load)
</script>
