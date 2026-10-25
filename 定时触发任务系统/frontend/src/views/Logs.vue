<template>
  <div class="page">
    <div class="page-header">
      <div class="page-title">日志中心</div>
      <el-button :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
    </div>

    <el-card shadow="never">
      <el-tabs v-model="tab">
        <el-tab-pane label="系统日志" name="system">
          <div style="margin-bottom: 10px">
            <el-button size="small" danger :icon="Delete" @click="clearSystem">清空系统日志</el-button>
          </div>
          <el-table :data="systemLogs" v-loading="loading" stripe max-height="560">
            <el-table-column label="时间" width="180">
              <template #default="{ row }">{{ row.ts }}</template>
            </el-table-column>
            <el-table-column label="级别" width="90" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="levelType(row.level)">{{ row.level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="source" label="来源" width="140" show-overflow-tooltip />
            <el-table-column prop="message" label="内容" min-width="320" show-overflow-tooltip />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="任务日志概览" name="tasks">
          <el-table :data="taskOverview" v-loading="loading" stripe>
            <el-table-column prop="task_name" label="任务名称" min-width="200" show-overflow-tooltip />
            <el-table-column prop="count" label="日志条数" width="120" align="center" />
            <el-table-column label="最近记录" width="200">
              <template #default="{ row }">{{ row.last_ts || '—' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button size="small" type="primary" link @click="openLogs(row)">查看日志</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!loading && !taskOverview.length" description="暂无任务日志" />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="logVisible" :title="`任务日志 - ${logTask?.task_name || ''}`" width="760px">
      <div class="log-box">{{ logText || '暂无日志' }}</div>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Refresh } from '@element-plus/icons-vue'
import { clearSystemLogs, getSystemLogs, getTaskLogOverview, getTaskLogs } from '../api'

const loading = ref(false)
const tab = ref('system')
const systemLogs = ref([])
const taskOverview = ref([])
const logVisible = ref(false)
const logTask = ref(null)
const logText = ref('')

function levelType(level) {
  if (level === 'ERROR') return 'danger'
  if (level === 'WARNING' || level === 'WARN') return 'warning'
  return 'info'
}

async function load() {
  loading.value = true
  try {
    const [sys, overview] = await Promise.all([getSystemLogs(300), getTaskLogOverview()])
    systemLogs.value = sys
    taskOverview.value = overview
  } finally {
    loading.value = false
  }
}

async function clearSystem() {
  await ElMessageBox.confirm('确认清空全部系统日志？', '提示', { type: 'warning' })
  await clearSystemLogs()
  ElMessage.success('系统日志已清空')
  load()
}

async function openLogs(row) {
  logTask.value = row
  logVisible.value = true
  const logs = await getTaskLogs(row.task_id, 200)
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
