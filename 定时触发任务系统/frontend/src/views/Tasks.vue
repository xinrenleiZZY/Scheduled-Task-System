<template>
  <div class="page">
    <div class="page-header">
      <div class="page-title">任务管理</div>
      <el-button type="primary" :icon="Plus" @click="openCreate">新建任务</el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="tasks" v-loading="loading" stripe>
        <el-table-column prop="name" label="任务名称" min-width="160" show-overflow-tooltip />
        <el-table-column label="关注" width="80" align="center">
          <template #default="{ row }">
            <el-icon v-if="row.pinned" color="#e6a23c"><StarFilled /></el-icon>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="启用" width="90" align="center">
          <template #default="{ row }">
            <el-switch :model-value="row.enabled" @change="toggle(row)" />
          </template>
        </el-table-column>
        <el-table-column label="调度" min-width="150">
          <template #default="{ row }">{{ scheduleText(row) }}</template>
        </el-table-column>
        <el-table-column label="发送方式" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="row.send_type === 'api' ? 'warning' : 'primary'">
              {{ row.send_type === 'api' ? '应用机器人' : 'Webhook' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="目标" min-width="140">
          <template #default="{ row }">{{ targetText(row) }}</template>
        </el-table-column>
        <el-table-column label="成功/失败" width="110" align="center">
          <template #default="{ row }">
            <span style="color: #67c23a">{{ row.stats.success_count }}</span> /
            <span style="color: #f56c6c">{{ row.stats.fail_count }}</span>
          </template>
        </el-table-column>
        <el-table-column label="上次运行" min-width="160">
          <template #default="{ row }">{{ row.stats.last_run_time || '从未运行' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="run(row)">执行</el-button>
            <el-button size="small" link @click="openEdit(row)">编辑</el-button>
            <el-button size="small" link @click="openLogs(row)">日志</el-button>
            <el-button size="small" link @click="pin(row)">{{ row.pinned ? '取消关注' : '关注' }}</el-button>
            <el-button size="small" type="danger" link @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建 / 编辑 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑任务' : '新建任务'" width="680px">
      <el-form :model="form" label-width="110px">
        <el-form-item label="任务名称">
          <el-input v-model="form.name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.enabled" />
          <span style="margin-left: 16px">关注到首页</span>
          <el-switch v-model="form.pinned" style="margin-left: 8px" />
        </el-form-item>
        <el-form-item label="调度方式">
          <el-radio-group v-model="form.schedule_type">
            <el-radio value="interval">间隔执行</el-radio>
            <el-radio value="cron">Cron 表达式</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="form.schedule_type === 'interval'" label="间隔">
          <el-input-number v-model="intervalValue" :min="1" />
          <el-select v-model="intervalUnit" style="width: 100px; margin-left: 10px">
            <el-option label="秒" value="second" />
            <el-option label="分钟" value="minute" />
            <el-option label="小时" value="hour" />
            <el-option label="天" value="day" />
          </el-select>
        </el-form-item>
        <el-form-item v-else label="Cron">
          <el-input v-model="form.cron_expr" placeholder="0 9 * * *" class="mono" />
          <div class="hint" style="margin-top: 6px">
            格式：分 时 日 月 周（标准 cron，周：0/7=周日，1=周一 … 6=周六）。例：<span class="mono">0 9 * * *</span> 表示每天 9:00，<span class="mono">1 18 * * 1-6</span> 表示周一~周六 18:01
          </div>
        </el-form-item>

        <el-form-item label="发送方式">
          <el-radio-group v-model="form.send_type">
            <el-radio value="webhook">Webhook（自定义机器人）</el-radio>
            <el-radio value="api">应用机器人 API</el-radio>
          </el-radio-group>
        </el-form-item>

        <template v-if="form.send_type === 'webhook'">
          <el-form-item label="Webhook 地址">
            <el-input v-model="form.webhook_url" placeholder="留空则使用全局默认" />
          </el-form-item>
          <el-form-item label="签名 Secret">
            <el-input v-model="form.secret" placeholder="留空则使用全局默认" show-password />
          </el-form-item>
        </template>

        <template v-else>
          <el-form-item label="应用机器人">
            <el-select v-model="form.bot_id" placeholder="请选择应用机器人" style="width: 100%">
              <el-option v-for="b in bots" :key="b.id" :label="b.name || b.app_id" :value="b.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="目标类型">
            <el-radio-group v-model="form.chat_type">
              <el-radio value="chat">群聊</el-radio>
              <el-radio value="user">用户/机器人</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="发送目标">
            <el-select v-model="form.chat_id" placeholder="请选择目标" style="width: 100%">
              <template v-if="form.chat_type === 'chat'">
                <el-option v-for="c in chats" :key="c.id" :label="c.name" :value="c.id" />
              </template>
              <template v-else>
                <el-option v-for="u in users" :key="u.id" :label="u.name" :value="u.id" />
              </template>
            </el-select>
          </el-form-item>
        </template>

        <el-form-item label="@ 用户">
          <el-select
            v-model="form.at_user_ids"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="选择或输入 open_id / user_id"
            style="width: 100%"
          >
            <el-option v-for="u in users" :key="u.id" :label="u.name" :value="u.open_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="@ 所有人">
          <el-switch v-model="form.at_all" />
        </el-form-item>

        <el-form-item label="消息内容">
          <el-input v-model="form.message" type="textarea" :rows="4" placeholder="定时任务提醒" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- 日志 -->
    <el-dialog v-model="logVisible" :title="`任务日志 - ${logTask?.name || ''}`" width="760px">
      <div style="margin-bottom: 10px">
        <el-button size="small" @click="loadLogs">刷新</el-button>
        <el-button size="small" type="danger" @click="clearLogs">清空日志</el-button>
      </div>
      <div class="log-box">{{ logText || '暂无日志' }}</div>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, StarFilled } from '@element-plus/icons-vue'
import {
  clearTaskLogs,
  createTask,
  deleteTask,
  getTaskLogs,
  listBots,
  listChats,
  listTasks,
  listUsers,
  pinTask,
  runTaskNow,
  toggleTask,
  updateTask
} from '../api'

const loading = ref(false)
const saving = ref(false)
const tasks = ref([])
const bots = ref([])
const chats = ref([])
const users = ref([])

const dialogVisible = ref(false)
const editing = ref(false)
const editingId = ref('')

const logVisible = ref(false)
const logTask = ref(null)
const logText = ref('')

const intervalValue = ref(1)
const intervalUnit = ref('day')

const form = reactive(emptyForm())

function emptyForm() {
  return {
    name: '新任务',
    enabled: true,
    pinned: false,
    schedule_type: 'interval',
    interval_seconds: 86400,
    cron_expr: '0 9 * * *',
    webhook_url: '',
    secret: '',
    send_type: 'webhook',
    bot_id: '',
    chat_id: '',
    chat_type: 'chat',
    message: '定时任务提醒',
    at_user_ids: [],
    at_user_names: [],
    at_all: false
  }
}

const UNIT = { second: 1, minute: 60, hour: 3600, day: 86400 }

function scheduleText(task) {
  if (task.schedule_type === 'cron') return `Cron：${task.cron_expr}`
  const s = task.interval_seconds
  if (s % 86400 === 0) return `每 ${s / 86400} 天`
  if (s % 3600 === 0) return `每 ${s / 3600} 小时`
  if (s % 60 === 0) return `每 ${s / 60} 分钟`
  return `每 ${s} 秒`
}

function targetText(task) {
  if (task.send_type === 'webhook') return task.webhook_url ? '自定义 Webhook' : '默认 Webhook'
  const bot = bots.value.find((b) => b.id === task.bot_id)
  const target =
    task.chat_type === 'chat'
      ? chats.value.find((c) => c.id === task.chat_id)
      : users.value.find((u) => u.id === task.chat_id)
  return `${bot?.name || '未选机器人'} → ${target?.name || '未选目标'}`
}

async function load() {
  loading.value = true
  try {
    ;[tasks.value, bots.value, chats.value, users.value] = await Promise.all([
      listTasks(),
      listBots(),
      listChats(),
      listUsers()
    ])
  } finally {
    loading.value = false
  }
}

function openCreate() {
  Object.assign(form, emptyForm())
  editing.value = false
  editingId.value = ''
  intervalValue.value = 1
  intervalUnit.value = 'day'
  dialogVisible.value = true
}

function openEdit(row) {
  Object.assign(form, emptyForm(), row)
  form.at_user_ids = [...(row.at_user_ids || [])]
  editing.value = true
  editingId.value = row.id
  const s = row.interval_seconds || 60
  if (s % 86400 === 0) {
    intervalValue.value = s / 86400
    intervalUnit.value = 'day'
  } else if (s % 3600 === 0) {
    intervalValue.value = s / 3600
    intervalUnit.value = 'hour'
  } else if (s % 60 === 0) {
    intervalValue.value = s / 60
    intervalUnit.value = 'minute'
  } else {
    intervalValue.value = s
    intervalUnit.value = 'second'
  }
  dialogVisible.value = true
}

async function save() {
  const payload = { ...form }
  if (payload.schedule_type === 'interval') {
    payload.interval_seconds = Math.max(1, intervalValue.value * UNIT[intervalUnit.value])
  }
  saving.value = true
  try {
    if (editing.value) {
      await updateTask(editingId.value, payload)
      ElMessage.success('任务已更新')
    } else {
      await createTask(payload)
      ElMessage.success('任务已创建')
    }
    dialogVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function toggle(row) {
  await toggleTask(row.id)
  load()
}

async function pin(row) {
  await pinTask(row.id)
  load()
}

async function run(row) {
  const res = await runTaskNow(row.id)
  ElMessage[res.success ? 'success' : 'error'](res.message)
  setTimeout(load, 1200)
}

async function remove(row) {
  await ElMessageBox.confirm(`确认删除任务「${row.name}」？`, '提示', { type: 'warning' })
  await deleteTask(row.id)
  ElMessage.success('已删除')
  load()
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

async function clearLogs() {
  if (!logTask.value) return
  await clearTaskLogs(logTask.value.id)
  ElMessage.success('日志已清空')
  loadLogs()
}

onMounted(load)
</script>
